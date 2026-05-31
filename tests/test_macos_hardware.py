import services.hwfit.hardware as hw


def test_detect_macos_apple_silicon(monkeypatch):
    hw._cache_by_host.clear()

    def fake_run(cmd):
        key = " ".join(cmd) if isinstance(cmd, list) else cmd
        responses = {
            "sysctl -n hw.memsize": str(32 * 1024**3),
            "sysctl -n hw.machine": "arm64",
            "sysctl -n machdep.cpu.brand_string": "Apple M3 Pro",
            "vm_stat": (
                "Mach Virtual Memory Statistics: (page size of 16384 bytes)\n"
                "Pages free: 100000.\n"
                "Pages inactive: 200000.\n"
                "Pages speculative: 50000.\n"
                "Pages purgeable: 50000.\n"
            ),
            "system_profiler SPDisplaysDataType": "Chipset Model: Apple M3 Pro\n",
        }
        return responses.get(key)

    monkeypatch.setattr(hw.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(hw.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(hw, "_run", fake_run)

    system = hw.detect_system(fresh=True)

    assert system["platform"] == "macos"
    assert system["backend"] == "metal"
    assert system["has_gpu"] is True
    assert system["unified_memory"] is True
    assert system["gpu_name"] == "Apple M3 Pro"
    assert system["total_ram_gb"] == 32.0
