import machine
import pycom
import influxdb
from network import Bluetooth, WLAN
from machine import WDT

bluetooth = Bluetooth()
bluetooth.deinit()
wlan = WLAN(mode=WLAN.STA)
wlan.deinit()

if machine.reset_cause() not in [machine.DEEPSLEEP_RESET, machine.SOFT_RESET, machine.WDT_RESET]:
    pycom.nvs_erase_all()
    influxdb.cleanup()
else:
    watchdog_timer = WDT(timeout=30000)


machine.main('main.py')
