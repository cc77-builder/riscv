#!/usr/bin/env bash
# Source from any directory: source /path/to/riscv/team/scripts/activate.sh
export TEAM_PROJECT_ROOT
TEAM_PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
export TEAM_XS_ENV_ROOT=${TEAM_XS_ENV_ROOT:-"$HOME/riscv-lab/xs-env"}
export JAVA_HOME=${JAVA_HOME:-/opt/graalvm-jdk-21}
export PATH="$JAVA_HOME/bin:/usr/local/llvm/bin:$PATH"
export LINUX_GNU_TOOLCHAIN=1
export XS_PROJECT_ROOT="$TEAM_XS_ENV_ROOT"
export NOOP_HOME="$TEAM_PROJECT_ROOT"
export NEMU_HOME="$TEAM_XS_ENV_ROOT/NEMU"
export AM_HOME="$TEAM_XS_ENV_ROOT/nexus-am"
export DRAMSIM3_HOME="$TEAM_XS_ENV_ROOT/DRAMsim3"
export TEAM_WORKLOAD="$TEAM_PROJECT_ROOT/team/workloads/hello-vadd"
export TEAM_EVIDENCE_DIR=${TEAM_EVIDENCE_DIR:-"$TEAM_PROJECT_ROOT/team/out/$(date +%Y%m%d-%H%M%S)-$$"}
