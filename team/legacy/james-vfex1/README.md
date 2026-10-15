# Historical James VFEX1 candidate

Source: 9bb544812df9b424e399ae3ca91899a904f583bd. These files preserve the
fixed-latency VFEX1 implementation and its tests; they are NOT active production
sources or acceptance tests for VFEX4. Shared source/configuration can be recovered
from that commit in a separate worktree. Never copy this partial directory over
the integrated production tree.

The standalone VdotExec experiment remains available through team/hardware/vdot;
its results describe only that historical executor. Current production checks are
check-vdot-datapath.sh, check-vdot-fu.sh and check-vdot-decode.sh.
Original full-core evidence remains immutable under team/evidence.
