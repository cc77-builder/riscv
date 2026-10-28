NAME = vdot-perf
SRCS = main.c
INC_DIR += $(CURDIR) $(C8_SDK)/include
CFLAGS += -ffreestanding -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
ifneq ($(R4_OBJ_ROOT),)
DST_DIR := $(R4_OBJ_ROOT)
endif
include $(AM_HOME)/Makefile.app

# Replace only the old GEMV object slot with the complete C8 archive.
LINK_FILES = $(OBJS) $(C8_SDK)/libxs_gemv_c8.a $(AM_HOME)/am/build/am-$(ARCH).a $(AM_HOME)/libs/klib/build/klib-$(ARCH).a

# Record member provenance without changing compiler/linker semantics.
LDFLAGS += -Map=$(R4_LINK_MAP) --trace
