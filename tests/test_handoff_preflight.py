"""R4/R12/R13 common A-G: identity success and meaningful mismatch/unavailable failures."""
import pytest

from scripts.preflight_handoff import check_model, inventory, local_endpoint


def test_installed_model_must_keep_digest_quantization_and_vision():
    profile = {"model": "gemma3:4b", "digest": "a" * 64,
               "quantization_level": "Q4_K_M", "capabilities": ["vision"]}
    assert check_model(profile, profile)["status"] == "passed"
    for field, value in [("digest", "b" * 64), ("quantization_level", "Q8_0"), ("capabilities", [])]:
        assert check_model(profile, {**profile, field: value})["status"] == "blocked"


@pytest.mark.parametrize("url", ["http://example.com", "http://localhost.evil", "http://user:secret@localhost:11434",
                                  "http://localhost:11434?key=secret", "http://localhost:11434/api"])
def test_preflight_will_not_forward_credentials_or_probe_an_unrequested_host(url):
    with pytest.raises(ValueError):
        local_endpoint(url)


def test_loopback_and_inventory_do_not_claim_generation_or_completion():
    assert local_endpoint("http://127.0.0.1:11434/") == "http://127.0.0.1:11434"
    report = inventory()
    assert report["checks"]["ollama"]["status"] == "not_probed"
    assert not report["checks"]["ollama"]["generation_executed"]
    assert not report["runtime_prerequisites_ready"] and not report["full_project_complete"]
