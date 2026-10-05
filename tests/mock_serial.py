"""Helpers for serial mocks used by CD48 unit tests."""

from __future__ import annotations

from unittest.mock import Mock


def arm_line_reader(mock_serial: Mock) -> None:
    """Serve ``read()`` from the payload stubbed on ``read_all()``.

    Production code reads until a line terminator. Tests historically stubbed
    only ``read_all``; both paths must return that same framed payload.
    """

    def _read(n: int = 1) -> bytes:
        del n
        data = mock_serial.read_all.return_value
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        return b""

    mock_serial.read.side_effect = _read
