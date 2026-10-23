NAME = vdot-perf
T13_DATA ?= $(abspath ../../out/t13/data)
SRCS = main.c $(T13_DATA)/kernels.S
INC_DIR += $(T13_DATA)
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
ifneq ($(T13_OBJ_ROOT),)
DST_DIR := $(T13_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app

LDFLAGS := $(subst -T $(AM_HOME)/am/src/nemu/isa/riscv/boot/loader64.ld,-T $(abspath fixed-layout.ld),$(LDFLAGS))
