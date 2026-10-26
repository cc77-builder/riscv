#ifndef XS_RUNQ_Q288_TAIL_H
#define XS_RUNQ_Q288_TAIL_H
#include "../phased.h"

/* Two internal e8 TA policy bits; the return state is still TU.
 * Availability of this symbol does not imply performance selection.
 * Use target/RESULT.md to decide between this entry, phased and RVV. */
void q288_tail_vdot(struct q288_context *);
#endif
