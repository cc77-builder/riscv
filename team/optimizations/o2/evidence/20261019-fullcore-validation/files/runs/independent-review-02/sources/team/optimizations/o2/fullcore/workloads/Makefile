NAME = o2-diag
O2_DATA ?= $(abspath data)
SRCS = main.c $(O2_DATA)/kernels.S
INC_DIR += $(O2_DATA)
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
ifneq ($(O2_OBJ_ROOT),)
DST_DIR := $(O2_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
