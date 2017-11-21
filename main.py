from helpers import *
import machine
from machine import Timer
import pycom
import _thread
from _thread import start_new_thread, allocate_lock

pycom.heartbeat(False)

VERSION = '0.1.4'

alive_timer = Timer.Chrono()
alive_timer.start()

from machine import Pin
import urequests
import time
import utime
import adc
from sht1x import SHT1X
from pmsdata import PMSData


# logging to file depends on time being set so import it here
# import console

######################
#  T/RH Measurement
######################
class AsyncMeasurements:
    def __init__(self, voltage=None, temperature=-1, rel_humidity=-1):
        self.voltage = voltage
        self.temperature = temperature
        self.rel_humidity = rel_humidity

measurements = AsyncMeasurements()

lock = _thread.allocate_lock()

def th_func(data):
    global lock
    lock.acquire()

    data.voltage = adc.ADCloopMeanStdDev()

    humid = SHT1X(gnd=Pin.exp_board.G7, sck=Pin.exp_board.G8, data=Pin.exp_board.G9, vcc=Pin.exp_board.G10)
    humid.wake_up()
    try:
        data.temperature = humid.temperature()
        data.rel_humidity = humid.humidity(data.temperature)
        printt('temperature: {}, humidity: {}'.format(data.temperature, data.rel_humidity))
    except SHT1X.AckException:
        printt('ACK exception in temperature meter')
        pass
    finally:
        humid.sleep()
        connect_to_WLAN()
        setup_rtc()
        lock.release()


_thread.start_new_thread(th_func, (measurements,))
######################



set_pin = Pin(Pin.exp_board.G12, mode=Pin.OUT)
set_pin(True)
en = Pin(Pin.exp_board.G22, mode=Pin.OUT, pull=Pin.PULL_DOWN) # MOSFET gate
rst = Pin(Pin.exp_board.G13, mode=Pin.OUT)

uart = UART(1, baudrate=9600, pins=(Pin.exp_board.G14, Pin.exp_board.G15)) # init with given baudrate
uart.deinit()

en.value(1)
rst.value(1)

uart.init(pins=(Pin.exp_board.G14, Pin.exp_board.G15))

valid_frames_count = 5
frames = []

# skip first frame because initial reading tends to be skewed
odd_frame = True
while len(frames) < valid_frames_count:
    wait_for_data(uart, 32)

    while uart.read(1) != b'\x42':
        machine.idle()

    if uart.read(1) == b'\x4D':
        wait_for_data(uart, 30)

        if odd_frame:
            uart.readall()
        else:
            try:
                data = PMSData.from_bytes(b'\x42\x4D' + uart.read(30))
                frames.append(data)
            except ValueError as e:
                printt('error reading frame: {}'.format(e.message))
                pass
        odd_frame = not odd_frame

uart.deinit()
en.value(0)

cpm25 = 0
cpm10 = 0
pm25 = 0
pm10 = 0

for data in frames:
    cpm25 += data.cpm25
    cpm10 += data.cpm10
    pm25 += data.pm25
    pm10 += data.pm10


mean_data = PMSData(cpm25/valid_frames_count, cpm10/valid_frames_count, \
                    pm25/valid_frames_count, pm10/valid_frames_count)

if lock.locked():
    printt('waiting for humidity/temp/voltage reading')
    while lock.locked():
        machine.idle()

time_alive = alive_timer.read_ms()

printt('cPM25: {}, cPM10: {}, PM25: {}, PM10: {}, temp: {}, rh: {}, Vbat: {}, time: {}' \
        .format(mean_data.cpm25, mean_data.cpm10, mean_data.pm25, mean_data.pm10, \
         measurements.temperature, measurements.rel_humidity, measurements.voltage, time_alive))


influx_url = 'http://rpi.local:8086/write?db=mydb'
data = 'aqi,indoor=1,version={} pm25={},pm10={},temperature={},humidity={},voltage={},duration={}' \
    .format(VERSION, mean_data.pm25, mean_data.pm10, measurements.temperature, measurements.rel_humidity, \
     measurements.voltage, time_alive)

success = False
number_of_retries = 3

while not success and number_of_retries > 0:
    try:
        urequests.post(influx_url, data=data)
        pycom.rgbled(0x008800)
        time.sleep_ms(20)
        pycom.rgbled(0x000000)

        success = True
    except OSError as e:
        printt('network error: {}'.format(e.errno))
        number_of_retries -= 1
        pass

printt('sleeping for 10 mins {}'.format(str(uart.any())))
alive_timer.stop()
elapsed_ms = int(alive_timer.read()*1000)
alive_timer.reset()
machine.deepsleep(600*1000 - elapsed_ms)
# time.sleep(600 - alive_timer.read())
# machine.deepsleep(5*1000)
# time.sleep(5)
