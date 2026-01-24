
from utils import error_handling as eh


class DialogCatcher:
    def __init__(self):
        self.calls = []

    def __call__(self, parent, title, message, details=None):
        self.calls.append({"title": title, "message": message, "details": details})


def test_safe_save_and_load_success(tmp_path, monkeypatch):
    catcher = DialogCatcher()
    monkeypatch.setattr(eh, "show_error_dialog", catcher)

    target = tmp_path / "data.json"
    payload = {"name": "Hero", "level": 2}

    assert eh.safe_save_json_file(target, payload, description="hero") is True
    assert catcher.calls == []

    loaded = eh.safe_load_json_file(target, description="hero")
    assert loaded == payload
    assert catcher.calls == []


def test_safe_load_missing_returns_none(tmp_path, monkeypatch):
    catcher = DialogCatcher()
    monkeypatch.setattr(eh, "show_error_dialog", catcher)

    missing = tmp_path / "missing.json"
    assert eh.safe_load_json_file(missing, description="missing") is None
    assert catcher.calls == []


def test_safe_load_invalid_json_shows_error(tmp_path, monkeypatch):
    catcher = DialogCatcher()
    monkeypatch.setattr(eh, "show_error_dialog", catcher)

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ invalid", encoding="utf-8")

    result = eh.safe_load_json_file(bad_file, description="bad file")

    assert result is None
    assert len(catcher.calls) == 1
    assert "Invalid Data File" in catcher.calls[0]["title"]


def test_safe_save_failure_shows_error(tmp_path, monkeypatch):
    catcher = DialogCatcher()
    monkeypatch.setattr(eh, "show_error_dialog", catcher)

    # Point to a file inside a non-existent directory we remove permissions from by mocking
    target = tmp_path / "dir" / "data.json"

    def fake_open(*_, **__):
        raise OSError("boom")

    monkeypatch.setattr("builtins.open", fake_open)

    result = eh.safe_save_json_file(target, {"a": 1}, description="hero")

    assert result is False
    assert len(catcher.calls) == 1
    assert "Save Failed" in catcher.calls[0]["title"]
