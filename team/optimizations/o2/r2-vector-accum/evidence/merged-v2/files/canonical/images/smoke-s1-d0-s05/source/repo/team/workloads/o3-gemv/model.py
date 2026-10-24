"""Independent signed INT8 GEMV oracle; no DUT or cycle input."""
def gemv(matrix, vector):
    if not matrix or not vector or any(len(row) != len(vector) for row in matrix):
        raise ValueError("nonempty rectangular MxK and K required")
    if any(type(x) is not int or not -128 <= x <= 127 for row in matrix for x in row):
        raise ValueError("matrix must contain signed int8")
    if any(type(x) is not int or not -128 <= x <= 127 for x in vector):
        raise ValueError("vector must contain signed int8")
    values = [sum(a * b for a, b in zip(row, vector)) for row in matrix]
    if any(not -(1 << 31) <= x < (1 << 31) for x in values):
        raise ValueError("int32 output overflow")
    return values

def result_bytes(value):
    return (value & 0xffffffff).to_bytes(4, "little") + bytes(12)
