from network import WLAN
import machine

wlan = WLAN(mode=WLAN.STA)
wlan.connect('SNSV', auth=(3, 'narodnitrida'), timeout=5000)
while not wlan.isconnected():
    machine.idle()

from machine import Pin
from machine import Timer
from helpers import *
import urequests
import pycom
import time
import utime
pycom.heartbeat(False)

printt('WLAN connection succeeded!')
rtc = machine.RTC()
rtc.ntp_sync("pool.ntp.org")
while not rtc.synced():
    machine.idle()
time.timezone(3600)

# logging to file depends on time being set so import it here
import console

set_pin = Pin(Pin.exp_board.G12, mode=Pin.OUT)
set_pin(True)
en = Pin(Pin.exp_board.G17, mode=Pin.OUT, pull=Pin.PULL_DOWN) # MOSFET gate
rst = Pin(Pin.exp_board.G13, mode=Pin.OUT)

uart = UART(1, baudrate=9600) # init with given baudrate
uart.deinit()


chrono = Timer.Chrono()

while True:
    chrono.start()
    en.value(1)
    rst.value(1)
    uart.init()
    printt('waiting 10s to take measurement')
    machine.idle()
    time.sleep_ms(10000)
    u = uart.any()
    printt('waiting for data {}'.format(str(u)))
    while u < 32:
        u = uart.any()
        pycom.rgbled(0x550000)
    printt('data ready {}'.format(str(uart.any())))
    pycom.rgbled(0x000000)

    frame_read = False

    while frame_read == False:
        while uart.read(1) != b'\x42':
            machine.idle()

        if uart.read(1) == b'\x4D':
            while u < 32:
                u = uart.any()
                pycom.rgbled(0x550000)

            pycom.rgbled(0x000000)
            (cpm25, cpm10, pm25, pm10) = read_frame(b'\x42\x4D' + uart.read(30))
            if (cpm25, cpm10, pm25, pm10) == (-1, -1, -1, -1):
                printt('error reading frame, skipping {}'.format(uart.any()))
            else:
                frame_read = True
                t = utime.localtime(utime.time())
                timestamp = '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(t[0], t[1], t[2], t[3], t[4], t[5])
                printt('{0} cPM25: {1}, cPM10: {2}, PM25: {3}, PM10: {4}'.format(timestamp, cpm25, cpm10, pm25, pm10))

                influx_url = 'http://rpi.local:8086/write?db=mydb'
                data = 'aqi,indoor=1 pm25={},pm10={}'.format(pm25, pm10)
                try:
                    r = urequests.post(influx_url, data=data)
                    pycom.rgbled(0x000055)
                    time.sleep_ms(20)
                    pycom.rgbled(0x000000)

                    en.value(0)
                    uart.deinit()
                    printt('sleeping for 10 mins {}'.format(str(uart.any())))
                    chrono.stop()
                    chrono.reset()
                    machine.idle()
                    time.sleep(600 - chrono.read())
                except OSError as e:
                    printt('network error: {}'.format(e.errno))
                    pass
