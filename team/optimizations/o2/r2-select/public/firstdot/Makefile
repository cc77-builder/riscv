# Team-owned V2 package. Reuse the qualified firstdot sources without edits.
CROSS_COMPILE ?= riscv64-linux-gnu-
OUT ?= build
HERE := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
FIRSTDOT := $(abspath $(HERE)/../../../r2-vector-accum/firstdot/public)

.PHONY: all
all: $(OUT)/libxs_gemv_firstdot.a $(OUT)/include/selected_gemv.h $(OUT)/include/firstdot_gemv.h

$(OUT) $(OUT)/include:
	mkdir -p "$@"

$(OUT)/gemv.o: $(FIRSTDOT)/gemv.S | $(OUT)
	$(CROSS_COMPILE)gcc -march=rv64gcv -mabi=lp64d -mno-relax -c "$<" -o "$@"

$(OUT)/libxs_gemv_firstdot.a: $(OUT)/gemv.o
	$(CROSS_COMPILE)ar rcsD "$@" "$<"

$(OUT)/include/selected_gemv.h: $(HERE)/selected_gemv.h | $(OUT)/include
	cp "$<" "$@"

$(OUT)/include/firstdot_gemv.h: $(FIRSTDOT)/gemv.h | $(OUT)/include
	cp "$<" "$@"
