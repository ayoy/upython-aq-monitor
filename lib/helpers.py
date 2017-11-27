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


def sum_of_bytes(bytes):
    s = 0
    for b in bytes:
        s += b
    return s

def wait_for_data(uart, byte_count):
    def idle_timer(alarm):
        pycom.rgbled(0x550000)

    alarm = None
    u = uart.any()
    if u < byte_count:
        alarm = machine.Timer.Alarm(idle_timer, 3)
        print('waiting for data {}'.format(str(u)))
    while u < byte_count:
        u = uart.any()
        # 32*8*1000/9600 (32 bytes @9600kbps)
        # but let's assume byte is 10 bits to skip complex math
        machine.Timer.sleep_us(byte_count)
    try:
        alarm.cancel()
    except AttributeError:
        pass
    pycom.rgbled(0x000000)
    print('data ready {}'.format(str(uart.any())))
