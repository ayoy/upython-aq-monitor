import machine
import pycom
import persistence
from network import Bluetooth, WLAN
from machine import WDT

bluetooth = Bluetooth()
bluetooth.deinit()
wlan = WLAN(mode=WLAN.STA)
wlan.deinit()

watchdog_timer = None

if machine.reset_cause() not in [machine.DEEPSLEEP_RESET, machine.SOFT_RESET, machine.WDT_RESET]:
    pycom.nvs_erase_all()
    persistence.cleanup()
# else:
    # watchdog_timer = WDT(timeout=30000)


machine.main('main.py')
