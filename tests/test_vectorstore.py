from dnd5e_engine.vectorstore import VectorStore


def _records():
    return [
        {"id": "a", "text": "alpha", "category": "spells", "index": "a",
         "name": "Alpha", "url": "/a", "source": "SRD 5.1", "license": "CC-BY-4.0", "vector": [1.0, 0.0]},
        {"id": "b", "text": "beta", "category": "spells", "index": "b",
         "name": "Beta", "url": "/b", "source": "SRD 5.1", "license": "CC-BY-4.0", "vector": [0.0, 1.0]},
        {"id": "c", "text": "gamma", "category": "spells", "index": "c",
         "name": "Gamma", "url": "/c", "source": "SRD 5.1", "license": "CC-BY-4.0", "vector": [0.9, 0.1]},
    ]


def test_build_and_search_returns_nearest_first(tmp_path):
    store = VectorStore(tmp_path / "idx")
    store.build(_records())
    rows = store.search([1.0, 0.0], k=2)
    assert len(rows) == 2
    assert rows[0]["index"] == "a"
    assert rows[1]["index"] == "c"
    assert rows[0]["name"] == "Alpha"
    assert "_distance" in rows[0]


def test_build_overwrite(tmp_path):
    store = VectorStore(tmp_path / "idx")
    store.build(_records())
    store.build(_records()[:1])  # overwrite with just 'a'
    rows = store.search([0.0, 1.0], k=5)
    assert {r["index"] for r in rows} == {"a"}


def test_search_limit(tmp_path):
    store = VectorStore(tmp_path / "idx")
    store.build(_records())
    assert len(store.search([0.5, 0.5], k=1)) == 1


def test_add_appends_to_existing(tmp_path):
    store = VectorStore(tmp_path / "idx")
    store.build([{"id": "a", "text": "x", "campaign": "", "vector": [1.0, 0.0]}])
    store.add([{"id": "b", "text": "y", "campaign": "C", "vector": [0.0, 1.0]}])
    rows = store.search([0.0, 1.0], k=5)
    assert {r["id"] for r in rows} == {"a", "b"}


def test_add_creates_table_when_missing(tmp_path):
    store = VectorStore(tmp_path / "idx")
    store.add([{"id": "a", "text": "x", "campaign": "", "vector": [1.0, 0.0]}])
    assert store.exists()
    assert len(store.search([1.0, 0.0], k=5)) == 1


def test_search_where_filters_by_metadata(tmp_path):
    store = VectorStore(tmp_path / "idx")
    store.build([
        {"id": "a", "text": "x", "campaign": "", "vector": [1.0, 0.0]},
        {"id": "b", "text": "y", "campaign": "C1", "vector": [0.9, 0.1]},
        {"id": "c", "text": "z", "campaign": "C2", "vector": [0.8, 0.2]},
    ])
    rows = store.search([1.0, 0.0], k=5, where="campaign = '' OR campaign = 'C1'")
    assert {r["id"] for r in rows} == {"a", "b"}
