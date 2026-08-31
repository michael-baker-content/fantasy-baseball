"""Small, dependency-free client for MLB's public Stats API."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://statsapi.mlb.com/api"


class MlbStatsClient:
    def __init__(self, cache_dir: str | Path = "data/mlb_cache") -> None:
        self.cache_dir = Path(cache_dir)

    def _get(self, path: str, params: dict | None = None) -> dict:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{BASE_URL}{path}{query}"
        request = Request(url, headers={"User-Agent": "BABBD-postseason-tracker/1.0"})
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    def postseason_schedule(self, season: int) -> dict:
        return self._get("/v1/schedule/postseason", {"season": season, "sportId": 1})

    def schedule(self, start_date: str, end_date: str, game_types: str = "R") -> dict:
        return self._get("/v1/schedule", {
            "sportId": 1,
            "startDate": start_date,
            "endDate": end_date,
            "gameTypes": game_types,
        })

    def game_feed(self, game_pk: int, refresh: bool = False) -> dict:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / f"{game_pk}.json"
        if path.exists() and not refresh:
            return json.loads(path.read_text(encoding="utf-8"))
        data = self._get(f"/v1.1/game/{game_pk}/feed/live")
        path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        return data
