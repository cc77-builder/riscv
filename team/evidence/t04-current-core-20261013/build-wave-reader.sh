#!/usr/bin/env bash
set -euo pipefail
folder=/home/amesotten/.cache/codex-rvinno/t04
gcc -O2 -fPIC -shared '-DFST_CONFIG_INCLUDE=<fst_config.h>' -I/usr/share/verilator/include/gtkwave \
  /usr/share/verilator/include/gtkwave/fstapi.c /usr/share/verilator/include/gtkwave/lz4.c \
  /usr/share/verilator/include/gtkwave/fastlz.c -lz -o "$folder/libfst-reader.so"
g++ -O2 -I/usr/share/verilator/include/gtkwave /mnt/c/Code/RVInno/riscv/team/out/t04-wave-reader.cpp \
  -L"$folder" -Wl,-rpath,"$folder" -lfst-reader -o "$folder/wave-reader"
