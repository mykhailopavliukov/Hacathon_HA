from app import main


def test_server_settings_defaults_to_local_only(monkeypatch):
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    assert main.server_settings() == {"host": "127.0.0.1", "port": 8080}


def test_server_settings_read_environment(monkeypatch):
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "10000")
    assert main.server_settings() == {"host": "0.0.0.0", "port": 10000}
