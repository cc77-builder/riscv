"""Validate the firstdot ordinary-C adapter's new interfaces and fail-closed bindings."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

import firstdot_c_api as c


def reject(fn):
    try:
        fn()
    except ValueError as exc:
        return str(exc)
    raise AssertionError("invalid C qualification accepted")


def check(repo, identity):
    c.a.parent_identity(repo, identity)
    value = c.a.read(identity)
    parent = c.g.load("firstdot_test_old_c", repo / c.PARENT)
    with tempfile.TemporaryDirectory(prefix="firstdot-c-host-") as temp:
        out, again = Path(temp) / "one", Path(temp) / "two"
        manifest = c.generate(repo, out)
        assert c.generate(repo, again) == manifest
        assert all((out / name).read_bytes() == (again / name).read_bytes() for name in parent.FILES)
        assert (out / "main.c").read_text() == parent.MAIN
        assert (out / "Makefile").read_text() == parent.MAKEFILE
        assert manifest["contract"] == c.CONTRACT and manifest["variant"] == "firstdot"
        assert len(manifest["rows"]) == 16 and len(manifest["cases"]) == 48
        names = {r["api_symbol"] for r in manifest["rows"]}
        assert len(names) == 16 and all(n.startswith("firstdot_gemv_") for n in names)
        for name in ("gemv.S", "gemv.h", "cases.h"):
            text = (out / name).read_text()
            assert "r4_gemv_" not in text and all(n in text for n in names)
        for shard in (1, 3, 5, 7):
            data = Path(temp) / f"matrix-{shard}"
            known = c.c.generate(repo, data, "firstdot", 0, shard)
            for row in known["rows"]:
                actual = next(r for r in manifest["rows"] if r["api_symbol"] == c.public_name(row["api_symbol"]))
                assert actual == dict(row, shard=shard, api_symbol=c.public_name(row["api_symbol"]))
        wrong = dict(value["hardware_profile"], emu_sha256="0" * 64)
        app = c.adapter(repo, value)
        with patch.object(c.a.t17.p, "hardware_profile", return_value=({}, wrong)):
            profile_rejection = reject(lambda: app.a.frozen_m.hardware_profile(repo, value["configuration"]))
        fake_run, fake_build = Path(temp) / "run", Path(temp) / "build"
        fake_run.mkdir()
        fake_build.mkdir()
        anchor = dict(status="FIRSTDOT_PUBLIC_LEAVES_MATCH_MATRIX", matrix_manifest_sha256="a" * 64)
        c.g.save(fake_build / "matrix-anchor.json", anchor)
        wrong = c.qualification(anchor)
        wrong["stable_default_changed"] = True
        c.g.save(fake_run / "firstdot-qualification.json", wrong)
        qualification_rejection = reject(lambda: c.validate_qualification(fake_build, fake_run, anchor))
    assert parent.MAIN == c.g.load("firstdot_test_old_c_again", repo / c.PARENT).MAIN
    return dict(status="FIRSTDOT_C_ADAPTER_HOST_PASS", unchanged_c_harness=True, unchanged_makefile=True,
                private_generation_repeat_identical=True, public_functions=16, scalar_oracle_cases=48,
                matrix_row_matches=16, old_symbol_collisions=0, foreign_profile_rejected=profile_rejection,
                false_qualification_rejected=qualification_rejection, new_emu_runs=0)


def library_tests(source):
    import firstdot_library as library
    good = library.byte_check(source)
    rejected = []
    with tempfile.TemporaryDirectory(prefix="firstdot-library-reject-") as temp:
        for case in ("missing-consumer", "wrong-member", "missing-artifact"):
            dest = Path(temp) / case
            shutil.copytree(source, dest)
            receipt = c.a.read(dest / "library.json")
            if case == "missing-consumer":
                name = "consumer-linked.o"
                (dest / name).write_bytes((dest / "gemv.o").read_bytes())
                receipt["artifacts"][name] = c.g.sha(dest / name)
            elif case == "wrong-member":
                name = "libfirstdot_gemv.a"
                raw = bytearray((dest / name).read_bytes())
                position = raw.find((dest / "gemv.o").read_bytes())
                assert position >= 0
                raw[position] ^= 1
                (dest / name).write_bytes(raw)
                receipt["artifacts"][name] = c.g.sha(dest / name)
            else:
                del receipt["artifacts"]["consumer.o"]
            c.g.save(dest / "library.json", receipt)
            rejected.append(dict(case=case, reason=reject(lambda: library.byte_check(dest))))
    return dict(status="FIRSTDOT_LIBRARY_REJECTION_PASS", good=good, rehashed_corruptions=rejected)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--identity", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--library", type=Path)
    args = p.parse_args()
    assert not args.output.exists()
    value = check(args.repo.resolve(), args.identity.resolve())
    if args.library:
        value["library"] = library_tests(args.library.resolve())
    c.g.save(args.output, value)
    print(json.dumps(value, indent=2))
