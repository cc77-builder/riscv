source team/scripts/activate.sh
export VDOT_O2_ELASTIC=1 VDOT_O1_HANDOFF=0 VDOT_O1_TRACE=0 VDOT_T14_FUSED_INPUT=1 VDOT_O2_TRACE=1 VDOT_T12_TRACE=0 VDOT_T13_TRACE=1
export CHISEL_FIRTOOL_PATH="$HOME/.cache/llvm-firtool/1.62.1/bin"
make emu CONFIG=MinimalConfig NUM_CORES=1 EMU_THREADS=1 JVM_XMX=12G OPT_FAST=-O3 OPT_SLOW=-O0 EMU_TRACE=0 WITH_CHISELDB=0 WITH_CONSTANTIN=0 WITH_ROLLINGDB=0 -j2 SHELL=/usr/bin/bash 'TIME_CMD=/usr/bin/time -avp -o '"'"'$(TIMELOG)'"'"'' CXX=/usr/bin/x86_64-linux-gnu-g++-13 CC=/usr/bin/x86_64-linux-gnu-gcc-13
