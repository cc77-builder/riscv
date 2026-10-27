"""Validate the config-reuse ordinary-C adapter's new interfaces and fail-closed bindings."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import struct
import tempfile
from unittest.mock import patch

import c_api as c


def reject(fn):
    try:
        fn()
    except ValueError as exc:
        return str(exc)
    raise AssertionError("invalid C qualification accepted")


def check(repo, identity):
    c.a.parent_identity(repo, identity)
    value = c.a.read(identity)
    parent = c.g.load("config-reuse_test_old_c", repo / c.PARENT)
    with tempfile.TemporaryDirectory(prefix="config-reuse-c-host-") as temp:
        out, again = Path(temp) / "one", Path(temp) / "two"
        manifest = c.generate(repo, out)
        assert c.generate(repo, again) == manifest
        assert all((out / name).read_bytes() == (again / name).read_bytes() for name in parent.FILES)
        assert (out / "main.c").read_text() == parent.MAIN
        assert (out / "Makefile").read_text() == parent.MAKEFILE
        assert manifest["contract"] == c.CONTRACT and manifest["variant"] == "config-reuse"
        assert len(manifest["rows"]) == 16 and len(manifest["cases"]) == 48
        names = {r["api_symbol"] for r in manifest["rows"]}
        assert len(names) == 16 and all(n.startswith("config_reuse_gemv_") for n in names)
        for name in ("gemv.S", "gemv.h", "cases.h"):
            text = (out / name).read_text()
            assert "r4_gemv_" not in text and "firstdot_gemv_" not in text and all(n in text for n in names)
        for shard in (1, 3, 5, 7):
            data = Path(temp) / f"matrix-{shard}"
            known = c.c.generate(repo, data, "config-reuse", 0, shard)
            for row in known["rows"]:
                actual = next(r for r in manifest["rows"] if r["api_symbol"] == c.public_name(row["api_symbol"]))
                assert actual == dict(row, shard=shard, api_symbol=c.public_name(row["api_symbol"]))
        foreign_matrix_rejection = reject(lambda: c.library_anchor(repo, Path(temp) / "not-a-build",
            repo / c.g.S1 / "evidence/firstdot-v1/matrix-archive"))
        assert "full config-reuse matrix required" in foreign_matrix_rejection
        wrong = dict(value["hardware_profile"], emu_sha256="0" * 64)
        app = c.adapter(repo, value)
        with patch.object(c.a.t17.p, "hardware_profile", return_value=({}, wrong)):
            profile_rejection = reject(lambda: app.a.frozen_m.hardware_profile(repo, value["configuration"]))
        fake_run, fake_build = Path(temp) / "run", Path(temp) / "build"
        fake_run.mkdir()
        fake_build.mkdir()
        anchor = dict(status="S3_PUBLIC_LEAVES_MATCH_MATRIX", matrix_manifest_sha256="a" * 64)
        c.g.save(fake_build / "matrix-anchor.json", anchor)
        wrong = c.qualification(anchor)
        wrong["stable_default_changed"] = True
        c.g.save(fake_run / "config-reuse-qualification.json", wrong)
        qualification_rejection = reject(lambda: c.validate_qualification(fake_build, fake_run, anchor))
    assert parent.MAIN == c.g.load("config-reuse_test_old_c_again", repo / c.PARENT).MAIN
    return dict(status="S3_C_ADAPTER_HOST_PASS", unchanged_c_harness=True, unchanged_makefile=True,
                private_generation_repeat_identical=True, public_functions=16, scalar_oracle_cases=48,
                matrix_row_matches=16, old_symbol_collisions=0, foreign_profile_rejected=profile_rejection,
                false_qualification_rejected=qualification_rejection,
                old_firstdot_matrix_rejected=foreign_matrix_rejection, new_emu_runs=0)


def library_tests(source):
    import library
    good = library.byte_check(source)
    rejected = []
    with tempfile.TemporaryDirectory(prefix="config-reuse-library-reject-") as temp:
        for case in ("missing-consumer", "wrong-member", "missing-artifact", "wrong-table-reference"):
            dest = Path(temp) / case
            shutil.copytree(source, dest)
            receipt = c.a.read(dest / "library.json")
            if case == "missing-consumer":
                name = "consumer-linked.o"
                (dest / name).write_bytes((dest / "gemv.o").read_bytes())
                receipt["artifacts"][name] = c.g.sha(dest / name)
            elif case == "wrong-member":
                name = "libconfig_reuse_gemv.a"
                raw = bytearray((dest / name).read_bytes())
                position = raw.find((dest / "gemv.o").read_bytes())
                assert position >= 0
                raw[position] ^= 1
                (dest / name).write_bytes(raw)
                receipt["artifacts"][name] = c.g.sha(dest / name)
            elif case == "missing-artifact":
                del receipt["artifacts"]["consumer.o"]
            else:
                name = "consumer-linked.o"
                raw = bytearray((dest / name).read_bytes())
                elf = c.g.ELF(raw)
                address, size, index, _ = elf.symbols["config_reuse_all_entries"]
                start = address - elf.sections[index][3]
                entries = []
                for section in elf.sections:
                    if section[1] == 4 and section[7] == index:
                        for pos in range(section[4], section[4] + section[5], 24):
                            offset, info, _ = struct.unpack_from("<QQq", raw, pos)
                            if start <= offset < start + size:
                                entries.append((offset, pos, info))
                entries.sort()
                assert len(entries) == 16 and entries[0][2] != entries[1][2]
                struct.pack_into("<Q", raw, entries[0][1] + 8, entries[1][2])
                (dest / name).write_bytes(raw)
                receipt["artifacts"][name] = c.g.sha(dest / name)
            c.g.save(dest / "library.json", receipt)
            rejected.append(dict(case=case, reason=reject(lambda: library.byte_check(dest))))
    return dict(status="S3_LIBRARY_REJECTION_PASS", good=good, rehashed_corruptions=rejected)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--identity", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--library", type=Path)
    args = p.parse_args()
    c.g.require(not args.output.exists(), "new C test output required")
    identity = c.a.parent_identity(args.repo.resolve(), args.identity.resolve())
    cfg = identity["configuration"]
    c.a.outside_inputs(args.output.resolve(), [args.repo.resolve(), args.identity.resolve().parent,
        cfg["hardware_source"], cfg["build_record"], cfg["am_home"],
        *([args.library.resolve()] if args.library else [])])
    value = check(args.repo.resolve(), args.identity.resolve())
    if args.library:
        value["library"] = library_tests(args.library.resolve())
    c.g.save(args.output, value)
    print(json.dumps(value, indent=2))

