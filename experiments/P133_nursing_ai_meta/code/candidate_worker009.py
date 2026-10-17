"""Prospective P133 worker, blocked unless separately authorized by exact source hash.
This file has never been imported/run during preparation.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes
import datetime
import hashlib
import importlib.metadata
import json
import os
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MiB = 1024 ** 2
RESOURCE_OUTPUT_GUARD = None
class MEMORY(ctypes.Structure):
    _fields_ = [("length", wintypes.DWORD), ("load", wintypes.DWORD)] + [(n, ctypes.c_ulonglong) for n in ("total", "avail", "totalpage", "availpage", "totalvirt", "availvirt", "extended")]
class COUNTERS(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in ("peak_working", "working", "quota_peak_paged", "quota_paged", "quota_peak_nonpaged", "quota_nonpaged", "pagefile", "peak_pagefile", "private")]

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(MiB), b""):
            h.update(b)
    return h.hexdigest()

def save(path, obj):
    if RESOURCE_OUTPUT_GUARD is not None:
        RESOURCE_OUTPUT_GUARD.check_output_bytes()
    temp = path.with_name(path.name + ".part")
    with temp.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=True, allow_nan=False)
        f.write("\n")
    if RESOURCE_OUTPUT_GUARD is not None:
        RESOURCE_OUTPUT_GUARD.check_output_bytes()
    temp.replace(path)
    if RESOURCE_OUTPUT_GUARD is not None:
        RESOURCE_OUTPUT_GUARD.check_output_bytes()

class Guard:
    def __init__(self, output, config):
        global RESOURCE_OUTPUT_GUARD
        self.output = output
        self.config = config["resources_proposed"]
        self.start = time.monotonic()
        self.K = ctypes.WinDLL("kernel32", use_last_error=True)
        self.M = ctypes.WinDLL("psapi", use_last_error=True)
        self.K.GetCurrentProcess.restype = wintypes.HANDLE
        self.handle = self.K.GetCurrentProcess()
        self.K.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        self.M.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(COUNTERS), wintypes.DWORD]
        self.M.GetProcessMemoryInfo.restype = wintypes.BOOL
        if not self.K.SetProcessAffinityMask(self.handle, 2):
            raise ctypes.WinError()
        self.phase_count = 0
        self.first_native = self.observation("pre_import")
        RESOURCE_OUTPUT_GUARD = self
    def output_bytes(self):
        total = 0
        pending = [self.output]
        while pending:
            directory = pending.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    info = entry.stat(follow_symlinks=False)
                    if entry.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                        raise RuntimeError("Owned output reparse/link is forbidden")
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        total += info.st_size
                    else:
                        raise RuntimeError("Unexpected owned output filesystem entry")
        return total
    def check_output_bytes(self):
        total = self.output_bytes()
        if total > self.config["output_cap_bytes"]:
            raise RuntimeError("Transparent owned output-byte resource stop; no restart")
        return total
    def observation(self, phase):
        m = MEMORY(); m.length = ctypes.sizeof(m)
        if not self.K.GlobalMemoryStatusEx(ctypes.byref(m)):
            raise ctypes.WinError()
        c = COUNTERS(); c.cb = ctypes.sizeof(c)
        if not self.M.GetProcessMemoryInfo(self.handle, ctypes.byref(c), c.cb):
            raise ctypes.WinError()
        return {"UTC": now(), "phase": phase, "elapsed_seconds": time.monotonic() - self.start, "available_bytes": int(m.avail), "native_peak_working_bytes": int(c.peak_working), "native_peak_pagefile_bytes": int(c.peak_pagefile), "native_private_bytes": int(c.private), "free_disk_bytes": shutil.disk_usage(ROOT).free, "owned_output_bytes": self.output_bytes()}
    def __call__(self, phase):
        record = self.observation(phase)
        self.phase_count += 1
        with (self.output / "phase_events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")
        save(self.output / "progress.json", {"state": "running", "pid": os.getpid(), "phase_count": self.phase_count, **record})
        r = self.config
        if record["available_bytes"] < r["continuous_available_bytes"] or record["native_peak_working_bytes"] > r["per_process_native_working_peak_bytes"] or record["native_peak_pagefile_bytes"] > r["per_process_native_private_peak_bytes"] or record["free_disk_bytes"] < r["disk_reserve_bytes"] or record["elapsed_seconds"] > r["worker_deadline_seconds"] or self.check_output_bytes() > r["output_cap_bytes"]:
            raise RuntimeError("Transparent resource stop; no restart")
        return record

def verify_authorization(args):
    if not args.authorization.is_file():
        raise RuntimeError("No separate numerical execution authorization")
    auth = json.loads(args.authorization.read_text(encoding="utf-8"))
    if auth.get("mode") != args.mode or auth.get("execution_authorized") is not True or auth.get("scope") != "P133_candidate004":
        raise RuntimeError("Mode/scope execution authority missing")
    freeze = HERE / "PROSPECTIVE_IMPLEMENTATION_SOURCE_FREEZE004.json"
    if auth.get("source_freeze_sha256") != sha(freeze):
        raise RuntimeError("Authorization not bound to frozen source")
    additive = HERE / "RESOURCE_ONLY_IMPLEMENTATION_FREEZE010.json"
    if auth.get("resource_only_additive_freeze_sha256") != sha(additive) or auth.get("worker_sha256") != sha(Path(__file__)):
        raise RuntimeError("Authorization must bind resource-only additive freeze and worker007")
    if auth.get("final_native_private_verification_required") is not True:
        raise RuntimeError("Final retained native private/tree evidence verification required")
    repair = HERE / "PROSPECTIVE_NUMERICAL_SOURCE_REPAIR_FREEZE027.json"
    if auth.get("numerical_source_repair_freeze_sha256") != sha(repair):
        raise RuntimeError("Authorization must bind prospective source-repair027 freeze")
    files = json.loads(freeze.read_text(encoding="utf-8"))["files"] + json.loads(additive.read_text(encoding="utf-8"))["files"] + json.loads(repair.read_text(encoding="utf-8"))["files"]
    for r in files:
        p = ROOT / r["path"]
        if p.stat().st_size != r["bytes"] or sha(p) != r["sha256"]:
            raise RuntimeError("Prelaunch source hash mismatch")
    if auth.get("external_native_guardian_verified") is not True or auth.get("bytecode_suppression_verified") is not True:
        raise RuntimeError("Reviewed outer native tree/exit collector and bytecode suppression required")
    return auth

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("fixture", "original"))
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    auth = verify_authorization(args)
    args.output = args.output.resolve()
    if ROOT not in args.output.parents or args.output.exists():
        raise RuntimeError("New unique output directory within workspace required")
    args.output.mkdir()
    config = json.loads((HERE / "CANDIDATE_METHOD_AND_RESOURCE_CONFIG004.json").read_text(encoding="utf-8"))
    guard = Guard(args.output, config)
    save(args.output / "launch_record.json", {"UTC": now(), "pid": os.getpid(), "mode": args.mode, "auth_path": str(args.authorization), "auth_sha256": sha(args.authorization), "source_freeze": sha(HERE / "PROSPECTIVE_IMPLEMENTATION_SOURCE_FREEZE004.json"), "configuration": config, "native_before": guard.first_native})
    status, result = "resource_or_engineering_failure", None
    try:
        # Continuous external guardian must enforce fresh readiness/tree caps as well.
        guard("immediately_before_numeric_import")
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
            os.environ[name] = "1"
        import candidate_core007 as core
        core.initialize_numeric_runtime()
        guard("immediately_after_numeric_import")
        versions = {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "psutil")}
        if versions != {"numpy": "2.3.4", "scipy": "1.17.1", "psutil": "7.1.3"}:
            raise RuntimeError("Frozen numeric runtime metadata mismatch")
        import candidate_pipeline007 as pipeline
        model_dir = args.output / "model_records"
        model_dir.mkdir()
        record_count = [0]
        def emit_record(kind, value):
            record_count[0] += 1
            save(model_dir / (str(record_count[0]).zfill(6) + ".json"), {"sequence": record_count[0], "UTC": now(), "kind": kind, "data": value})
        pipeline.set_recorder(emit_record)
        bundle = pipeline.source_bundle(ROOT)
        if args.mode == "fixture":
            from synthetic_fixture004 import synthetic_bundle
            bundle = synthetic_bundle(bundle)
        rows = bundle["rows"]
        pipeline.validate_canonical(rows, bundle["gates"], original=args.mode == "original")
        save(args.output / "canonical_input.json", bundle)
        guard("complete_suite_start")
        result = pipeline.run_complete_suite(rows, guard)
        result["mode"] = args.mode
        result["structural_census"] = pipeline.structural_census(result, rows)
        result["primary_output_values"] = pipeline.primary_outputs(result, bundle["gates"])
        result["supporting_output_values"] = pipeline.supporting_outputs(result, bundle["gates"])
        if args.mode == "original":
            comparison = pipeline.compare_all_inputs_and_outputs(rows, result, bundle["gates"])
            result["source_claims"] = pipeline.source_claims(result, comparison)
            save(args.output / "gate_comparisons.json", comparison)
            # Preliminary numerical gate status only; independent audit/root must decide.
            status = "primary_numeric_pass_pending_audit" if comparison["input_pass"] and comparison["primary263_pass"] and all(x["passed"] for x in result["source_claims"][:3]) else "primary_numeric_failure"
        else:
            from engineering_checks004 import engineering_checks
            result["engineering_checks"] = engineering_checks(core, pipeline, rows, result, guard)
            result["fixture"] = bundle["fixture"]
            result["source_claims"] = None
            save(args.output / "gate_comparisons.json", {"status": "unrelated_fixture_no_original_source_fit_comparisons", "expected_input_IDs": [g["id"] for g in bundle["gates"]["input_gates"]], "expected_primary_IDs": [g["id"] for g in bundle["gates"]["primary_output_gates"]], "expected_support_IDs": [g["id"] for g in bundle["gates"]["supporting_literal_gates"]], "scientific_credit": False})
            status = "fixture_complete_pending_independent_engineering_audit"
        save(args.output / "result.json", result)
        guard("complete_suite_finished")
        save(args.output / "runtime_metadata.json", {"versions": versions, "python": sys.version, "executable": sys.executable, "threads_env": {k: os.environ[k] for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}, "CPU_affinity": [1], "floating_type": "float64", "software_deviation": "Independent Python numerical port, paper reports R4.5.0; not author-exact", "scientific_credit": False})
    except BaseException as exc:
        save(args.output / "failure.json", {"UTC": now(), "error": str(exc), "exception_type": type(exc).__name__, "state": status, "native": guard.observation("failure"), "no_restart": True})
        raise
    finally:
        save(args.output / "progress.json", {"UTC": now(), "state": status, "pid": os.getpid(), "native_final_self_before_exit": guard.observation("finally"), "actual_native_exit_pending_external_collector": True, "no_own_success_credit": True})
    print(json.dumps({"status": status, "output": str(args.output)}, ensure_ascii=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
