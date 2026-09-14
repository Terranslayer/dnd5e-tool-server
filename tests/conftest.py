import pytest


class FakeRNG:
    """A scripted RNG for deterministic tests. randint() returns the next
    scripted value and asserts it is within the requested [a, b] range."""

    def __init__(self, values):
        self.values = list(values)
        self.i = 0

    def randint(self, a, b):
        assert self.i < len(self.values), "FakeRNG ran out of scripted values"
        v = self.values[self.i]
        self.i += 1
        assert a <= v <= b, f"scripted value {v} out of range [{a}, {b}]"
        return v


@pytest.fixture
def fake_rng():
    """Returns a factory: fake_rng([3, 5]) -> FakeRNG yielding 3 then 5."""
    return FakeRNG
