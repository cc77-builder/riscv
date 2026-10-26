#include <stdint.h>
extern uintptr_t __stack_chk_guard;
/* Compiled separately with real stack protection. The saved guard must fail. */
__attribute__((noinline)) void team_guard_control(void) {
    __stack_chk_guard ^= UINT64_C(1);
    __asm__ volatile ("" ::: "memory");
}
