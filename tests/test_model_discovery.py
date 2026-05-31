from src.model_discovery import ModelDiscovery


def test_model_discovery_scans_common_openai_compatible_ports(monkeypatch):
    md = ModelDiscovery(default_host="localhost")
    targets = md._targets(["localhost"])

    assert "http://localhost:11434/v1" in targets
    assert "http://localhost:1234/v1" in targets
    assert "http://localhost:8080/v1" in targets
    assert "http://localhost:30000/v1" in targets
    assert "http://localhost:8000/v1" in targets


def test_model_discovery_accepts_exact_endpoint_env(monkeypatch):
    monkeypatch.setenv(
        "LLM_ENDPOINTS",
        "http://localhost:1234/v1, https://generativelanguage.googleapis.com/v1beta/openai",
    )
    md = ModelDiscovery(default_host="localhost")

    assert md._configured_bases() == [
        "http://localhost:1234/v1",
        "https://generativelanguage.googleapis.com/v1beta/openai",
    ]


def test_model_discovery_labels_found_provider(monkeypatch):
    class Response:
        is_success = True

        def json(self):
            return {"data": [{"id": "llama3.2"}]}

    seen = []

    def fake_get(url, timeout):
        seen.append(url)
        return Response()

    monkeypatch.setattr("src.model_discovery.httpx.get", fake_get)
    result = ModelDiscovery(default_host="localhost")._check_base("http://localhost:11434/v1")

    assert seen == ["http://localhost:11434/v1/models"]
    assert result["provider"] == "ollama"
    assert result["url"] == "http://localhost:11434/v1/chat/completions"
    assert result["models"] == ["llama3.2"]
