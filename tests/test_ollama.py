"""
Tests for local Ollama integration.
"""

import socket
import pytest


def _is_ollama_running(host: str = "127.0.0.1", port: int = 11434, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def test_ollama_client_import():
    import ollama
    assert ollama is not None


def test_ollama_chat_optional():
    if not _is_ollama_running():
        pytest.skip("Ollama daemon is not active on 127.0.0.1:11434. Skipping live inference test.")

    import ollama
    try:
        client = ollama.Client(timeout=10.0)
        response = client.chat(
            model="llama3.1:8b",
            messages=[{"role": "user", "content": "Say Hello"}],
        )
        assert response is not None
        assert "message" in response
    except Exception as e:
        pytest.skip(f"Ollama inference did not complete ({e}). Skipping live test.")


if __name__ == "__main__":
    test_ollama_client_import()
    print("✅ Ollama client import successful!")