"""Attribute the C1 mapped DFF count change using semantic Q/QN aliases."""
import argparse, hashlib, json
from pathlib import Path

def scan(root):
    path = root / "parent-map-01/mapped.json"
    design = json.loads(path.read_text())["modules"]["CommonParentCostTop"]
    cells = {name: cell for name, cell in design["cells"].items()
             if cell["type"].startswith("DFF")}
    drivers = {}
    for name, cell in cells.items():
        for pin in ("Q", "QN"):
            for bit in cell["connections"].get(pin, []):
                if isinstance(bit, int):
                    drivers[bit] = name
    groups = {name: set() for name in cells}
    for name, net in design["netnames"].items():
        if not name.startswith("dut."):
            continue
        for index, bit in enumerate(net["bits"]):
            if bit in drivers:
                groups[drivers[bit]].add(name + (f"[{index}]" if len(net["bits"]) > 1 else ""))
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                count=len(cells)), groups

def compare(before, after):
    bm, bg = scan(before)
    am, ag = scan(after)
    bi = {label: cell for cell, labels in bg.items() for label in labels}
    ai = {label: cell for cell, labels in ag.items() for label in labels}
    removed = {cell: sorted(labels) for cell, labels in bg.items()
               if labels and not labels.intersection(ai)}
    added = {cell: sorted(labels) for cell, labels in ag.items()
             if labels and not labels.intersection(bi)}
    split = {cell: sorted({ai[label] for label in labels if label in ai})
             for cell, labels in bg.items()
             if len({ai[label] for label in labels if label in ai}) > 1}
    merged = {cell: sorted({bi[label] for label in labels if label in bi})
              for cell, labels in ag.items()
              if len({bi[label] for label in labels if label in bi}) > 1}
    result = dict(before=bm, after=am, added=added, removed=removed,
                  split=split, merged=merged,
                  unlabeled_before=sum(not x for x in bg.values()),
                  unlabeled_after=sum(not x for x in ag.values()))
    expected_removed = {"dut.uncer_en_reg", "dut.uncer_en_reg_1"}
    actual_removed = {label for labels in removed.values() for label in labels}
    actual_added = {label for labels in added.values() for label in labels}
    result["exact_expected_change"] = (
        bm["count"] == 17172 and am["count"] == 17171 and
        len(removed) == 2 and len(added) == 1 and
        expected_removed <= actual_removed and
        "dut.elasticDivOccupied_divOwnerIsFp" in actual_added and
        not split and not merged and
        result["unlabeled_before"] == result["unlabeled_after"] == 0)
    result["status"] = "C1_DFF_ATTRIBUTION_PASS" if result["exact_expected_change"] else "REVIEW_REQUIRED"
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.before, args.after)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["exact_expected_change"] else 1)
