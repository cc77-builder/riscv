NAME = vdot-perf
SRCS = main.c gemv.S
INC_DIR += $(CURDIR)
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
ifneq ($(R4_OBJ_ROOT),)
DST_DIR := $(R4_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
