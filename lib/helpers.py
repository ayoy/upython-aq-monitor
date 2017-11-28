import utime
import time
import machine
import pycom
from network import WLAN

def connect_to_WLAN(ssid, passkey):
    wlan = WLAN(mode=WLAN.STA)
    wlan.connect(ssid, auth=(3, passkey), timeout=5000)
    while not wlan.isconnected():
        utime.sleep_ms(500)
    print('WLAN connection succeeded!')


def setup_rtc():
    rtc = machine.RTC()
    rtc.ntp_sync("pool.ntp.org")
    while not rtc.synced():
        utime.sleep_ms(500)
    time.timezone(3600)
