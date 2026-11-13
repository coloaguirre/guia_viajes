import json

from guia.geocode import geocode_places


class FakeResp:
    def __init__(self, data):
        self._d = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, params, headers, timeout):
        self.calls.append(params["q"])
        if params["q"].startswith("Nowhere"):
            return FakeResp([])
        return FakeResp([{"lat": "-41.1", "lon": "-71.3", "display_name": "Bariloche, Argentina"}])


def test_geocode_uses_cache_and_keeps_misses(tmp_path, capsys):
    cache = tmp_path / "geocache.json"
    s = FakeSession()
    places = [
        {"slug": "bariloche", "nombre": "Bariloche"},
        {"slug": "nowhere", "nombre": "Nowhere"},
    ]
    geocode_places(places, cache, "Argentina", session=s, pause=0)
    assert s.calls == ["Bariloche, Argentina", "Nowhere, Argentina"]
    assert places[0]["lat"] == -41.1 and places[0]["geo_display"].startswith("Bariloche")
    assert places[1]["lat"] is None
    assert "not geocoded: ['Nowhere']" in capsys.readouterr().out
    assert set(json.loads(cache.read_text())) == {"bariloche", "nowhere"}

    # Second run: cache hit, no new requests.
    geocode_places(places, cache, "Argentina", session=s, pause=0)
    assert len(s.calls) == 2


def test_geocode_query_override_and_tramo_midpoint(tmp_path):
    s = FakeSession()
    places = [
        {"slug": "a", "nombre": "A"},
        {"slug": "b", "nombre": "B"},
        {"slug": "ruta-a-b", "nombre": "Ruta A – B", "extremos": ["a", "b"]},
    ]
    geocode_places(
        places, tmp_path / "c.json", "Argentina", session=s, pause=0, queries={"b": "B, Chubut"}
    )
    assert s.calls == ["A, Argentina", "B, Chubut"]
    assert places[2]["lat"] == -41.1 and places[2]["geo_display"].startswith("punto medio")


def test_geocode_manual_fix_skips_lookup(tmp_path):
    s = FakeSession()
    places = [{"slug": "x", "nombre": "X"}]
    geocode_places(
        places, tmp_path / "c.json", "", session=s, pause=0, fixes={"x": {"lat": 1.0, "lon": 2.0}}
    )
    assert s.calls == [] and places[0]["lat"] == 1.0
