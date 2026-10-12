NAME = rvv-baseline
SRCS = main.c ../vdot-exceptions/judge.c ../vdot-exceptions/diagnostics.c ../vdot-exceptions/harness.S baseline.S
VDOT_DATA ?= $(abspath ../../out/t09-data)
INC_DIR += $(VDOT_DATA) $(abspath ../vdot-exceptions)
CFLAGS += -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns -ffreestanding
ASFLAGS += -I$(abspath ../vdot-exceptions) -I$(VDOT_DATA)
ifneq ($(VDOT_OBJ_ROOT),)
DST_DIR := $(VDOT_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
