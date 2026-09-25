from datetime import date
import subprocess

import pytest

from scripts import update_site


def test_refreshes_all_views_with_shared_cutoff(tmp_path, monkeypatch):
    monkeypatch.setattr(update_site, "ROOT", tmp_path)
    calls = []
    monkeypatch.setattr(update_site.subprocess, "run", lambda args, **kwargs: calls.append((args, kwargs)))
    update_site.refresh_site(date(2026, 9, 21))
    assert len(calls) == 4
    assert calls[0][0][1:3] == ["-m", "scripts.publish_sheet"]
    for args, kwargs in calls[1:]:
        assert args[args.index("--through") + 1] == "2026-09-21"
        assert kwargs == {"cwd": tmp_path, "check": True}
    assert "--last-30-days" not in calls[2][0]
    assert "--last-30-days" in calls[3][0]
    assert all("--site" in args and "csv" in args for args, _ in calls[2:])


@pytest.mark.parametrize("existing", [True, False])
def test_failed_refresh_restores_site_files(tmp_path, monkeypatch, existing):
    monkeypatch.setattr(update_site, "ROOT", tmp_path)
    data = tmp_path / "docs/data"
    data.mkdir(parents=True)
    paths = [data / "league.json", data / "player-stats.json", data / "sheet-players.json"]
    if existing:
        for path in paths:
            path.write_bytes(b"original")
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        for path in paths:
            path.write_bytes(b"partial update")
        if len(calls) == 2:
            raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(update_site.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        update_site.refresh_site(date(2026, 9, 21))
    assert len(calls) == 2
    for path in paths:
        assert path.read_bytes() == b"original" if existing else not path.exists()
