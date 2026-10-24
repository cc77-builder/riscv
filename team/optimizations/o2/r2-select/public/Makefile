# Team-owned library entry. The qualified assembly/header remain unchanged.
CROSS_COMPILE ?= riscv64-linux-gnu-
OUT ?= build

.PHONY: all
all: $(OUT)/libxs_gemv.a

$(OUT):
	mkdir -p "$(OUT)"

$(OUT)/gemv.o: gemv.S | $(OUT)
	$(CROSS_COMPILE)gcc -march=rv64gcv -mabi=lp64d -mno-relax -c "$<" -o "$@"

$(OUT)/libxs_gemv.a: $(OUT)/gemv.o
	$(CROSS_COMPILE)ar rcsD "$@" "$<"
