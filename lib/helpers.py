import utime
import time
import machine
import pycom
from network import WLAN

# uart.write(b'\x42\x4D\x00\x00\xE4\x01\x73') # sleep
# uart.write(b'\x42\x4D\x01\x00\xE4\x01\x74') # wake up
# uart.write(b'\x42\x4D\x00\x00\xE1\x01\x70') # passive
# uart.write(b'\x42\x4D\x00\x00\xE2\x01\x71') # read data

def connect_to_WLAN():
    wlan = WLAN(mode=WLAN.STA)
    wlan.connect('SNSV', auth=(3, 'narodnitrida'), timeout=5000)
    while not wlan.isconnected():
        utime.sleep_ms(500)
    printt('WLAN connection succeeded!')


def setup_rtc():
    rtc = machine.RTC()
    rtc.ntp_sync("pool.ntp.org")
    while not rtc.synced():
        utime.sleep_ms(500)
    time.timezone(3600)


def printt(objects):
    print(objects)
    # t = utime.localtime(utime.time())
    # timestamp = '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(t[0], t[1], t[2], t[3], t[4], t[5])
    # print('{} {}'.format(timestamp, objects))


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
        printt('waiting for data {}'.format(str(u)))
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
    printt('data ready {}'.format(str(uart.any())))
