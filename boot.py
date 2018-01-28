import machine
import pycom
import persistence
from network import Bluetooth, WLAN
from machine import WDT
from helpers import *

pycom.wifi_on_boot(False)

########################################
## Handle wake by button to enter debug mode
########################################

if machine.wake_reason()[0] is machine.PIN_WAKE:
    print('PIN WAKE')
    connect_to_WLAN()
else:
    watchdog_timer = None

    if machine.reset_cause() not in [machine.DEEPSLEEP_RESET, machine.SOFT_RESET, machine.WDT_RESET]:
        print('hard reset, erasing NVS')
        pycom.nvs_erase_all()
        # persistence.cleanup()
    else:
        print('soft/deepsleep reset, enabling watchdog timer')
        watchdog_timer = WDT(timeout=30000)

    machine.main('main.py')
