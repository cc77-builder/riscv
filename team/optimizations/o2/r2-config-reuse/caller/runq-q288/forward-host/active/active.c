/* Team-owned active consumer. Reference and frozen observer stay unchanged.
 * Reuse their deterministic fixture helpers; old observation runs only on the
 * independent reference forward. Upstream license: ../upstream/LICENSE.
 */
#define main frozen_passive_observer_main
#include "../observe.c"
#undef main

typedef int (*projection_fn)(unsigned,unsigned,unsigned,
    const int8_t*,const int8_t*,const float*,const int8_t*,const float*,float*);
static projection_fn projection;
static unsigned method_number,control_number,projections,team_quantizes,team_matmuls;
static unsigned quantized_groups,quantized_elements,injected;
static unsigned char shared_input[D+9*sizeof(float)];
static FILE *events;

static void event(const char *name,unsigned method,unsigned pos,unsigned a,unsigned b,unsigned c) {
    require(fprintf(events,"%s %u %u %u %u %u\n",name,method,pos,a,b,c)>0,"event write");
    require(fflush(events)==0,"event flush");
}

static void team_quantize(QuantizedTensor *output,float *input,int n) {
    unsigned call=team_quantizes++;
    require(call<25 && n==((call<24 && call%4==3)?H:D),"candidate quantize sequence");
    for(int start=0;start<n;start+=32) {
        float maximum=0.0f;
        for(int i=0;i<32;++i) {
            require(isfinite(input[start+i]),"finite candidate pre-quantize values");
            float magnitude=fabsf(input[start+i]);if(magnitude>maximum)maximum=magnitude;
        }
        require(maximum>0.0f,"candidate nonzero quantizer group");
        volatile float scale=maximum/127.0f;
        require(isfinite(scale) && scale>0.0f,"candidate positive representable scale");
        for(int i=0;i<32;++i) {
            volatile float scaled=input[start+i]/scale;
            double rounded=round((double)scaled);
            require(isfinite(scaled) && rounded>=-128.0 && rounded<=127.0,"candidate defined int8 domain");
        }
        ++quantized_groups;
    }
    quantized_elements+=(unsigned)n;
    if(call<24 && call%4<2) {
        char name[100];
        snprintf(name,sizeof(name),"m%u-p%u-l%u-%s-fp32.bin",method_number,position_number,call/4,call%4?"o":"qkv");
        write_file(name,input,n*sizeof(float));
    }
    quantize(output,input,n);
    for(int i=0;i<n/32;++i)require(isfinite(output->s[i]) && output->s[i]>0.0f,"candidate actual quantized scale");
}

static void team_matmul(float *output,QuantizedTensor *input,QuantizedTensor *weight,int n,int d) {
    ++team_matmuls;matmul(output,input,weight,n,d);
}

static void team_project(float *output,QuantizedTensor *input,QuantizedTensor *weight,unsigned id) {
    require(id==projections && id<24,"explicit Q/K/V/O order");
    struct prepared_q *p=&prepared[id];
    require(p->weight==weight,"correct layer and matrix routing");
    unsigned char saved[D+9*sizeof(float)];
    memcpy(saved,input->q,D);memcpy(saved+D,input->s,9*sizeof(float));
    if(id%4==0)memcpy(shared_input,saved,sizeof(saved));
    if(id%4==1 || id%4==2)require(memcmp(shared_input,saved,sizeof(saved))==0,"QKV quantization really shared");
    uint32_t poison=UINT32_C(0x7fc00042);
    for(unsigned i=0;i<D;++i)memcpy(output+i,&poison,sizeof(poison));
    require(projection(method_number,position_number,id,weight->q,p->packed,weight->s,
                       input->q,input->s,output)==0,"projection callback succeeded");
    for(unsigned i=0;i<D;++i)require(isfinite(output[i]),"callback overwrote every output");
    require(memcmp(saved,input->q,D)==0 && memcmp(saved+D,input->s,9*sizeof(float))==0,"candidate quantized input readonly");
    char name[100];
    snprintf(name,sizeof(name),"m%u-p%u-q%02u-input.bin",method_number,position_number,id);write_file(name,saved,sizeof(saved));
    snprintf(name,sizeof(name),"m%u-p%u-q%02u-output.bin",method_number,position_number,id);write_file(name,output,D*sizeof(float));
    /* Corruption is AFTER accepted ELF-model output and BEFORE RoPE/KV. */
    if(method_number==0 && position_number==0 &&
       ((control_number==1 && id==1) || (control_number==2 && id==2))) {
        output[0]+=8.0f;require(isfinite(output[0]),"finite injected candidate output");++injected;
        event("INJECT",method_number,position_number,id,0,0);
    }
    ++projections;
}

