"""Fixed retained C3-HF state identities; not a timing or functional proof."""
SEMANTICS = ("dut.elasticDivOccupied_divBusy", "dut.uncer_en_reg", "dut.uncer_en_reg_1")
def need(ok, message):
    if not ok:
        raise ValueError(message)
def bind_states(d):
    result = {}
    for semantic in SEMANTICS:
        need(semantic in d.mapping["netnames"], "missing required state: " + semantic)
        bits = d.mapping["netnames"][semantic]["bits"]
        need(len(bits) == 1 and isinstance(bits[0], int), "invalid state bit: " + semantic)
        need(bits[0] in d.drivers, "undriven state: " + semantic)
        cell, pin = d.drivers[bits[0]]
        mapped = d.mapping["cells"][cell]
        need(pin in ("Q", "QN") and mapped["type"].startswith("DFF"), "state not DFF: " + semantic)
        need(len(mapped["connections"].get("D", [])) == 1, "missing D pin: " + semantic)
        need(cell in d.reverse, "missing canonical binding: " + semantic)
        result[semantic] = d.reverse[cell] + "/D"
    need(len(set(result.values())) == 3, "control states aliased to one DFF")
    owner = "dut.elasticDivOccupied_divOwnerIsFp"
    need(owner not in d.mapping["netnames"], "unexpected C1/C2 owner state")
    return result
