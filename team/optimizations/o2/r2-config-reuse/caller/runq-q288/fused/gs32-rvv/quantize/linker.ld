/* Team-owned standalone reference experiment. No device runtime is linked. */
OUTPUT_ARCH(riscv)
ENTRY(_start)
SECTIONS
{
  . = 0x80000000;
  .text : { KEEP(*(.text.quant_entry)) *(.text .text.*) }
  .rodata : ALIGN(16) { *(.rodata .rodata.* .srodata .srodata.*) }
  .data : ALIGN(16) { *(.data .data.* .sdata .sdata.*) }
  PROVIDE(__global_pointer$ = ADDR(.data) + 0x800);
  .bss : ALIGN(16) { *(.bss .bss.* .sbss .sbss.*) *(COMMON) }
  .stack (NOLOAD) : ALIGN(16) {
    __quant_stack_bottom = .;
    . += 65536;
    __quant_stack_top = .;
  }
  /DISCARD/ : { *(.eh_frame .eh_frame_hdr .comment) }
}
