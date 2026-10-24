"""New runtime identity around the unchanged, host-proved S3 generator.

The generated instruction/data bytes stay identical to candidate.py. Runtime
qualification belongs to experiment results, never to a generation manifest.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
S3 = Path("team/optimizations/o2/r2-config-reuse")
CONTRACT = "r2-s3-config-reuse-runtime-v1"
HOST_SHA = "e1ec595c78f3c14314c1d4dc1cc9f49650929e77275ba38241bce541481b15f7"


def private(path):
    spec = importlib.util.spec_from_file_location("s3_private_host_candidate", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


host = private(Path(__file__).with_name("candidate.py"))
FILES, HARNESS = host.FILES, host.HARNESS


def generate(repo, output, variant, dataset, shard, suite="performance"):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    host.require(repo == ROOT and host.sha(repo / S3 / "candidate.py") == HOST_SHA,
                 "runtime generator source identity")
    manifest = host.generate(repo, output, variant, dataset, shard, suite)
    manifest.update(config_reuse_runtime_contract=CONTRACT,
                    runtime_adapter_sha256=host.sha(Path(__file__)))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
