from services.hwfit import fit


def _model(name, params, mmlu):
    return {
        "name": name,
        "provider": name.split("/")[0],
        "parameter_count": f"{params}B",
        "parameters_raw": int(params * 1_000_000_000),
        "quantization": "Q4_K_M",
        "context_length": 4096,
        "use_case": "General purpose text generation",
        "benchmarks": [{"name": "mmlu", "value": mmlu, "source": "test"}],
    }


def test_rank_models_prioritizes_fit_before_benchmark_quality(monkeypatch):
    models = [
        _model("great-but-too-large/Model-70B", 70, 99),
        _model("fits-best-quality/Model-2B", 2, 80),
        _model("fits-lower-quality/Model-1B", 1, 60),
    ]
    monkeypatch.setattr(fit, "get_models", lambda: models)
    system = {
        "has_gpu": True,
        "gpu_vram_gb": 8,
        "gpu_count": 1,
        "available_ram_gb": 16,
        "backend": "cuda",
        "gpu_name": "RTX 4060",
    }

    ranked = fit.rank_models(system, sort="score", limit=3, quant="Q4_K_M")

    assert ranked[0]["name"] == "fits-best-quality/Model-2B"
    assert ranked[1]["name"] == "fits-lower-quality/Model-1B"
    assert ranked[-1]["name"] == "great-but-too-large/Model-70B"
    assert ranked[-1]["fit_possible"] is False


def test_benchmark_quality_source_is_exposed():
    model = _model("benchmarked/Model-2B", 2, 0.75)
    result = fit.analyze_model(
        model,
        {
            "has_gpu": True,
            "gpu_vram_gb": 8,
            "gpu_count": 1,
            "available_ram_gb": 16,
            "backend": "cuda",
            "gpu_name": "RTX 4060",
        },
        target_quant="Q4_K_M",
    )

    assert result["quality_source"] == "benchmark"
    assert result["benchmark_details"][0]["name"] == "mmlu"
    assert result["scores"]["quality"] > 60


def test_rank_models_uses_fit_category_after_quality(monkeypatch):
    models = [
        {**_model("perfect-fit/Model-2B", 2, 75), "recommended_ram_gb": 2},
        {**_model("marginal-fit/Model-12B", 12, 75), "recommended_ram_gb": 16},
    ]
    monkeypatch.setattr(fit, "get_models", lambda: models)
    system = {
        "has_gpu": True,
        "gpu_vram_gb": 8,
        "gpu_count": 1,
        "available_ram_gb": 16,
        "backend": "cuda",
        "gpu_name": "RTX 4060",
    }

    ranked = fit.rank_models(system, sort="score", limit=2, quant="Q4_K_M")

    assert ranked[0]["name"] == "perfect-fit/Model-2B"
    assert ranked[0]["fit_level"] == "perfect"
    assert ranked[1]["fit_level"] == "marginal"
