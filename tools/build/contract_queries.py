"""Pure queries shared by generated contract validators."""

from __future__ import annotations

import re
import struct


def _blocks(text: str, kind: str) -> tuple[str, ...]:
    return tuple(re.findall(rf"(?ms)^{re.escape(kind)} \{{.*?^\}}", text))


def piece_blocks(text: str) -> tuple[str, ...]:
    return _blocks(text, "Piece")


def locator_blocks(text: str) -> tuple[str, ...]:
    return _blocks(text, "Locator")


def locator_position(text: str, name: str) -> tuple[float, float, float]:
    match = re.search(
        rf'(?ms)Locator \{{\s+Name: "{re.escape(name)}".*?Position: \( &([0-9a-f]+)\s+&([0-9a-f]+)\s+&([0-9a-f]+) \)',
        text,
    )
    if match is None:
        raise AssertionError(f"missing locator {name}")
    return tuple(
        struct.unpack(">f", bytes.fromhex(value))[0] for value in match.groups()
    )


def locator_y(text: str, name: str) -> float:
    return locator_position(text, name)[2]
