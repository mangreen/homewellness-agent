"""Controller helper: run a state-changing request at most once per idempotency key."""

from collections.abc import Iterator
from contextlib import contextmanager

from homewellness.interfaces import ClaimStore
from homewellness.models.errors import DuplicateRequestError


@contextmanager
def idempotent(claims: ClaimStore, scope: str, key: str) -> Iterator[None]:
    """Claim the key. A second caller gets DuplicateRequestError. A failure frees the key."""
    claim_key = f"idem:{scope}:{key}"
    if not claims.try_claim(claim_key):
        raise DuplicateRequestError("this request was already handled")
    try:
        yield
    except BaseException:
        claims.release(claim_key)  # The client may retry with the same key.
        raise
