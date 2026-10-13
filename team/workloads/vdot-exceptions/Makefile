NAME = vdot-exceptions
SRCS = main.c judge.c diagnostics.c harness.S fixed-sites.S
VDOT_DATA ?= $(abspath ../../out/t05)
MODE ?= full
VDOT_LOG_COMPACT ?= 0
INC_DIR += $(VDOT_DATA)
CFLAGS += -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
CFLAGS += -ffreestanding
CPPFLAGS += -DVDOT_MODE_SELFTEST=$(if $(filter selftest,$(MODE)),1,0)
CPPFLAGS += -DVDOT_LOG_COMPACT=$(VDOT_LOG_COMPACT)
ASFLAGS += -I$(CURDIR) -I$(VDOT_DATA)
ifneq ($(VDOT_OBJ_ROOT),)
DST_DIR := $(VDOT_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app
