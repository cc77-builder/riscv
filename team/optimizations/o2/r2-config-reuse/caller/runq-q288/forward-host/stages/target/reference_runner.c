/* Team-owned bounded caller of the unmodified fixed NEMU shared-library API.
 * Compile against its actual configuration/headers; never emulate or skip ISA.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <time.h>
#include <ctype.h>
#include <isa-def.h>
#include <utils.h>

#if defined(CONFIG_LIGHTQS) || defined(CONFIG_SHARE_CTRL) || !defined(CONFIG_SHARE)
#error This external adapter supports only the actual non-LIGHTQS SHARE ABI.
#endif

static void require(int ok,const char *why) {
    if(!ok) {fprintf(stderr,"REFERENCE_ADAPTER_REJECT %s\n",why);exit(70);}
}
static void *symbol(void *library,const char *name) {
    dlerror();void *result=dlsym(library,name);const char *error=dlerror();
    if(error)fprintf(stderr,"missing symbol %s: %s\n",name,error);
    require(!error && result,"required fixed reference API");return result;
}
static double wall_seconds(void) {
    struct timespec value;require(clock_gettime(CLOCK_MONOTONIC,&value)==0,"monotonic wall clock");
    return (double)value.tv_sec+(double)value.tv_nsec*1e-9;
}
static FILE *create(const char *directory,const char *name) {
    char path[4096];int count=snprintf(path,sizeof(path),"%s/%s",directory,name);
    require(count>0 && (size_t)count<sizeof(path),"bounded fresh output path");
    FILE *file=fopen(path,"wbx");require(file!=NULL,"exclusive output creation");return file;
}
static void save_bytes(const char *directory,const char *name,const void *data,size_t size) {
    FILE *file=create(directory,name);require(fwrite(data,1,size,file)==size && fclose(file)==0,"complete raw state output");
}
static uint64_t number(const char *text) {
    char *end;require(*text && *text!='-',"nonnegative integer argument");
    uint64_t result=strtoull(text,&end,0);require(!*end,"whole integer argument");return result;
}

int main(int argc,char **argv) {
    require(argc==9,"so image output flash-or-builtin max-calls wall-seconds dump-plan-or-none max-idle");
    setvbuf(stdout,NULL,_IOLBF,0);
    uint64_t max_calls=number(argv[5]),wall_limit=number(argv[6]),max_idle=number(argv[8]);
    require(max_calls>0 && max_calls<=UINT64_C(10000000000) && wall_limit>0 && wall_limit<=14400 && max_idle>0 && max_idle<=1024,"bounded execution limits");
    void *library=dlopen(argv[1],RTLD_LAZY|RTLD_DEEPBIND);require(library!=NULL,"load fixed reference shared object");
    unsigned register_size=*(const unsigned*)symbol(library,"DIFFTEST_REG_SIZE");
    const size_t expected_size=offsetof(riscv64_CPU_state,difftest_state_end)-offsetof(riscv64_CPU_state,gpr);
    require(offsetof(riscv64_CPU_state,gpr)==0 && register_size==expected_size && register_size<=sizeof(riscv64_CPU_state),"actual header/runtime register ABI");
    void (*set_ram)(size_t)=symbol(library,"difftest_set_ramsize");
    void (*initialize)(void)=symbol(library,"difftest_init");
    void (*load_flash)(void*,size_t)=symbol(library,"difftest_load_flash");
    void (*copy_memory)(uint64_t,void*,size_t,bool)=symbol(library,"difftest_memcpy");
    void (*copy_registers)(void*,bool)=symbol(library,"difftest_regcpy");
    void (*copy_csrs)(void*,bool)=symbol(library,"difftest_csrcpy");
    void (*execute)(uint64_t)=symbol(library,"difftest_exec");
    uint64_t (*retired)(void)=symbol(library,"get_abs_instr_count");
    bool (*critical)(void)=dlsym(library,"difftest_raise_critical_error");
    const NEMUState *state=symbol(library,"nemu_state");
    riscv64_CPU_state current={0};uint64_t csrs[4096];
    set_ram(128u*1024u*1024u);initialize();
    copy_registers(&current,false);copy_csrs(csrs,false);
    save_bytes(argv[3],"initial-registers.bin",&current,register_size);
    save_bytes(argv[3],"initial-csrs.bin",csrs,sizeof(csrs));
    FILE *layout=create(argv[3],"abi.json");
    fprintf(layout,"{\"register_bytes\":%u,\"header_span\":%zu,\"whole_struct_bytes\":%zu,\"pc_offset\":%zu,\"mode_offset\":%zu,\"mcause_offset\":%zu,\"mepc_offset\":%zu,\"mtval_offset\":%zu,\"initial_pc\":%llu,\"initial_mode\":%llu,\"state_object_bytes\":%zu}\n",register_size,expected_size,sizeof(current),offsetof(riscv64_CPU_state,pc),offsetof(riscv64_CPU_state,mode),offsetof(riscv64_CPU_state,mcause),offsetof(riscv64_CPU_state,mepc),offsetof(riscv64_CPU_state,mtval),(unsigned long long)current.pc,(unsigned long long)current.mode,sizeof(NEMUState));
    require(fclose(layout)==0,"ABI receipt close");
    load_flash(!strcmp(argv[4],"builtin")?NULL:argv[4],0);
    FILE *input=fopen(argv[2],"rb");require(input!=NULL && fseek(input,0,SEEK_END)==0,"raw image readable");
    long length=ftell(input);require(length>0 && length<=128*1024*1024 && fseek(input,0,SEEK_SET)==0,"bounded raw image");
    unsigned char *image=malloc((size_t)length);require(image!=NULL,"host image buffer");
    require(fread(image,1,(size_t)length,input)==(size_t)length && fclose(input)==0,"complete raw image read");
    copy_memory(UINT64_C(0x80000000),image,(size_t)length,true);free(image);
    /* All CPU/CSR state remains that initialized by NEMU and the selected flash.
     * There is no TO_REF register copy, no MMIO skip, no exception suppression. */
    FILE *trace=create(argv[3],"steps.jsonl");
    uint64_t calls=0,last_retired=retired(),idle=0;double begin=wall_seconds();const char *reason="call_limit";
    while(calls<max_calls) {
        uint64_t before_pc=current.pc;
        execute(1);++calls;copy_registers(&current,false);
        uint64_t count=retired();idle=count==last_retired?idle+1:0;last_retired=count;
        bool fatal=critical && critical();
        bool outside=!((current.pc>=UINT64_C(0x80000000) && current.pc<UINT64_C(0x88000000)) ||
                       (current.pc>=CONFIG_MMIO_RESET_VECTOR && current.pc<CONFIG_MMIO_RESET_VECTOR+UINT64_C(0x10000)));
        bool terminal=state->state==NEMU_END || state->state==NEMU_ABORT || fatal || outside || idle>=max_idle;
        if(calls<=256 || calls%1000000==0 || terminal) {
            fprintf(trace,"{\"call\":%llu,\"retired\":%llu,\"from_pc\":%llu,\"pc\":%llu,\"mode\":%llu,\"mepc\":%llu,\"mcause\":%llu,\"mtval\":%llu,\"mtvec\":%llu,\"state\":%d,\"critical\":%s}\n",(unsigned long long)calls,(unsigned long long)count,(unsigned long long)before_pc,(unsigned long long)current.pc,(unsigned long long)current.mode,(unsigned long long)current.mepc,(unsigned long long)current.mcause,(unsigned long long)current.mtval,(unsigned long long)current.mtvec,state->state,fatal?"true":"false");
            require(fflush(trace)==0,"durable step trace flush");
        }
        if(state->state==NEMU_END) {reason=state->halt_ret==0?"good_trap":"bad_trap";break;}
        if(state->state==NEMU_ABORT) {reason="reference_abort";break;}
        if(fatal) {reason="critical_error";break;}
        if(outside) {reason="pc_outside_ram_and_boot_flash";break;}
        if(idle>=max_idle) {reason="no_retirement_progress";break;}
        if((calls&4095)==0 && wall_seconds()-begin>(double)wall_limit) {reason="wall_limit";break;}
    }
    require(fclose(trace)==0,"trace close");
    copy_csrs(csrs,false);save_bytes(argv[3],"final-registers.bin",&current,register_size);
    save_bytes(argv[3],"final-csrs.bin",csrs,sizeof(csrs));
    unsigned dumps=0;
    if(strcmp(argv[7],"none")) {
        FILE *plan=fopen(argv[7],"r");require(plan!=NULL,"dump plan readable");
        unsigned char *buffer=malloc(1u<<20);require(buffer!=NULL,"bounded dump chunk");
        char name[128];unsigned long long address,bytes;
        int fields;
        while((fields=fscanf(plan,"%127s %llx %llu",name,&address,&bytes))!=EOF) {
            require(fields==3,"complete dump plan record");
            require(++dumps<=64 && bytes>0 && address>=UINT64_C(0x80000000) && address<UINT64_C(0x88000000) && bytes<=UINT64_C(0x88000000)-address,"bounded target memory dump");
            for(char *p=name;*p;++p)require(isalnum((unsigned char)*p)||*p=='_'||*p=='-'||*p=='.',"plain dump basename");
            require(strcmp(name,".") && strcmp(name,".."),"safe dump basename");
            FILE *output=create(argv[3],name);
            for(uint64_t offset=0;offset<bytes;) {
                size_t chunk=bytes-offset>(1u<<20)?(1u<<20):(size_t)(bytes-offset);
                copy_memory(address+offset,buffer,chunk,false);
                require(fwrite(buffer,1,chunk,output)==chunk,"complete target dump write");offset+=chunk;
            }
            require(fclose(output)==0,"target dump close");
        }
        require(feof(plan) && fclose(plan)==0,"whole dump plan parsed");free(buffer);
    }
    double elapsed=wall_seconds()-begin;FILE *result=create(argv[3],"reference-result.json");
    fprintf(result,"{\"reason\":\"%s\",\"api_calls\":%llu,\"retired\":%llu,\"elapsed_seconds\":%.6f,\"state\":%d,\"halt_pc\":%llu,\"halt_ret\":%u,\"pc\":%llu,\"mcause\":%llu,\"mepc\":%llu,\"mtval\":%llu,\"mnstatus\":%llu,\"mnepc\":%llu,\"mncause\":%llu,\"memory_dumps\":%u,\"xiangshan_cycles_measured\":false}\n",reason,(unsigned long long)calls,(unsigned long long)last_retired,elapsed,state->state,(unsigned long long)state->halt_pc,state->halt_ret,(unsigned long long)current.pc,(unsigned long long)csrs[0x342],(unsigned long long)csrs[0x341],(unsigned long long)csrs[0x343],(unsigned long long)csrs[0x744],(unsigned long long)csrs[0x741],(unsigned long long)csrs[0x742],dumps);
    require(fclose(result)==0,"reference result close");
    printf("REFERENCE_ADAPTER_DONE reason=%s calls=%llu retired=%llu seconds=%.6f\n",reason,(unsigned long long)calls,(unsigned long long)last_retired,elapsed);
    return !strcmp(reason,"good_trap")?0:2;
}