/* BEGIN DERIVED FORWARD: only the name and explicit team call sites differ. */
static float* team_forward(Transformer* transformer, int token, int pos) {

    // a few convenience variables
    Config* p = &transformer->config;
    TransformerWeights* w = &transformer->weights;
    RunState* s = &transformer->state;
    float *x = s->x;
    int dim = p->dim;
    int kv_dim = (p->dim * p->n_kv_heads) / p->n_heads;
    int kv_mul = p->n_heads / p->n_kv_heads; // integer multiplier of the kv sharing in multiquery
    int hidden_dim =  p->hidden_dim;
    int head_size = dim / p->n_heads;

    // copy the token embedding into x
    memcpy(x, w->token_embedding_table + token*dim, dim * sizeof(float));

    // forward all the layers
    for(int l = 0; l < p->n_layers; l++) {

        // attention rmsnorm
        rmsnorm(s->xb, x, w->rms_att_weight + l*dim, dim);

        // qkv matmuls for this position
        team_quantize(&s->xq, s->xb, dim);
        team_project(s->q, &s->xq, w->wq + l, (unsigned)(4*l+0));
        team_project(s->k, &s->xq, w->wk + l, (unsigned)(4*l+1));
        team_project(s->v, &s->xq, w->wv + l, (unsigned)(4*l+2));

        // RoPE relative positional encoding: complex-valued rotate q and k in each head
        for (int i = 0; i < dim; i+=2) {
            int head_dim = i % head_size;
            float freq = 1.0f / powf(10000.0f, head_dim / (float)head_size);
            float val = pos * freq;
            float fcr = cosf(val);
            float fci = sinf(val);
            int rotn = i < kv_dim ? 2 : 1; // how many vectors? 2 = q & k, 1 = q only
            for (int v = 0; v < rotn; v++) {
                float* vec = v == 0 ? s->q : s->k; // the vector to rotate (query or key)
                float v0 = vec[i];
                float v1 = vec[i+1];
                vec[i]   = v0 * fcr - v1 * fci;
                vec[i+1] = v0 * fci + v1 * fcr;
            }
        }

        // save key,value at this time step (pos) to our kv cache
        int loff = l * p->seq_len * kv_dim; // kv cache layer offset for convenience
        float* key_cache_row = s->key_cache + loff + pos * kv_dim;
        float* value_cache_row = s->value_cache + loff + pos * kv_dim;
        memcpy(key_cache_row, s->k, kv_dim * sizeof(*key_cache_row));
        memcpy(value_cache_row, s->v, kv_dim * sizeof(*value_cache_row));

        // multihead attention. iterate over all heads
        int h;
        #pragma omp parallel for private(h)
        for (h = 0; h < p->n_heads; h++) {
            // get the query vector for this head
            float* q = s->q + h * head_size;
            // attention scores for this head
            float* att = s->att + h * p->seq_len;
            // iterate over all timesteps, including the current one
            for (int t = 0; t <= pos; t++) {
                // get the key vector for this head and at this timestep
                float* k = s->key_cache + loff + t * kv_dim + (h / kv_mul) * head_size;
                // calculate the attention score as the dot product of q and k
                float score = 0.0f;
                for (int i = 0; i < head_size; i++) {
                    score += q[i] * k[i];
                }
                score /= sqrtf(head_size);
                // save the score to the attention buffer
                att[t] = score;
            }

            // softmax the scores to get attention weights, from 0..pos inclusively
            softmax(att, pos + 1);

            // weighted sum of the values, store back into xb
            float* xb = s->xb + h * head_size;
            memset(xb, 0, head_size * sizeof(float));
            for (int t = 0; t <= pos; t++) {
                // get the value vector for this head and at this timestep
                float* v = s->value_cache + loff + t * kv_dim + (h / kv_mul) * head_size;
                // get the attention weight for this timestep
                float a = att[t];
                // accumulate the weighted value into xb
                for (int i = 0; i < head_size; i++) {
                    xb[i] += a * v[i];
                }
            }
        }

        // final matmul to get the output of the attention
        team_quantize(&s->xq, s->xb, dim);
        team_project(s->xb2, &s->xq, w->wo + l, (unsigned)(4*l+3));

        // residual connection back into x
        for (int i = 0; i < dim; i++) {
            x[i] += s->xb2[i];
        }

        // ffn rmsnorm
        rmsnorm(s->xb, x, w->rms_ffn_weight + l*dim, dim);

        // Now for FFN in PyTorch we have: self.w2(F.silu(self.w1(x)) * self.w3(x))
        // first calculate self.w1(x) and self.w3(x)
        team_quantize(&s->xq, s->xb, dim);
        team_matmul(s->hb, &s->xq, w->w1 + l, dim, hidden_dim);
        team_matmul(s->hb2, &s->xq, w->w3 + l, dim, hidden_dim);

        // SwiGLU non-linearity
        for (int i = 0; i < hidden_dim; i++) {
            float val = s->hb[i];
            // silu(x)=x*σ(x), where σ(x) is the logistic sigmoid
            val *= (1.0f / (1.0f + expf(-val)));
            // elementwise multiply with w3(x)
            val *= s->hb2[i];
            s->hb[i] = val;
        }

        // final matmul to get the output of the ffn
        team_quantize(&s->hq, s->hb, hidden_dim);
        team_matmul(s->xb, &s->hq, w->w2 + l, hidden_dim, dim);

        // residual connection
        for (int i = 0; i < dim; i++) {
            x[i] += s->xb[i];
        }
    }

    // final rmsnorm
    rmsnorm(x, x, w->rms_final_weight, dim);

    // classifier into logits
    team_quantize(&s->xq, x, dim);
    team_matmul(s->logits, &s->xq, w->wcls, dim, p->vocab_size);
    return s->logits;
}

