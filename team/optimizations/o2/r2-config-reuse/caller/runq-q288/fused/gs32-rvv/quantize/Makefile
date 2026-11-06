CC = $(CROSS_COMPILE)gcc
LD = $(CROSS_COMPILE)ld
OBJCOPY = $(CROSS_COMPILE)objcopy
CFLAGS += -O2 -Wall -Werror -march=rv64gv -mcmodel=medany -fno-pic
CFLAGS += -std=gnu11 -ffreestanding -fno-builtin -ffp-contract=off -fno-fast-math -fno-lto
CFLAGS += -fno-tree-vectorize -fno-tree-slp-vectorize -fno-tree-loop-distribute-patterns
CFLAGS += -fno-ipa-cp -fno-ipa-icf -mno-relax -mabi=lp64d -fno-stack-protector
CFLAGS += -ffunction-sections -fdata-sections -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0
CFLAGS += -Wno-error=unused-variable -Wno-error=unused-function
CFLAGS += -fno-asynchronous-unwind-tables -fno-unwind-tables
OBJECTS = $(QUANT_OBJ_ROOT)/main.o $(QUANT_OBJ_ROOT)/probe.o $(QUANT_OBJ_ROOT)/entry.o
LINK_FILES = original-consumer-core.o candidate.o bad-rne.o bad-keep-flags.o bad-entry-flags.o
.PHONY: image
image: $(BINARY).bin
$(QUANT_OBJ_ROOT):
	mkdir -p $@
$(QUANT_OBJ_ROOT)/%.o: %.c | $(QUANT_OBJ_ROOT)
	$(CC) $(CFLAGS) -c $< -o $@
$(QUANT_OBJ_ROOT)/%.o: %.S | $(QUANT_OBJ_ROOT)
	$(CC) -march=rv64gv -mabi=lp64d -mno-relax -c $< -o $@
$(BINARY).elf: $(OBJECTS) $(LINK_FILES) linker.ld
	$(LD) -melf64lriscv -static --no-relax --gc-sections --emit-relocs -T linker.ld -Map=$(BINARY).map -o $@ $(OBJECTS) $(LINK_FILES) $(MATH_ARCHIVE)
$(BINARY).bin: $(BINARY).elf
	$(OBJCOPY) -S --set-section-flags .bss=alloc,contents -O binary $< $@
