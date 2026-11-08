/* Host interposer: inject one vector bit100 at the frozen chain instruction.
 * Original interpreter is pinned by the supervisor, never rebuilt here. */
#include <dlfcn.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifndef REF_SO
#error REF_SO must identify the SHA-pinned original interpreter
#endif
#define STATE_BYTES 1400u
#define PC_OFFSET 656u
#define VECTOR_OFFSET 800u
#define TARGET_PC UINT64_C(0x80000d64)
#define TARGET_WORD UINT32_C(0x0388000b)
#define TARGET_VD 0u
static void (*real_exec)(uint64_t);
static void (*real_regcpy)(void *, bool);
static void (*real_memcpy)(uint64_t, void *, size_t, bool);
static void *handle;
static bool pending, injected;
static void fail(const char *what) { fprintf(stderr,"NEGATIVE_FIXTURE_SETUP_FAIL %s\n",what); fflush(stderr); abort(); }
static void *symbol(const char *name) { void *p=dlsym(handle,name); if(!p)fail(name);return p; }
__attribute__((constructor)) static void configure(void) {
  const char *env=getenv("SP1_CHAIN_BIT100");
  if(!env || strcmp(env,"1")) fail("SP1_CHAIN_BIT100 must be 1");
  handle=dlopen(REF_SO, RTLD_NOW|RTLD_LOCAL); if(!handle)fail(dlerror());
  const unsigned *size=(const unsigned *)symbol("DIFFTEST_REG_SIZE");
  if(*size!=STATE_BYTES)fail("state size must be 1400");
  real_exec=symbol("difftest_exec");real_regcpy=symbol("difftest_regcpy");real_memcpy=symbol("difftest_memcpy");
}
void difftest_exec(uint64_t count) {
  if(injected || count!=1) { real_exec(count); return; }
  unsigned char state[STATE_BYTES];uint64_t pc;uint32_t word=0;
  real_regcpy(state,false);memcpy(&pc,state+PC_OFFSET,sizeof(pc));
  if(pc==TARGET_PC)real_memcpy(pc,&word,sizeof(word),false);
  real_exec(count);
  if(pc==TARGET_PC && word==TARGET_WORD && ((word>>7)&31)==TARGET_VD)pending=true;
}
void difftest_regcpy(void *state,bool to_reference) {
  real_regcpy(state,to_reference);
  if(to_reference) { pending=false;return; }
  if(pending && !injected) {
    ((unsigned char *)state)[VECTOR_OFFSET+16*TARGET_VD+12]^=0x10;
    pending=false;injected=true;
    fprintf(stderr,"DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=0 pc=0x80000d64 instruction=0x0388000b\n");fflush(stderr);
  }
}