/* END DERIVED FORWARD */

struct span { unsigned char *start; size_t size; };
static unsigned spans(RunState *s,struct span *out) {
    struct span values[]={
        {(unsigned char*)s->x,D*4},{(unsigned char*)s->xb,D*4},{(unsigned char*)s->xb2,D*4},
        {(unsigned char*)s->hb,H*4},{(unsigned char*)s->hb2,H*4},
        {(unsigned char*)s->xq.q,D},{(unsigned char*)s->xq.s,D*4},
        {(unsigned char*)s->hq.q,H},{(unsigned char*)s->hq.s,H*4},
        {(unsigned char*)s->q,D*4},{(unsigned char*)s->k,D*4},{(unsigned char*)s->v,D*4},
        {(unsigned char*)s->att,6*S*4},{(unsigned char*)s->logits,V*4},
        {(unsigned char*)s->key_cache,L*S*D*4},{(unsigned char*)s->value_cache,L*S*D*4}};
    memcpy(out,values,sizeof(values));return sizeof(values)/sizeof(values[0]);
}

static void distinct_states(Transformer *all,unsigned count) {
    struct span values[48];unsigned n=0;
    for(unsigned i=0;i<count;++i)n+=spans(&all[i].state,values+n);
    for(unsigned i=0;i<n;++i) {
        require(values[i].start!=NULL,"all state buffers allocated");
        for(unsigned j=i+1;j<n;++j) {
            uintptr_t a=(uintptr_t)values[i].start,b=(uintptr_t)values[j].start;
            require(a+values[i].size<=b || b+values[j].size<=a,"all writable state buffers disjoint");
        }
    }
}

