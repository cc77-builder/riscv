set -e
cd /home/lizufan/riscv-lab/r3-perf-20261025-0001/source
export JAVA_HOME=/home/lizufan/.local/share/graalvm-jdk-21.0.12
export PATH="$JAVA_HOME/bin:/home/lizufan/riscv-lab/r3-perf-20261025-0001/bin:/home/lizufan/riscv-tools/bin:/home/lizufan/riscv-tools/verilator-5.052/bin:/usr/local/llvm/bin:$PATH"
export TEAM_XS_ENV_ROOT=/home/lizufan/riscv-lab/t17-clean-20261024-0854/clean-02/xs-env
export VDOT_RTL_JOBS=4
export VDOT_RTL_JAVA_OPTS='-Xmx5G -Xss8m -XX:ActiveProcessorCount=4'
exec python3 -B team/optimizations/o2/run_rtl.py parent /home/lizufan/riscv-lab/r3-perf-20261025-0001/run-02
