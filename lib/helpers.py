import utime
import time
import machine
import pycom
from network import WLAN
from keychain import *

def connect_to_WLAN():
    wlan = WLAN(mode=WLAN.STA)
    if not wlan.isconnected():
        wlan = __connect_to_WLAN(wlan, WLAN_SSID, WLAN_PASSKEY)
    return wlan


def __connect_to_WLAN(wlan, ssid, passkey):
    wlan.connect(ssid, auth=(WLAN.WPA2, passkey), timeout=10000)
    while not wlan.isconnected():
        utime.sleep_ms(500)
    print('WLAN connection succeeded!')
    return wlan


def setup_rtc():
    rtc = machine.RTC()
    rtc.ntp_sync("pool.ntp.org")
    while not rtc.synced():
        utime.sleep_ms(500)
    time.timezone(3600)


def flash_led(color, n=1):
    for _ in range(n):
        pycom.rgbled(color)
        utime.sleep_ms(20)
        pycom.rgbled(0x000000)
        if n != 1:
            utime.sleep_ms(200)
