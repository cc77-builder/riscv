source team/scripts/activate.sh
make -C team/workloads/vdot-regression ARCH=riscv64-xs MARCH=rv64gcv T12_DATA=/home/riscv/riscv-lab/t14-optimization-20261015/runs/control-sweep-02/data T12_OBJ_ROOT=/home/riscv/riscv-lab/t14-optimization-20261015/runs/control-sweep-02/objects BINARY=/home/riscv/riscv-lab/t14-optimization-20261015/runs/control-sweep-02/vdot-regression -j2
