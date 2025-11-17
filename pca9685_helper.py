#!/usr/bin/env python3
"""Shared PCA9685 helper for motor and servo drivers.

The original Adeept examples hard-coded the Robot HAT's PWM address to 0x5f.
However, depending on how the board is assembled (and on replacement hats),
the PCA9685 may still live at the default 0x40 address.  Instantiating
multiple PCA9685 objects with the wrong address causes the servos and
motors to remain silent.

This helper centralises the discovery of the chip and returns a single
configured instance that can be reused safely across the project.
"""
from __future__ import annotations

import os
import threading
from typing import Iterable, Optional, Sequence, Tuple

from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

# Try the Adeept firmware default first (0x5f) and fall back to the PCA9685
# hardware default (0x40).  The list can be overridden with the
# ADEEPT_PCA9685_ADDRS environment variable which accepts comma separated
# hexadecimal addresses (e.g. "0x5f,0x40,0x41").
_DEFAULT_ADDRS: Sequence[int] = (
    0x5F,
    0x40,
)

_i2c_bus: Optional[busio.I2C] = None
_pca9685: Optional[PCA9685] = None
_active_address: Optional[int] = None
_lock = threading.Lock()


def _parse_addr_env(env_value: Optional[str]) -> Sequence[int]:
    if not env_value:
        return _DEFAULT_ADDRS
    parsed = []
    for item in env_value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            parsed.append(int(item, 16))
        except ValueError:
            raise ValueError(
                "Unable to parse ADEEPT_PCA9685_ADDRS entry %r" % item
            )
    return tuple(parsed) if parsed else _DEFAULT_ADDRS


def _ensure_bus() -> busio.I2C:
    global _i2c_bus
    if _i2c_bus is None:
        _i2c_bus = busio.I2C(SCL, SDA)
    return _i2c_bus


def _try_addresses(addresses: Iterable[int], frequency: int) -> Tuple[PCA9685, int]:
    bus = _ensure_bus()
    last_exc: Optional[Exception] = None
    for addr in addresses:
        try:
            controller = PCA9685(bus, address=addr)
            controller.frequency = frequency
            return controller, addr
        except Exception as exc:  # pragma: no cover - hardware dependent
            last_exc = exc
    raise RuntimeError(
        "Unable to communicate with PCA9685 at addresses: %s"
        % ", ".join("0x%02X" % addr for addr in addresses)
    ) from last_exc


def get_pca9685(frequency: int = 50,
                addresses: Optional[Sequence[int]] = None) -> PCA9685:
    """Return a configured PCA9685 instance shared across the project."""
    global _pca9685, _active_address
    with _lock:
        if _pca9685 is not None:
            # Ensure any caller-requested frequency is honoured.
            if frequency and _pca9685.frequency != frequency:
                _pca9685.frequency = frequency
            return _pca9685

        address_list = addresses or _parse_addr_env(
            os.environ.get("ADEEPT_PCA9685_ADDRS")
        )
        controller, addr = _try_addresses(address_list, frequency)
        _pca9685 = controller
        _active_address = addr
        return _pca9685


def get_active_address() -> Optional[int]:
    """Expose the detected PCA9685 address for diagnostics."""
    return _active_address


def deinit():
    """Release the PCA9685 instance (mainly for unit tests)."""
    global _pca9685, _active_address
    with _lock:
        if _pca9685 is not None:
            _pca9685.deinit()
        _pca9685 = None
        _active_address = None
