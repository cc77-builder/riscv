OUTPUT_ARCH(riscv)
ENTRY(_start)
PHDRS { text PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }
SECTIONS {
  . = 0x80000000;
  .text : { *(.text.init) *(.text .text.*) } :text
  .rodata : { *(.rodata .rodata.*) } :text
  . = ALIGN(4096);
  .data : { *(.data .data.*) } :data
  . = ALIGN(16);
  __global_pointer$ = . + 0x800;
  .sdata : { *(.sdata .sdata.*) } :data
  . = ALIGN(16);
  __bss_start = .;
  .bss : { *(.sbss .sbss.*) *(.bss .bss.*) *(COMMON) } :data
  . = ALIGN(16);
  __bss_end = .;
}
