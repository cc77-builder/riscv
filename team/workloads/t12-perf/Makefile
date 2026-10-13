T12_START ?= 0
T12_COUNT ?= 65535
CFLAGS += -DT12_START=$(T12_START) -DT12_COUNT=$(T12_COUNT)
NAME = t12-perf
SRCS = main.c sites.S ../vdot-exceptions/harness.S ../vdot-exceptions/judge.c
T12_DATA ?= $(abspath ../../out/t12-data)
INC_DIR += $(T12_DATA) $(abspath ../vdot-exceptions)
CFLAGS += -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns -ffreestanding
ASFLAGS += -I$(abspath ../vdot-exceptions) -I$(T12_DATA)
ifneq ($(VDOT_OBJ_ROOT),)
DST_DIR := $(VDOT_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
