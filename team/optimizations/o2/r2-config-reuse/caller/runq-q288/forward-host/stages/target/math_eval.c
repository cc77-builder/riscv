#include "math_eval.h"
extern float powf(float, float), sinf(float), cosf(float), expf(float), sqrtf(float), roundf(float), fabsf(float);
extern double round(double), fabs(double);
extern void sincosf(float, float *, float *);

void math_evaluate(const struct math_input *in, uint64_t out[2]) {
    union { uint32_t u; float f; } a={.u=(uint32_t)in->a}, b={.u=(uint32_t)in->b}, r={.u=0}, s={.u=0};
    union { uint64_t u; double d; } ad={.u=in->a}, rd={.u=0};
    out[0]=out[1]=0;
    switch(in->kind) {
    case M_POWF:r.f=powf(a.f,b.f);break;
    case M_SINF:r.f=sinf(a.f);break;
    case M_COSF:r.f=cosf(a.f);break;
    case M_SINCOSF:sincosf(a.f,&r.f,&s.f);out[1]=s.u;break;
    case M_EXPF:r.f=expf(a.f);break;
    case M_SQRTF:r.f=sqrtf(a.f);break;
    case M_ROUNDF:r.f=roundf(a.f);break;
    case M_ROUND:rd.d=round(ad.d);out[0]=rd.u;return;
    case M_FABSF:r.f=fabsf(a.f);break;
    case M_FABS:rd.d=fabs(ad.d);out[0]=rd.u;return;
    default:out[0]=UINT64_MAX;return;
    }
    out[0]=r.u;
}
