/* Test-only DiffTest negative fixture. Never use as a normal reference.
 * For a selected vector instruction, corrupt only bit 100 in the architecture
 * state COPY returned to DiffTest. The actual pinned NEMU state is unmodified.
 * All instruction execution, memory access and reference APIs use the original
 * library. No network, credentials, host-process inspection or skipped checks.
 * Runtime selection: XS_NEGATIVE_VECTOR_TARGET=vadd or vdot.
 */
#include <dlfcn.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifndef REF_SO
#error Specify the verified original reference shared-library path
#endif
#define STATE_BYTES 1400u
#define PC_OFFSET 656u
#define VECTOR_OFFSET 800u
static void (*original_exec)(uint64_t);
static void (*original_regcpy)(void *, bool);
static void (*original_memcpy)(uint64_t, void *, size_t, bool);
static bool pending, injected;
static unsigned destination;
static uint32_t pending_word;
static uint64_t pending_pc;
static uint32_t selected_match;
static bool enabled;
static void *reference_handle;
static void *symbol(const char *name) {
  void *p=dlsym(reference_handle,name);
  if (!p) { fprintf(stderr,"NEGATIVE_FIXTURE_SETUP_FAIL symbol=%s\n",name); abort(); }
  return p;
}
__attribute__((constructor)) static void configure_fixture(void) {
  const char *target=getenv("XS_NEGATIVE_VECTOR_TARGET");
  if (target && strcmp(target,"vadd")==0) { selected_match=0x02000057u; enabled=true; }
  else if (target && strcmp(target,"vdot")==0) { selected_match=0x0200000bu; enabled=true; }
  else { fprintf(stderr,"NEGATIVE_FIXTURE_SETUP_FAIL explicit target required\n"); abort(); }
  reference_handle=dlopen(REF_SO,RTLD_NOW|RTLD_LOCAL);
  if (!reference_handle) { fprintf(stderr,"NEGATIVE_FIXTURE_SETUP_FAIL original reference load\n"); abort(); }
  const unsigned *size=(const unsigned *)symbol("DIFFTEST_REG_SIZE");
  if (*size!=STATE_BYTES) { fprintf(stderr,"NEGATIVE_FIXTURE_SETUP_FAIL ABI size=%u\n",*size); abort(); }
  original_exec=(void (*)(uint64_t))symbol("difftest_exec");
  original_regcpy=(void (*)(void *,bool))symbol("difftest_regcpy");
  original_memcpy=(void (*)(uint64_t,void *,size_t,bool))symbol("difftest_memcpy");
}
void difftest_exec(uint64_t count) {
  if (!enabled || injected || count!=1) { original_exec(count); return; }
  unsigned char state[STATE_BYTES];
  uint64_t pc; uint32_t instruction=0;
  original_regcpy(state,false);
  memcpy(&pc,state+PC_OFFSET,sizeof(pc));
  if (pc>=UINT64_C(0x80000000) && pc<UINT64_C(0x88000000))
    original_memcpy(pc,&instruction,sizeof(instruction),false);
  original_exec(count);
  if ((instruction&0xfe00707fu)==selected_match) {
    pending=true; destination=(instruction>>7)&31u;
    pending_pc=pc; pending_word=instruction;
  }
}
void difftest_regcpy(void *state,bool to_reference) {
  original_regcpy(state,to_reference);
  if (to_reference) { pending=false; return; }
  if (pending && !injected) {
    unsigned char *bytes=(unsigned char *)state;
    bytes[VECTOR_OFFSET+16u*destination+12u]^=0x10u;
    injected=true; pending=false;
    fprintf(stderr,"DIFFTEST_HIGHBIT_NEGATIVE_INJECTED bit=100 vd=%u pc=0x%llx instruction=0x%08x\n",
            destination,(unsigned long long)pending_pc,pending_word);
    fflush(stderr);
  }
}
