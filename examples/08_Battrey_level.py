import os
import time
import board
import adafruit_ads7830.ads7830 as ADC
from adafruit_ads7830.analog_in import AnalogIn

i2c = board.I2C()

def _address_list():
    env_value = os.environ.get("ADEEPT_BAT_ADDR")
    if env_value:
        try:
            return [int(env_value, 16)]
        except ValueError:
            print(
                f"[ADS7830] Invalid ADEEPT_BAT_ADDR {env_value!r}, "
                "falling back to defaults."
            )
    return [0x48, 0x49, 0x4A, 0x4B]

def detect_ads7830(possible_addresses=None):
    """Try to create an ADS7830 object across common address pins."""
    possible_addresses = possible_addresses or _address_list()
    last_error = None
    for addr in possible_addresses:
        try:
            adc = ADC.ADS7830(i2c, addr)
            print(f"[ADS7830] Detected on address 0x{addr:02X}")
            return adc
        except Exception as exc:
            last_error = exc
            time.sleep(0.05)
    raise RuntimeError(
        "No ADS7830 detected. Check wiring or set ADEEPT_BAT_ADDR."
    ) from last_error

def build_channels(adc):
    """Return AnalogIn instances for all 8 channels."""
    return [AnalogIn(adc, ch) for ch in range(8)]

adc = detect_ads7830()
channels = build_channels(adc)

if __name__ == "__main__":

    while True:
        chan0 = channels[0]
        print(f"battery level = {chan0.value/65535*8.4:.2f} V")

        time.sleep(0.5)

