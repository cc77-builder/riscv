#!/usr/bin/env python3
"""Assemble plain RISC-V assembly with installed LLVM C API (no CPP/linking).

This is an LLVM static object-generation helper, not a GNU or runtime validator.
Invoke as a separate process: LLVM can terminate on malformed assembly.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path


DEFAULT_LIBRARY = "/usr/lib/x86_64-linux-gnu/libLLVM.so.20.1"
TRIPLE = b"riscv64-unknown-elf"
FEATURES = b"+m,+a,+f,+d,+c,+v,+zicsr,+zifencei"


def assemble(source, output, library=DEFAULT_LIBRARY):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file() or output.exists() or not output.parent.is_dir():
        raise ValueError("existing source and fresh object path in an existing directory required")
    lib = C.CDLL(library)
    ptr, charp, uint = C.c_void_p, C.c_char_p, C.c_uint

    def bind(name, result, args):
        fn = getattr(lib, name)
        fn.restype, fn.argtypes = result, args
        return fn

    for component in ("TargetInfo", "Target", "TargetMC", "AsmPrinter", "AsmParser"):
        bind("LLVMInitializeRISCV" + component, None, [])()
    context_create = bind("LLVMContextCreate", ptr, [])
    context_dispose = bind("LLVMContextDispose", None, [ptr])
    module_create = bind("LLVMModuleCreateWithNameInContext", ptr, [charp, ptr])
    module_dispose = bind("LLVMDisposeModule", None, [ptr])
    set_target = bind("LLVMSetTarget", None, [ptr, charp])
    set_asm = bind("LLVMSetModuleInlineAsm2", None, [ptr, charp, C.c_size_t])
    target_from_triple = bind("LLVMGetTargetFromTriple", C.c_int, [charp, C.POINTER(ptr), C.POINTER(ptr)])
    dispose_message = bind("LLVMDisposeMessage", None, [ptr])
    options_create = bind("LLVMCreateTargetMachineOptions", ptr, [])
    options_dispose = bind("LLVMDisposeTargetMachineOptions", None, [ptr])
    options_cpu = bind("LLVMTargetMachineOptionsSetCPU", None, [ptr, charp])
    options_features = bind("LLVMTargetMachineOptionsSetFeatures", None, [ptr, charp])
    options_abi = bind("LLVMTargetMachineOptionsSetABI", None, [ptr, charp])
    machine_create = bind("LLVMCreateTargetMachineWithOptions", ptr, [ptr, charp, ptr])
    machine_dispose = bind("LLVMDisposeTargetMachine", None, [ptr])
    emit = bind("LLVMTargetMachineEmitToFile", C.c_int, [ptr, ptr, charp, C.c_int, C.POINTER(ptr)])
    get_version = bind("LLVMGetVersion", None, [C.POINTER(uint), C.POINTER(uint), C.POINTER(uint)])

    version = (uint(), uint(), uint())
    get_version(*(C.byref(x) for x in version))
    target, error = ptr(), ptr()
    if target_from_triple(TRIPLE, C.byref(target), C.byref(error)):
        message = C.string_at(error).decode("utf-8", "replace")
        dispose_message(error)
        raise RuntimeError(message)

    context = context_create()
    module = module_create(b"riscv_asm", context)
    options = options_create()
    machine = None
    try:
        options_cpu(options, b"generic-rv64")
        options_features(options, FEATURES)
        options_abi(options, b"lp64d")
        machine = machine_create(target, TRIPLE, options)
        if not machine:
            raise RuntimeError("LLVMCreateTargetMachineWithOptions returned NULL")
        body = Path(source).read_bytes()
        set_target(module, TRIPLE)
        set_asm(module, body, len(body))
        output = Path(output).absolute()
        if emit(machine, module, str(output).encode(), 1, C.byref(error)):
            message = C.string_at(error).decode("utf-8", "replace")
            dispose_message(error)
            raise RuntimeError(message)
        result = output.read_bytes()
        if result[:6] != b"\x7fELF\x02\x01":
            raise RuntimeError("LLVM output is not an ELF64 little-endian object")
        return {
            "scope": "LLVM_STATIC_OBJECT_ONLY",
            "llvm_version": ".".join(str(x.value) for x in version),
            "library": library,
            "triple": TRIPLE.decode(),
            "features": FEATURES.decode(),
            "abi": "lp64d",
            "source": str(Path(source).absolute()),
            "source_sha256": hashlib.sha256(body).hexdigest(),
            "object": str(output),
            "object_sha256": hashlib.sha256(result).hexdigest(),
            "object_size": len(result),
        }
    finally:
        if machine:
            machine_dispose(machine)
        options_dispose(options)
        module_dispose(module)
        context_dispose(context)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--library", default=DEFAULT_LIBRARY)
    args = parser.parse_args()
    print(json.dumps(assemble(args.source, args.output, args.library), indent=2))
