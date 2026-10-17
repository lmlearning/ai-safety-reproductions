"""Resource-only helpers; no trial data or statistical estimators."""
import os
for _name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS",
              "NUMEXPR_NUM_THREADS","NUMEXPR_MAX_THREADS","VECLIB_MAXIMUM_THREADS",
              "BLIS_NUM_THREADS"):
    os.environ[_name] = "1"
import time, shutil
_STARTED = time.monotonic()
import psutil

class ResourceGuard:
    def __init__(self, root):
        self.root = root
        self.start = _STARTED
        self.peak_rss = 0
        self.min_available = float("inf")
        self.min_disk = float("inf")
        self.process = psutil.Process()
        self.check()
    def check(self):
        memory = self.process.memory_info()
        rss = max(memory.rss,getattr(memory,"peak_wset",memory.rss))
        available = psutil.virtual_memory().available
        disk = shutil.disk_usage(self.root).free
        elapsed = time.monotonic()-self.start
        self.peak_rss = max(self.peak_rss,rss)
        self.min_available = min(self.min_available,available)
        self.min_disk = min(self.min_disk,disk)
        if rss > 2**30:
            raise RuntimeError("Resource stop: RSS exceeded fixed1GiB bound")
        if available < 1.0*2**30:
            raise RuntimeError("Resource stop: available RAM below fixed1.0GiB floor")
        if disk < 35*2**30:
            raise RuntimeError("Resource stop: disk below fixed35GiB floor")
        if elapsed > 600:
            raise RuntimeError("Resource stop: fixed600sec bound exceeded")
    def summary(self):
        return {"CPU_threads":1,"elapsed_seconds":time.monotonic()-self.start,
                "peak_RSS_bytes":self.peak_rss,
                "minimum_available_RAM_bytes":self.min_available,
                "minimum_free_disk_bytes":self.min_disk,
                "limits":{"RSS_bytes":2**30,"available_RAM_floor_bytes":int(1.0*2**30),
                          "free_disk_floor_bytes":35*2**30,"seconds":600}}
