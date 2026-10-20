source team/scripts/activate.sh
export VDOT_T14_FUSED_INPUT=1 VDOT_O1_HANDOFF=0 VDOT_O2_ELASTIC=1 VDOT_O2_TRACE=1 VDOT_O1_TRACE=0 VDOT_T12_TRACE=0 VDOT_T13_TRACE=0
export JAVA_OPTS="-Xmx12G -Xss16m"
export CHISEL_FIRTOOL_PATH="$HOME/.cache/llvm-firtool/1.62.1/bin"
mill -i -j 2 vdotElasticParent.runMain team.vdot.GenerateVDotElasticParent /home/riscv/riscv-lab/o2-fullcore-20261019/observer-elaboration-01/rtl
