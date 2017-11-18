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
import adc
from pmsdata import PMSData
pycom.heartbeat(False)

printt('WLAN connection succeeded!')
rtc = machine.RTC()
rtc.ntp_sync("pool.ntp.org")
while not rtc.synced():
    machine.idle()
time.timezone(3600)

# logging to file depends on time being set so import it here
# import console

set_pin = Pin(Pin.exp_board.G12, mode=Pin.OUT)
set_pin(True)
en = Pin(Pin.exp_board.G22, mode=Pin.OUT, pull=Pin.PULL_DOWN) # MOSFET gate
rst = Pin(Pin.exp_board.G13, mode=Pin.OUT)

uart = UART(1, baudrate=9600, pins=(Pin.exp_board.G14, Pin.exp_board.G15)) # init with given baudrate
uart.deinit()


chrono = Timer.Chrono()

chrono.start()
en.value(1)
rst.value(1)

uart.init(pins=(Pin.exp_board.G14, Pin.exp_board.G15))

valid_frames_count = 10
frames_to_skip_count = 1
frames = []


while len(frames) < valid_frames_count + frames_to_skip_count:
    wait_for_data(uart, 32)

    while uart.read(1) != b'\x42':
        machine.idle()

    if uart.read(1) == b'\x4D':
        wait_for_data(uart, 30)

        try:
            data = PMSData.from_bytes(b'\x42\x4D' + uart.read(30))
            frames.append(data)
            # printt('cPM25: {}, cPM10: {}, PM25: {}, PM10: {}' \
            #     .format(data.cpm25, data.cpm10, data.pm25, data.pm10))
        except ValueError as e:
            printt('error reading frame: {}'.format(e.message))
            pass


cpm25 = 0
cpm10 = 0
pm25 = 0
pm10 = 0

# skip some first frames because initial readings tend to be skewed
for data in frames[frames_to_skip_count:]:
    cpm25 += data.cpm25
    cpm10 += data.cpm10
    pm25 += data.pm25
    pm10 += data.pm10


mean_data = PMSData(cpm25/valid_frames_count, cpm10/valid_frames_count, \
                    pm25/valid_frames_count, pm10/valid_frames_count)

voltage = adc.ADCloopMeanStdDev()
printt('cPM25: {}, cPM10: {}, PM25: {}, PM10: {}' \
        .format(mean_data.cpm25, mean_data.cpm10, mean_data.pm25, mean_data.pm10))

influx_url = 'http://rpi.local:8086/write?db=mydb'
data = 'aqi,indoor=1 pm25={},pm10={},voltage={}'.format(mean_data.pm25, mean_data.pm10, voltage)

success = False
number_of_retries = 3

while not success and number_of_retries > 0:
    try:
        urequests.post(influx_url, data=data)
        pycom.rgbled(0x008800)
        time.sleep_ms(20)
        pycom.rgbled(0x000000)

        en.value(0)
        uart.deinit()

        success = True
    except OSError as e:
        printt('network error: {}'.format(e.errno))
        number_of_retries -= 1
        pass

printt('sleeping for 10 mins {}'.format(str(uart.any())))
chrono.stop()
elapsed_ms = int(chrono.read()*1000)
chrono.reset()
machine.deepsleep(600*1000 - elapsed_ms)
# time.sleep(600 - chrono.read())
# machine.deepsleep(5*1000)
# time.sleep(5)
