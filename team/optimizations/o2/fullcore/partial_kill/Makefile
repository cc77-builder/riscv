NAME = partial-v2
PARTIAL_DATA ?= $(abspath data)
SRCS = main.c $(PARTIAL_DATA)/kernels.S
INC_DIR += $(PARTIAL_DATA)
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
DST_DIR := $(PARTIAL_OBJECTS)
include $(AM_HOME)/Makefile.app
