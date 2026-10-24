NAME = vdot-regression
T12_DATA ?= $(abspath ../../out/t12/data)
SRCS = main.c $(T12_DATA)/sequences.S
INC_DIR += $(T12_DATA)
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
ifneq ($(T12_OBJ_ROOT),)
DST_DIR := $(T12_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
