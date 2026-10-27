# Build-only C8 SDK. Identity/static qualification belongs to verify_c8_package.py.
# Each invocation requires a fresh OUT; failed outputs are preserved for audit.
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c
.NOTPARALLEL:
.DEFAULT_GOAL := all
CROSS_COMPILE ?= riscv64-linux-gnu-
PYTHON ?= python3
C8_PUBLIC := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

.PHONY: all
all:
	@test -n "$(SOURCE_DIR)" || { echo 'SOURCE_DIR is required' >&2; exit 2; }
	@test -n "$(OUT)" || { echo 'OUT is required and must be fresh' >&2; exit 2; }
	@$(PYTHON) -c 'from pathlib import Path; import hashlib,sys; src=Path(sys.argv[1]).resolve(strict=True); out=Path(sys.argv[2]); public=Path(sys.argv[3]).resolve(strict=True); dst=out.resolve(); roots=[src,public]+[p for p in public.parents if (p/".git").exists()]; (not out.exists() and not out.is_symlink()) or sys.exit("OUT already exists; preserve it and choose a fresh directory"); all(dst!=p and p not in dst.parents and dst not in p.parents for p in roots) or sys.exit("OUT overlaps source/repository"); pins={"gemv.S":"9b8e03d1827ad70105d11566b635c49900c495b3fad6e871a8e25d9fc414a6d2","gemv.h":"d6cbdadb8ed601e1ccd4d308970111588c5fe7e10098b821625630e2b5360be9"}; all((src/n).is_file() and not (src/n).is_symlink() and hashlib.sha256((src/n).read_bytes()).hexdigest()==h for n,h in pins.items()) or sys.exit("qualified source hash mismatch"); out.mkdir(parents=True,exist_ok=False); (out/"include").mkdir()' "$(SOURCE_DIR)" "$(OUT)" "$(C8_PUBLIC)"
	"$(CROSS_COMPILE)gcc" -march=rv64gcv -mabi=lp64d -mno-relax -c "$(SOURCE_DIR)/gemv.S" -o "$(OUT)/gemv.o"
	@$(PYTHON) -c 'from pathlib import Path; import hashlib,sys; b=Path(sys.argv[1]).read_bytes(); (len(b)==27160 and hashlib.sha256(b).hexdigest()=="f8bc13daeead98a414f313600a5778c96ac95a66b5bcb5c714ea3b98e0d25ab3") or sys.exit("rebuilt object differs from qualified complete object")' "$(OUT)/gemv.o"
	"$(CROSS_COMPILE)ar" rcsD "$(OUT)/libxs_gemv_c8.a" "$(OUT)/gemv.o"
	cp -- "$(SOURCE_DIR)/gemv.h" "$(OUT)/include/config_reuse_gemv.h"
	cp -- "$(C8_PUBLIC)selected_gemv_c8.h" "$(OUT)/include/selected_gemv_c8.h"
	cp -- "$(C8_PUBLIC)example.c" "$(OUT)/example.c"
	cp -- "$(C8_PUBLIC)../CONTRACT.md" "$(OUT)/CONTRACT.md"
	@echo C8_SDK_BUILD_COMPLETE_RUNTIME_NOT_TESTED
