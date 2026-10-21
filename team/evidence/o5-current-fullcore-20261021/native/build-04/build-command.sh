source team/scripts/activate.sh
export VDOT_O2_ELASTIC=1 VDOT_O1_HANDOFF=0 VDOT_O1_TRACE=0 VDOT_T14_FUSED_INPUT=1 VDOT_O2_TRACE=1 VDOT_T12_TRACE=0 VDOT_T13_TRACE=1
export CHISEL_FIRTOOL_PATH="$HOME/.cache/llvm-firtool/1.62.1/bin"
/usr/bin/python3.12 /home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021/repo/team/optimizations/o1/split_recipe.py --pins /home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021/build-04/hardware-inputs-before.json --output /home/amesotten/.cache/codex-rvinno/o5-fullcore-20261021/build-04/split
