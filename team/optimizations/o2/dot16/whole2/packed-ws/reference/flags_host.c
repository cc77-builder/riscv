/* Independent host check of unchanged K288 scalar oracle and exact fixture bits. */
#include <errno.h>
#include <fenv.h>
#include <float.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "q288.h"
#pragma STDC FENV_ACCESS ON
static int8_t weights[82944],input[288];
static float scales[2592],xs[9],output[288];
static unsigned char gold[1152];
static void fail(const char *reason) {fprintf(stderr,"HOST_FLAGS_FAIL %s\n",reason);exit(1);}
static void read_span(const char *dir,const char *name,void *dst,size_t size) {
    char path[4096];int n=snprintf(path,sizeof(path),"%s/%s",dir,name);
    if(n<0 || (size_t)n>=sizeof(path))fail("input path length");
    FILE *f=fopen(path,"rb");if(!f)fail("input open");
    if(fread(dst,1,size,f)!=size || fgetc(f)!=EOF || ferror(f))fail("input exact size");
    if(fclose(f))fail("input close");
}
int main(int argc,char **argv) {
    if(argc!=3)fail("expected fixture directory and fresh output flags path");
    if(sizeof(float)!=4 || FLT_RADIX!=2 || FLT_MANT_DIG!=24)fail("binary32 host");
    read_span(argv[1],"weight.bin",weights,sizeof(weights));
    read_span(argv[1],"input.bin",input,sizeof(input));
    read_span(argv[1],"scales.bin",scales,sizeof(scales));
    read_span(argv[1],"input-scales.bin",xs,sizeof(xs));
    read_span(argv[1],"gold.bin",gold,sizeof(gold));
    if(fesetround(FE_TONEAREST) || fegetround()!=FE_TONEAREST || feclearexcept(FE_ALL_EXCEPT))fail("RNE/fenv setup");
    q288_oracle(output,input,xs,weights,scales);
    int raised=fetestexcept(FE_ALL_EXCEPT);
    if(memcmp(output,gold,sizeof(gold)))fail("complete original golden bytes");
    unsigned flags=((raised&FE_INEXACT)?1u:0u)|((raised&FE_UNDERFLOW)?2u:0u)|
        ((raised&FE_OVERFLOW)?4u:0u)|((raised&FE_DIVBYZERO)?8u:0u)|((raised&FE_INVALID)?16u:0u);
    unsigned char bytes[4]={(unsigned char)flags,0,0,0};
    FILE *f=fopen(argv[2],"wbx");if(!f)fail("fresh flags output");
    if(fwrite(bytes,1,4,f)!=4 || fclose(f))fail("flags output write");
    printf("K288_HOST_ORACLE_FLAGS_PASS bytes=1152 riscv_flags=%u host_exceptions=%d\n",flags,raised);
    return 0;
}
