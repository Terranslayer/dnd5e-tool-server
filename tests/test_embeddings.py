import math

from dnd5e_engine.embeddings import FakeEmbedder


def test_fake_embedder_dim_and_determinism():
    e = FakeEmbedder(dim=8)
    a = e.embed(["fireball"])
    b = e.embed(["fireball"])
    assert len(a) == 1 and len(a[0]) == 8
    assert a == b  # deterministic


def test_fake_embedder_batch():
    e = FakeEmbedder(dim=8)
    out = e.embed(["a", "b", "c"])
    assert len(out) == 3 and all(len(v) == 8 for v in out)


def test_fake_embedder_normalized():
    e = FakeEmbedder(dim=8)
    v = e.embed(["some text here"])[0]
    norm = math.sqrt(sum(x * x for x in v))
    assert abs(norm - 1.0) < 1e-6


def test_fake_embedder_different_text_differs():
    e = FakeEmbedder(dim=8)
    assert e.embed(["fireball"])[0] != e.embed(["cure wounds"])[0]
