import pytest

from homewellness.controllers.idempotency import idempotent
from homewellness.models.errors import DuplicateRequestError
from homewellness.stores.memory import InMemoryClaimStore


def should_run_the_block_once_when_the_same_key_is_used_twice():
    claims, runs = InMemoryClaimStore(), []
    with idempotent(claims, "scope", "key-1"):
        runs.append(1)
    with pytest.raises(DuplicateRequestError), idempotent(claims, "scope", "key-1"):
        runs.append(2)
    assert runs == [1]


def should_keep_scopes_independent_when_the_key_is_the_same():
    claims = InMemoryClaimStore()
    with idempotent(claims, "a", "key-1"), idempotent(claims, "b", "key-1"):
        pass


def should_free_the_key_when_the_block_fails():
    claims = InMemoryClaimStore()
    with pytest.raises(RuntimeError), idempotent(claims, "scope", "key-1"):
        raise RuntimeError("boom")
    with idempotent(claims, "scope", "key-1"):
        pass
