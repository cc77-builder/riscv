#ifndef VDOT_LAYOUT_H
#define VDOT_LAYOUT_H
/* Shared RV64 assembly/C offsets, verified by C static assertions. */
#define REC_EXPECTED_PC 0
#define REC_RESUME_PC 8
#define REC_EXPECTED_CAUSE 16
#define REC_ARMED 24
#define REC_TRAP_COUNT 32
#define REC_CAUSE 40
#define REC_EPC 48
#define REC_TVAL 56
#define REC_RAW_STATUS 64
#define REC_ERRORS 72
#define REC_IN_HANDLER 80
#define REC_PHASE 88
#define REC_ABORT_PC 96
#define REC_PRE_CSR 104
#define REC_POST_CSR 152
#define REC_PRE_STATUS 200
#define REC_PRE_REGS 208
#define REC_PRE_VALID 720
#define CFG_VTYPE 0
#define CFG_VL 8
#define CFG_VSTART 16
#define CFG_VXRM 24
#define CFG_VXSAT 32
#define CFG_VS_OFF 40
#define CFG_PC_BIAS 48
#define CFG_VS 56
#define ERR_UNARMED 1
#define ERR_PC 2
#define ERR_CAUSE 4
#define ERR_NESTED 8
#endif
