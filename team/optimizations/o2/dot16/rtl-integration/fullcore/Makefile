NAME = dot16-core-smoke
SRCS = main.c kernels.S
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
ifneq ($(SMOKE_OBJ_ROOT),)
DST_DIR := $(SMOKE_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
