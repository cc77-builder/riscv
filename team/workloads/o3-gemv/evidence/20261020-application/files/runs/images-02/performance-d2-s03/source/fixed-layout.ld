/* Same physical addresses for every implementation. Derived from pinned nexus-am section.ld. */
pmem_base = 0x80000000;
MEMORY { ram (rwxa) : ORIGIN = 0x80000000, LENGTH = 128M }
ENTRY(_start)
SECTIONS {
  . = ORIGIN(ram);
  .text : { *(entry) *(.text) }
  etext = .; _etext = .;
  .rodata 0x80080000 : { *(.rodata*) }
  .benchmark_inputs 0x80100000 : { *(.benchmark.inputs) }
  .benchmark_expected 0x80110000 : { *(.benchmark.expected) }
  .benchmark_cases 0x80120000 : { *(.benchmark.cases) }
  .benchmark_result 0x80130000 : { *(.benchmark.result) }
  .benchmark_sink 0x80131000 : { *(.benchmark.sink) }
  .data 0x80140000 : { *(.data) }
  edata = .; _data = .;
  .bss 0x80150000 : { _bss_start = .; *(.bss*) *(.sbss*) *(.scommon) }
  _stack_top = ALIGN(0x1000);
  . = _stack_top + 0x8000; _stack_pointer = .;
  . = _stack_top + 0x320000; end = .; _end = .;
  _heap_start = ALIGN(0x1000);
  _pmem_start = pmem_base; _pmem_end = _pmem_start + LENGTH(ram);
}
