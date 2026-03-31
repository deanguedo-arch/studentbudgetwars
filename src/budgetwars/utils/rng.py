from __future__ import annotations

import hashlib
import random


def seeded_rng(seed: int | None) -> random.Random:
    return random.Random(seed)


def derive_seed(*parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)
