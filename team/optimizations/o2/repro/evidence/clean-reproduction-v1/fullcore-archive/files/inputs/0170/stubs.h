/* Generated instruction dispatch. */
#ifndef VDOT_STUBS_H
#define VDOT_STUBS_H
extern void vdot_word_00100073(void);
extern void vdot_word_0094050b(void);
extern void vdot_word_0290050b(void);
extern void vdot_word_0294050b(void);
extern void vdot_word_02940557(void);
extern void vdot_word_0294150b(void);
extern void vdot_word_0294250b(void);
extern void vdot_word_0294450b(void);
extern void vdot_word_0694050b(void);
extern void vdot_word_0a94050b(void);
extern void vdot_word_1294050b(void);
extern void vdot_word_2294050b(void);
extern void vdot_word_4294050b(void);
extern void vdot_word_8294050b(void);
static void (*find_stub(unsigned word))(void) { switch (word) {
case 0x00100073U: return vdot_word_00100073;
case 0x0094050bU: return vdot_word_0094050b;
case 0x0290050bU: return vdot_word_0290050b;
case 0x0294050bU: return vdot_word_0294050b;
case 0x02940557U: return vdot_word_02940557;
case 0x0294150bU: return vdot_word_0294150b;
case 0x0294250bU: return vdot_word_0294250b;
case 0x0294450bU: return vdot_word_0294450b;
case 0x0694050bU: return vdot_word_0694050b;
case 0x0a94050bU: return vdot_word_0a94050b;
case 0x1294050bU: return vdot_word_1294050b;
case 0x2294050bU: return vdot_word_2294050b;
case 0x4294050bU: return vdot_word_4294050b;
case 0x8294050bU: return vdot_word_8294050b;
default: return 0; } }
#endif
