#include "fixed.h"

__attribute__((noinline,noclone)) void fixed_packed(struct fixed_context *c) {
    const int8_t *a=c->a, *x=c->x;
    int8_t *packed=c->packed;
    int32_t *y=c->y;
    struct caller_slot *slots=c->slots;
    caller_leaf entry=c->packed_entry;
    size_t count=c->count;
    for (unsigned k=0;k<256;++k) packed[k]=a[k];
    for (size_t step=0;step<count;++step) {
        for (unsigned k=0;k<32;++k) packed[256+k]=x[step*32+k];
        entry(packed,slots+step*8);
        for (unsigned r=0;r<8;++r) y[step*8+r]=slots[step*8+r].value;
    }
}

__attribute__((noinline,noclone)) void fixed_split(struct fixed_context *c) {
    const int8_t *a=c->a, *x=c->x;
    int32_t *y=c->y;
    struct caller_slot *slots=c->slots;
    split_leaf entry=c->split_entry;
    size_t count=c->count;
    for (size_t step=0;step<count;++step) {
        entry(a,x+step*32,slots+step*8);
        for (unsigned r=0;r<8;++r) y[step*8+r]=slots[step*8+r].value;
    }
}
