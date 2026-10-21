# Explicit shared boot ROM, matching the pinned DiffTest default boot sequence.
.option norvc
.text
.globl _start
_start:
  addiw t0, zero, 1
  slli t0, t0, 31
  jr t0