int active_run(const char *output_directory,unsigned control,projection_fn callback) {
    destination=output_directory;control_number=control;projection=callback;
    require(control<=3 && callback!=NULL,"bounded control and explicit callback");
    require(sizeof(float)==4 && sizeof(void*)==8 && fesetround(FE_TONEAREST)==0,"binary32 interface and RNE");
    char path[4096];int length=snprintf(path,sizeof(path),"%s/events.txt",destination);
    require(length>0 && (size_t)length<sizeof(path),"bounded event path");
    events=fopen(path,"wb");require(events!=NULL,"open events");
    Transformer all[3]={0};all[0].config=(Config){D,H,L,6,6,V,S};
    random_state=UINT32_C(0x53485041);size_t weight_bytes;
    unsigned char *weights=make_weights(all,&weight_bytes),*weight_copy=malloc(weight_bytes);
    require(weight_copy!=NULL,"weight snapshot");memcpy(weight_copy,weights,weight_bytes);
    size_t embedding_bytes=(size_t)V*D*sizeof(float),cache_bytes=(size_t)L*S*D*sizeof(float);
    float *embedding_copy=malloc(embedding_bytes),*before_key=malloc(cache_bytes),*before_value=malloc(cache_bytes);
    require(embedding_copy && before_key && before_value,"immutable/state snapshots");
    memcpy(embedding_copy,all[0].weights.token_embedding_table,embedding_bytes);
    prepare_weights(all);unsigned char *packed_copy=malloc(24*D*D);require(packed_copy!=NULL,"packed snapshot");
    for(unsigned i=0;i<24;++i)memcpy(packed_copy+i*D*D,prepared[i].packed,D*D);
    unsigned methods=control?1:2;
    for(unsigned i=0;i<=methods;++i) {
        all[i].config=all[0].config;all[i].weights=all[0].weights;
        malloc_run_state(&all[i].state,&all[i].config);
    }
    distinct_states(all,methods+1);
    const int tokens[]={1,7,19};unsigned mismatch_logit[3]={0},mismatch_key[3]={0},mismatch_value[3]={0};
    injected=0;pass_number=1;
    for(position_number=0;position_number<3;++position_number) {
        observed=&all[0];
        memcpy(before_key,observed->state.key_cache,cache_bytes);memcpy(before_value,observed->state.value_cache,cache_bytes);
        matmuls=quantizes=rmsnorms=softmaxes=q_calls=groups=input_elements=0;active_q=24;active=1;
        float *reference=forward(observed,tokens[position_number],(int)position_number);active=0;
        require(matmuls==43 && quantizes==25 && rmsnorms==13 && softmaxes==36 &&
                q_calls==24 && groups==315 && input_elements==10080,"reference complete inventory");
        finite_cache_and_unchanged_rows(observed,before_key,before_value,position_number);
        for(unsigned i=0;i<V;++i)require(isfinite(reference[i]),"reference logits finite");
        event("REFERENCE",2,position_number,matmuls,quantizes,q_calls);
        char name[100];
        snprintf(name,sizeof(name),"reference-p%u-logits.bin",position_number);write_file(name,reference,V*sizeof(float));
        snprintf(name,sizeof(name),"reference-p%u-key.bin",position_number);write_file(name,all[0].state.key_cache,cache_bytes);
        snprintf(name,sizeof(name),"reference-p%u-value.bin",position_number);write_file(name,all[0].state.value_cache,cache_bytes);
        for(method_number=0;method_number<methods;++method_number) {
            Transformer *current=&all[method_number+1];
            memcpy(before_key,current->state.key_cache,cache_bytes);memcpy(before_value,current->state.value_cache,cache_bytes);
            projections=team_quantizes=team_matmuls=quantized_groups=quantized_elements=0;
            float *logits=team_forward(current,tokens[position_number],(int)position_number);
            require(projections==24 && team_quantizes==25 && team_matmuls==19 &&
                    quantized_groups==315 && quantized_elements==10080,"candidate complete inventory");
            finite_cache_and_unchanged_rows(current,before_key,before_value,position_number);
            for(unsigned i=0;i<V;++i)require(isfinite(logits[i]),"candidate logits finite");
            unsigned dl=memcmp(reference,logits,V*sizeof(float))!=0;
            unsigned dk=memcmp(all[0].state.key_cache,current->state.key_cache,cache_bytes)!=0;
            unsigned dv=memcmp(all[0].state.value_cache,current->state.value_cache,cache_bytes)!=0;
            mismatch_logit[position_number]|=dl;mismatch_key[position_number]|=dk;mismatch_value[position_number]|=dv;
            event("COMPARE",method_number,position_number,dl,dk,dv);
            if(!control)require(dl==0 && dk==0 && dv==0,"complete active logits/KV equality");
            snprintf(name,sizeof(name),"m%u-p%u-logits.bin",method_number,position_number);write_file(name,logits,V*sizeof(float));
            snprintf(name,sizeof(name),"m%u-p%u-key.bin",method_number,position_number);write_file(name,current->state.key_cache,cache_bytes);
            snprintf(name,sizeof(name),"m%u-p%u-value.bin",method_number,position_number);write_file(name,current->state.value_cache,cache_bytes);
            require(memcmp(weights,weight_copy,weight_bytes)==0 &&
                    memcmp(all[0].weights.token_embedding_table,embedding_copy,embedding_bytes)==0,"all weights/embedding readonly");
            for(unsigned i=0;i<24;++i)require(memcmp(packed_copy+i*D*D,prepared[i].packed,D*D)==0,"all persistent packed weights readonly");
            event("INVENTORY",method_number,position_number,projections,team_quantizes,team_matmuls);
        }
    }
    if(control==1)require(injected==1 && mismatch_key[0] && mismatch_key[1] &&
                          mismatch_logit[1],"K corruption consumed across positions");
    if(control==2)require(injected==1 && mismatch_value[0] && mismatch_logit[0] &&
                          mismatch_logit[1],"V corruption consumed immediately and across positions");
    if(control==3)require(0,"omitted callback output was wrongly accepted");
    event("COMPLETE",control,methods,3,24,1990656);
    require(fclose(events)==0,"close event stream");
    for(unsigned i=0;i<=methods;++i)free_run_state(&all[i].state);
    free(weight_copy);free(embedding_copy);free(before_key);free(before_value);free(packed_copy);
    for(unsigned i=0;i<24;++i)free(prepared[i].packed);
    free(all[0].weights.token_embedding_table);free(all[0].weights.q_tokens);
    free(all[0].weights.wq);free(all[0].weights.wk);free(all[0].weights.wv);free(all[0].weights.wo);
    free(all[0].weights.w1);free(all[0].weights.w2);free(all[0].weights.w3);free(weights);
    return 0;
}


