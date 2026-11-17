"""Local launch refuses altered model bytes and insecure/occupied startup state."""
import json
import socket

import pytest

from scripts.run_local_workspace import ensure_ports_free, private_token, validate_assets


def test_private_token_is_owner_only_and_never_silently_rotated(tmp_path):
    path = tmp_path / 'local.json'
    original = private_token(path)
    assert len(original) >= 32 and path.stat().st_mode & 0o077 == 0
    assert private_token(path) == original
    path.chmod(0o644)
    with pytest.raises(ValueError, match='owner-only'):
        private_token(path)
    path.chmod(0o600)
    path.write_text(json.dumps({'api_token':'short'}))
    with pytest.raises(ValueError, match='invalid'):
        private_token(path)


def test_occupied_loopback_port_is_not_taken_over():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        listener.listen()
        with pytest.raises(ValueError, match='occupied'):
            ensure_ports_free([listener.getsockname()[1]])


def test_altered_gguf_refuses_before_any_process_is_started(tmp_path):
    binary = tmp_path / 'existing-binary'
    binary.write_text('unused')
    binary.chmod(0o700)
    audit = tmp_path / 'audit.json'
    audit.write_text('{}')
    gguf = tmp_path / 'model.gguf'
    gguf.write_bytes(b'changed bytes')
    with pytest.raises(ValueError, match='pinned'):
        validate_assets(binary,binary,tmp_path,gguf,audit,tmp_path)
