#!/usr/bin/env python3
"""Check a full-domain arithmetic certificate extracted from actual Yosys RTL.

This intentionally recognizes only the observed unsigned, equal-width add and
bitwise cells. Unknown graphs fail closed. No RTL name or random sample grants
a positive proof. Eight-case truth tables establish the local compressor lemma;
actual bit connections and a multiset conservation certificate compose it.
"""
import argparse
from collections import Counter
import importlib.util
import itertools
import json
import os
from pathlib import Path
import re
import signal


def need(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    return int(value, 2) if isinstance(value, str) else value


def signed_extend(bits, width):
    need(len(bits) <= width, "truncated signed operand")
    return tuple(bits) + (bits[-1],) * (width - len(bits))


def pair(a, b):
    return frozenset(Counter((tuple(a), tuple(b))).items())


class Graph:
    def __init__(self, document, strict=True):
        self.strict = strict
        need(set(document["modules"]) == {"VDotReduce"}, "unexpected modules")
        m = document["modules"]["VDotReduce"]
        need(not m.get("memories") and not m.get("processes"), "state or processes")
        need(not number(m.get("attributes", {}).get("blackbox", 0)), "black box")
        expected = {"io_products_" + str(i): ("input", 16) for i in range(8)}
        expected["io_result"] = ("output", 128)
        need({n: (p["direction"], len(p["bits"])) for n, p in m["ports"].items()} == expected,
             "complete IO domain differs")
        self.inputs = [tuple(m["ports"]["io_products_" + str(i)]["bits"]) for i in range(8)]
        self.output = tuple(m["ports"]["io_result"]["bits"])
        input_bits = [b for v in self.inputs for b in v]
        need(len(set(input_bits)) == 128 and all(type(b) is int for b in input_bits), "aliased/constrained inputs")
        self.cells, self.drivers, self.vectors = {}, {}, {}
        for name, cell in m["cells"].items():
            need(cell["type"] in ("$add", "$xor", "$and", "$or"), "unsupported cell " + cell["type"])
            need(cell["port_directions"] == {"A": "input", "B": "input", "Y": "output"}, "cell port directions")
            c = {p: tuple(bits) for p, bits in cell["connections"].items()}
            need(set(c) == {"A", "B", "Y"}, "unexpected cell port")
            p = {k: number(v) for k, v in cell["parameters"].items()}
            w = len(c["Y"])
            need(p == dict(A_SIGNED=0, B_SIGNED=0, A_WIDTH=len(c["A"]), B_WIDTH=len(c["B"]), Y_WIDTH=w)
                 and w > 0 and (not strict or len(c["A"]) == len(c["B"]) == w), "unsupported cell widths/signs")
            for b in c["Y"]:
                need(type(b) is int and b not in self.drivers and b not in input_bits, "duplicate/constrained driver")
                self.drivers[b] = name
            need(c["Y"] not in self.vectors, "duplicate output vector")
            self.vectors[c["Y"]] = name
            self.cells[name] = dict(c, op=cell["type"], width=w)
        known = set(input_bits) | set(self.drivers) | {"0", "1"}
        need(all(b in known for c in self.cells.values() for p in ("A", "B", "Y") for b in c[p])
             and all(b in known for b in self.output), "undefined/X/Z bit")
        pending, ordered, done = set(self.cells), [], set(input_bits) | {"0", "1"}
        while pending:
            ready = sorted(n for n in pending if all(b in done for p in ("A", "B") for b in self.cells[n][p]))
            need(ready, "cyclic combination graph")
            for n in ready:
                ordered.append(n)
                done.update(self.cells[n]["Y"])
                pending.remove(n)
        self.order = ordered

    def output_is(self, bits):
        need(len(bits) == 19 and self.output == signed_extend(bits, 32) + ("0",) * 96,
             "full 128-bit output extension differs")

    def evaluate(self, values):
        state = {"0": 0, "1": 1}
        for bits, v in zip(self.inputs, values):
            for i, b in enumerate(bits):
                state[b] = (v >> i) & 1
        val = lambda bits: sum(state[b] << i for i, b in enumerate(bits))
        for n in self.order:
            c = self.cells[n]
            a, b = val(c["A"]), val(c["B"])
            v = {"$add": lambda: a + b, "$xor": lambda: a ^ b,
                 "$and": lambda: a & b, "$or": lambda: a | b}[c["op"]]()
            for i, bit in enumerate(c["Y"]):
                state[bit] = (v >> i) & 1
        return val(self.output)


def prove_baseline(graph):
    need(graph.strict, "positive proof requires strict graph")
    known = {v: Counter({i: 1}) for i, v in enumerate(graph.inputs)}
    certificate = []
    need(len(graph.cells) == 7, "baseline cell count")
    for name in graph.order:
        c = graph.cells[name]
        need(c["op"] == "$add", "baseline is not an adder tree")
        operands = []
        for port in ("A", "B"):
            matches = [coeff for bits, coeff in known.items() if len(bits) <= c["width"]
                       and signed_extend(bits, c["width"]) == c[port]]
            need(len(matches) == 1, "baseline signed operand not established")
            operands.append(matches[0])
        coeff = operands[0] + operands[1]
        low, high = -32768 * sum(coeff.values()), 32767 * sum(coeff.values())
        need(-(1 << (c["width"] - 1)) <= low <= high < (1 << (c["width"] - 1)), "baseline signed overflow")
        known[c["Y"]] = coeff
        certificate.append(dict(cell=name, width=c["width"], coefficients=dict(coeff), interval=[low, high]))
    result = graph.output[:19]
    graph.output_is(result)
    need(known.get(result) == Counter(range(8)), "baseline does not sum every lane once")
    return certificate


def prove_candidate(graph):
    need(graph.strict, "positive proof requires strict graph")
    adders = [n for n, c in graph.cells.items() if c["op"] == "$add"]
    need(len(adders) == 1, "candidate must have one final adder")
    final = graph.cells[adders[0]]
    need(final["width"] == 19, "candidate final sum width")
    graph.output_is(final["Y"])
    need(Counter(c["op"] for c in graph.cells.values()) == Counter({"$xor": 12, "$and": 18, "$or": 12, "$add": 1}),
         "unexpected compressor cell coverage")
    for c in graph.cells.values():
        need(c["width"] == (18 if c["op"] in ("$and", "$or") else 19), "compressor cell width")

    def or_leaves(vector):
        name = graph.vectors.get(vector)
        if name is not None and graph.cells[name]["op"] == "$or":
            c = graph.cells[name]
            a, used_a = or_leaves(c["A"])
            b, used_b = or_leaves(c["B"])
            return a + b, used_a | used_b | {name}
        return [vector], set()

    compressors = []
    for outer_name, outer in graph.cells.items():
        if outer["op"] != "$xor":
            continue
        for child_port, other in (("A", "B"), ("B", "A")):
            inner_name = graph.vectors.get(outer[child_port])
            if inner_name is None or graph.cells[inner_name]["op"] != "$xor":
                continue
            inner = graph.cells[inner_name]
            terms = [inner["A"], inner["B"], outer[other]]
            expected = Counter(pair(terms[a][:18], terms[b][:18]) for a, b in ((0, 1), (0, 2), (1, 2)))
            for majority_name, majority in graph.cells.items():
                if majority["op"] != "$or":
                    continue
                leaves, or_cells = or_leaves(majority["Y"])
                and_names = [graph.vectors.get(v) for v in leaves]
                if len(leaves) != 3 or len(or_cells) != 2 or any(n is None or graph.cells[n]["op"] != "$and" for n in and_names):
                    continue
                actual = Counter(pair(graph.cells[n]["A"], graph.cells[n]["B"]) for n in and_names)
                if actual == expected:
                    cells = {outer_name, inner_name, *and_names, *or_cells}
                    need(len(cells) == 7, "reused local compressor cell")
                    compressors.append(dict(sum=outer["Y"], carry=("0",) + majority["Y"], inputs=terms,
                                            cells=sorted(cells)))
    need(len(compressors) == 6, "six actual compressors not uniquely established")
    covered = [name for c in compressors for name in c["cells"]]
    need(len(set(covered)) == 42 and set(covered) | set(adders) == set(graph.cells), "compressor cell reuse or omission")
    terms = Counter((final["A"], final["B"]))
    pending, sequence = list(range(6)), []
    while pending:
        ready = [i for i in pending if terms[compressors[i]["sum"]] > 0 and terms[compressors[i]["carry"]] > 0]
        need(ready, "sum/carry pair not conserved in actual graph")
        i = ready[0]
        c = compressors[i]
        terms.subtract((c["sum"], c["carry"]))
        terms.update(c["inputs"])
        terms = +terms
        pending.remove(i)
        sequence.append(dict(compressor=i, term_count=sum(terms.values())))
    need(terms == Counter(signed_extend(v, 19) for v in graph.inputs), "candidate duplicates/omits/misextends an input")
    truth = []
    for a, b, c in itertools.product((0, 1), repeat=3):
        s, carry = a ^ b ^ c, (a & b) | (a & c) | (b & c)
        need(s + 2 * carry == a + b + c, "compressor identity")
        truth.append([a, b, c, s, carry])
    return dict(compressors=compressors, expansion=sequence, truth_table=truth,
                modulus=1 << 19, signed_sum_interval=[-262144, 262136])


def negative_sources(text):
    edits = [("bit100", "96'h0", "96'h100000000000000000"),
             ("zero-extended-lane", "{{3{io_products_0[15]}}, io_products_0}", "{3'h0, io_products_0}"),
             ("carry-shift", "{six_majority, 1'h0}", "{1'h0, six_majority}"),
             ("low32-sign", "{13{_sum19_T[18]}}", "13'h0")]
    result = {}
    for label, before, after in edits:
        need(text.count(before) == 1, "negative mutation ambiguous: " + label)
        result[label] = text.replace(before, after)
    header, body = text.split(");\n\n", 1)
    need("io_products_7" in body, "missing lane mutation target")
    result["duplicate-lane"] = header + ");\n\n" + re.sub(r"\bio_products_7\b", "io_products_6", body)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("driver", "baseline", "candidate", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    a = p.parse_args()
    spec = importlib.util.spec_from_file_location("r3driver", a.driver)
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    def stop(signum, frame):
        raise InterruptedError("termination signal " + str(signum))
    signal.signal(signal.SIGTERM, stop)
    gold, gate = d.generated(a.baseline, "baseline"), d.generated(a.candidate, "candidate")
    roots = [Path(d.read(x / "result.json")["source_root"]) for x in (a.baseline, a.candidate)]
    out = d.fresh(a.output, [a.baseline, a.candidate, *roots])
    result = dict(contract=d.CONTRACT, status="RUNNING", method="actual RTL structural arithmetic certificate",
                  input_bits=128, output_bits=128, baseline_rtl_sha256=d.sha(gold), candidate_rtl_sha256=d.sha(gate),
                  proof_driver_sha256=d.sha(__file__), helper_sha256=d.sha(a.driver), yosys_sha256=d.sha("/usr/bin/yosys"),
                  started=d.now())
    d.save(out / "result.json", result)
    def convert(label, source):
        script = out / (label + ".ys")
        script.write_text(f"read_verilog -sv -DSYNTHESIS {source}\nprep -top VDotReduce -flatten\nwrite_json {out / (label + '.json')}\n")
        receipt = d.command(["/usr/bin/yosys", "-Q", "-T", "-s", script], out, os.environ.copy(), out, label, 60)
        need(receipt["exit_code"] == 0, "actual RTL conversion failed")
        return d.read(out / (label + ".json"))
    try:
        base = Graph(convert("baseline", gold))
        candidate = Graph(convert("candidate", gate))
        certificate = dict(baseline=prove_baseline(base), candidate=prove_candidate(candidate))
        d.save(out / "certificate.json", certificate)
        negatives = []
        witnesses = [[0] * 8, [-32768] + [0] * 7, [-1] + [0] * 7, [1, 1] + [0] * 6,
                     [0] * 6 + [3, 5], [-32768] * 8, [32767] * 8]
        for label, text in negative_sources(gate.read_text()).items():
            source = out / ("negative-" + label + ".sv")
            source.write_text(text)
            document = convert("negative-" + label, source)
            try:
                prove_candidate(Graph(document))
            except ValueError as exc:
                reason = str(exc)
            else:
                raise ValueError("negative accepted: " + label)
            # This evaluator only finds a concrete counterexample after the
            # strict proof rejected. Unsigned unequal-width operands naturally
            # zero-extend in Python bit operations; it cannot grant a proof.
            bad = Graph(document, strict=False)
            witness = next((v for v in witnesses if bad.evaluate(v) != (sum(v) & 0xffffffff)), None)
            need(witness is not None, "no actual negative counterexample: " + label)
            negatives.append(dict(label=label, rejection=reason, inputs=witness, actual=bad.evaluate(witness),
                                  expected=sum(witness) & 0xffffffff, rtl_sha256=d.sha(source),
                                  json_sha256=d.sha(out / ("negative-" + label + ".json"))))
        d.save(out / "negative-controls.json", negatives)
        result.update(status="R3_GENERATED_REDUCTION_EQUIVALENCE_PASS", certificate_sha256=d.sha(out / "certificate.json"),
                      baseline_json_sha256=d.sha(out / "baseline.json"), candidate_json_sha256=d.sha(out / "candidate.json"),
                      negative_control="actual candidate bit100 and four arithmetic mutations rejected with counterexamples",
                      negative_controls_sha256=d.sha(out / "negative-controls.json"))
    except BaseException as exc:
        result.update(status="FAILED", error=repr(exc))
        raise
    finally:
        result["finished"] = d.now()
        d.save(out / "result.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
