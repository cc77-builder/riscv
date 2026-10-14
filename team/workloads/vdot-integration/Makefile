NAME = vdot-integration
HARNESS = ../vdot-exceptions
SRCS = main.c $(HARNESS)/judge.c $(HARNESS)/diagnostics.c $(HARNESS)/harness.S $(HARNESS)/fixed-sites.S
VDOT_DATA ?= $(abspath ../../out/t10-core-data)
INC_DIR += $(VDOT_DATA) $(abspath $(HARNESS))
CFLAGS += -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns -ffreestanding
ASFLAGS += -I$(abspath $(HARNESS)) -I$(VDOT_DATA)
ifneq ($(VDOT_OBJ_ROOT),)
DST_DIR := $(VDOT_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
