#!/usr/bin/env python3
"""Alternative bounded proof of the same generated RTL with ABC FRAIG/CEC.

The original SAT attempt is preserved. No input RTL or acceptance domain is
changed. AIG input/output symbols and widths are checked before comparison.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re


def decisive(log, equivalent):
    positive = "Networks are equivalent" in log
    negative = "Networks are NOT EQUIVALENT" in log
    unresolved = re.search(r"ERROR|Error:|UNDECIDED|undecided|timed out|Time limit", log)
    return not unresolved and ((positive and not negative) if equivalent else (negative and not positive))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("driver", "baseline", "candidate", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    a = p.parse_args()
    spec = importlib.util.spec_from_file_location("r3driver", a.driver)
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    import signal
    def stop(signum, frame):
        raise InterruptedError("termination signal " + str(signum))
    signal.signal(signal.SIGTERM, stop)
    gold, gate = d.generated(a.baseline, "baseline"), d.generated(a.candidate, "candidate")
    roots = [Path(d.read(x / "result.json")["source_root"]) for x in (a.baseline, a.candidate)]
    out = d.fresh(a.output, [a.baseline, a.candidate, *roots])
    result = dict(contract=d.CONTRACT, status="RUNNING", method="ABC FRAIG+SAT automatic partitions",
                  input_bits=128, output_bits=128, baseline_rtl_sha256=d.sha(gold), candidate_rtl_sha256=d.sha(gate),
                  proof_driver_sha256=d.sha(__file__), helper_sha256=d.sha(a.driver), started=d.now(),
                  tool_sha256={p: d.sha(p) for p in ("/usr/bin/yosys", "/usr/bin/berkeley-abc")},
                  input_matching="ABC cec default by name; positive AIG order also identical")
    d.save(out / "result.json", result)
    try:
        text, count = re.subn(r"\bmodule\s+VDotReduce\s*\(", "module VDotReduceCore(", gate.read_text(), count=1)
        d.require(count == 1, "missing generated reduction module")
        ports = ", ".join("input [15:0] io_products_" + str(i) for i in range(8))
        wiring = ", ".join(".io_products_%d(io_products_%d)" % (i, i) for i in range(8))
        text += "\nmodule VDotReduce(" + ports + ", output [127:0] io_result);\nwire [127:0] value;\n"
        text += "VDotReduceCore dut(" + wiring + ", .io_result(value));\nassign io_result = value ^ (128'h1 << 100);\nendmodule\n"
        negative = out / "negative-bit100.sv"
        negative.write_text(text)
        symbols, artifacts = [], []
        for name, source in (("baseline", gold), ("candidate", gate), ("negative", negative)):
            script = out / (name + ".ys")
            script.write_text("\n".join([f"read_verilog -sv -DSYNTHESIS {source}", "prep -top VDotReduce -flatten",
                f"write_json {out / (name + '.json')}", "techmap", "opt", "aigmap", "opt_clean",
                f"write_aiger -ascii -symbols -map {out / (name + '.map')} {out / (name + '.aag')}",
                f"write_aiger -symbols {out / (name + '.aig')}"]) + "\n")
            r = d.command(["/usr/bin/yosys", "-Q", "-T", "-s", script], out, os.environ.copy(), out, name + "-aig", 90)
            d.require(r["exit_code"] == 0, "AIG conversion failed")
            module = d.read(out / (name + ".json"))["modules"]["VDotReduce"]
            ports = {n: (v["direction"], len(v["bits"])) for n, v in module["ports"].items()}
            expected = {"io_products_" + str(i): ("input", 16) for i in range(8)}
            expected["io_result"] = ("output", 128)
            d.require(ports == expected, "proof IO domain changed")
            lines = (out / (name + ".aag")).read_text().splitlines()
            header = lines[0].split()
            d.require(header[0] == "aag" and tuple(map(int, header[2:5])) == (128, 0, 128), "unexpected AIG IO/state")
            table = [line for line in lines if re.match(r"^[io][0-9]+ ", line)]
            d.require(len(table) == 256 and len(set(table)) == 256, "incomplete AIG symbols")
            binary = (out / (name + ".aig")).read_bytes()
            end = binary.index(b"\n")
            bh = binary[:end].decode().split()
            d.require(bh[0] == "aig" and bh[1:] == header[1:], "binary/ASCII AIG headers differ")
            cursor = end + 1
            for _ in range(128):
                end = binary.index(b"\n", cursor)
                d.require(binary[cursor:end].isdigit(), "invalid binary AIG output literal")
                cursor = end + 1
            for _ in range(2 * int(bh[5])):
                while binary[cursor] & 128:
                    cursor += 1
                cursor += 1
            binary_symbols = [line for line in binary[cursor:].decode().splitlines()
                              if re.match(r"^[io][0-9]+ ", line)]
            d.require(binary_symbols == table, "binary/ASCII AIG symbols differ")
            for kind in ("i", "o"):
                entries = [line.split(" ", 1) for line in table if line.startswith(kind)]
                indexes = [int(index[1:]) for index, _ in entries]
                names = [symbol for _, symbol in entries]
                wanted = ({"io_products_%d[%d]" % (i, b) for i in range(8) for b in range(16)}
                          if kind == "i" else {"io_result[%d]" % b for b in range(128)})
                d.require(len(entries) == 128 and set(indexes) == set(range(128))
                          and set(names) == wanted, "AIG bit name/index bijection incomplete")
            symbols.append(table)
            artifacts.append(dict(name=name, rtl_sha256=d.sha(source), aig_sha256=d.sha(out / (name + ".aig")),
                                  ascii_aig_sha256=d.sha(out / (name + ".aag")), symbols=table))
        d.require(symbols[0] == symbols[1], "positive AIG bit symbols/order differ")
        # Flattening the negative wrapper may reorder PIs. ABC's default CEC
        # matches names (the -n toggle would switch to position); all 256 names
        # above are checked against the complete expected bit domain.
        proofs = []
        for name, target, limit in (("equivalence", "candidate", 120), ("negative-bit100", "negative", 20)):
            command = f"cec -T {limit} -C 1000000 -p {out / 'baseline.aig'} {out / (target + '.aig')}"
            r = d.command(["/usr/bin/berkeley-abc", "-c", command], out, os.environ.copy(), out, name, limit + 30)
            log = (out / (name + ".log")).read_text()
            d.require(r["exit_code"] == 0 and decisive(log, name == "equivalence"),
                      name + " not decisively and consistently resolved")
            proofs.append(dict(label=name, log_sha256=d.sha(out / (name + ".log")), command_sha256=d.sha(out / (name + ".command.json"))))
        result.update(status="R3_GENERATED_REDUCTION_EQUIVALENCE_PASS", proofs=proofs, artifacts=artifacts,
                      negative_control="actual candidate output bit100 flip rejected")
    except BaseException as exc:
        result.update(status="FAILED", error=repr(exc))
        raise
    finally:
        result["finished"] = d.now()
        d.save(out / "result.json", result)
    print(json.dumps({k: result[k] for k in ("status", "method", "input_bits", "output_bits")}, indent=2))


if __name__ == "__main__":
    main()
