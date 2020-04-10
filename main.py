import pycom
import machine
from machine import Timer, Pin, PWM
from helpers import *
import _thread
import utime
import adc
from dht import DHT, DHTResult
from pms5003 import PMS5003, PMSData
from persistence import Counter
from datapoint import DataPoint
import lora_node

class AsyncMeasurements:
    def __init__(self, voltage=None, temperature=-1, rel_humidity=-1):
        self.voltage = voltage
        self.temperature = temperature
        self.rel_humidity = rel_humidity


def get_battery_level(pin):
    # set to false to enable battery voltage measurement
    pin.hold(False)
    pin(False)
    voltage = adc.vbatt()
    # set to true to enable temperature/rel.humidity measurement
    pin(True)
    pin.hold(True)
    return voltage


def tear_down(timer, initial_time_remaining):
    timer.stop()
    elapsed_ms = int(timer.read()*1000)
    timer.reset()
    time_remaining = initial_time_remaining - elapsed_ms
    print('sleeping for {}ms'.format(time_remaining))
    machine.deepsleep(time_remaining)


#############################################


pycom.heartbeat(False)

if machine.reset_cause() not in [machine.DEEPSLEEP_RESET, machine.SOFT_RESET, machine.WDT_RESET]:
    flash_led(0x008800, n=5)
    print('init-sleeping for {}ms'.format(600000))
    machine.deepsleep(600000)

VERSION = '1.0.1'

adc_dht_en = Pin('P3', mode=Pin.OUT, pull=Pin.PULL_DOWN) # MOSFET gate

voltage = get_battery_level(adc_dht_en)
print("battery voltage: {}mv".format(voltage))

if voltage < 3700:
    print('Battery voltage is too low, entering deep sleep')
    machine.deepsleep()

counter = Counter(6)
print("COUNTER: {}; reading AQ: {}".format(counter.value, counter.value == 0))

alive_timer = Timer.Chrono()
alive_timer.start()

######################
#  T/RH Measurement
######################
measurements = AsyncMeasurements()

lock = _thread.allocate_lock()

def th_func(en_pin, data, voltage):
    global lock

    lock.acquire()

    data.voltage = voltage

    dht_pin = Pin('P23', mode=Pin.OPEN_DRAIN)
    dht = DHT(dht_pin, sensor=1)
    result = dht.read()
    data.temperature = result.temperature
    data.rel_humidity = result.humidity
    print('temperature: {}, humidity: {} (voltage: {})'.format(data.temperature, data.rel_humidity, data.voltage))
    lock.release()


######################

# measure Air Quality only if counter is 0
if counter.value == 0:
    _thread.start_new_thread(th_func, (adc_dht_en, measurements, voltage))

    en = Pin('P4', mode=Pin.OUT, pull=Pin.PULL_DOWN) # MOSFET gate
    en(True)

    aq_sensor = PMS5003(Pin.module.P8, Pin.module.P9, Pin.module.P10, Pin.module.P11)
    aq_sensor.wake_up()
    frames = aq_sensor.read_frames(5)
    aq_sensor.idle()

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


    pms_data = PMSData(cpm25/len(frames), cpm10/len(frames), \
                        pm25/len(frames), pm10/len(frames))
    counter.store_aq(pms_data.pm10, pms_data.pm25)
else:
    th_func(adc_dht_en, measurements, voltage)
    pms_data = PMSData(0, 0, 0, 0)

if lock.locked():
    print('waiting for humidity/temp/voltage reading')
    while lock.locked():
        machine.idle()

time_alive = alive_timer.read_ms()
timestamp = utime.time()

print('cPM25: {}, cPM10: {}, PM25: {}, PM10: {}, temp: {}, rh: {}, Vbat: {}, time: {}' \
        .format(pms_data.cpm25, pms_data.cpm10, pms_data.pm25, pms_data.pm10, \
         measurements.temperature, measurements.rel_humidity, measurements.voltage, time_alive))

datapoint = DataPoint(timestamp=timestamp, pm10=pms_data.pm10, pm25=pms_data.pm25, temperature=measurements.temperature,
                      humidity=measurements.rel_humidity, voltage=measurements.voltage, duration=time_alive, version=VERSION)

def send_data(datapoint):
    lock.acquire()
    send_aq = counter.value is 0
    if lora_node.send_bytes(datapoint.to_bytes(send_aq)):
        flash_led(0x888888)
    else:
        flash_led(0x880000)
    lock.release()

_thread.start_new_thread(send_data, (datapoint,))

import epd1in54b
import monaco12
import monaco16_pms as monaco16
import menlo24

mosi = Pin('P22')
clk = Pin('P21')
cs = Pin('P20')
dc = Pin('P19')
reset = Pin('P18')
busy = Pin('P17')

epd = epd1in54b.EPD(reset, dc, busy, cs, clk, mosi)
epd.init()

# initialize the frame buffer
fb_size = int(epd.width * epd.height / 8)
frame_black = bytearray(fb_size)
frame_red = bytearray(fb_size)

(last_pm10, last_pm25) = counter.last_aq()

pm10_label = "PM10"
pm25_label = "PM2.5"
pm10_value = "{}\x80".format(last_pm10)
pm25_value = "{}\x80".format(last_pm25)
t_label = "Temp."
t_value = "%.1f\x81\x82" % datapoint.temperature
rh_label = "Humidity"
rh_value = "%d%%" % datapoint.humidity
battery_value = "battery: %dmV" % datapoint.voltage
epd.clear_frame(frame_black, frame_red)

epd.display_string_at(frame_black,
                      epd.width//4 - len(pm10_label)*monaco16.width//2, 25,
                      pm10_label, monaco16,
                      epd1in54b.COLORED)
epd.display_string_at(frame_black,
                      epd.width//4 - len(pm10_value)*menlo24.width//2, 45,
                      pm10_value, menlo24,
                      epd1in54b.COLORED)

epd.display_string_at(frame_black,
                      epd.width//4*3 - len(pm25_label)*monaco16.width//2, 25,
                      pm25_label, monaco16,
                      epd1in54b.COLORED)
epd.display_string_at(frame_black,
                      epd.width//4*3 - len(pm25_value)*menlo24.width//2, 45,
                      pm25_value, menlo24,
                      epd1in54b.COLORED)

epd.display_string_at(frame_black,
                      epd.width//4 - len(t_label)*monaco16.width//2, 115,
                      t_label, monaco16,
                      epd1in54b.COLORED)
epd.display_string_at(frame_black,
                      epd.width//4 - len(t_value)*menlo24.width//2, 135,
                      t_value, menlo24,
                      epd1in54b.COLORED)

epd.display_string_at(frame_black,
                      epd.width//4*3 - len(rh_label)*monaco16.width//2, 115,
                      rh_label, monaco16,
                      epd1in54b.COLORED)
epd.display_string_at(frame_black,
                      epd.width//4*3 - len(rh_value)*menlo24.width//2, 135,
                      rh_value, menlo24,
                      epd1in54b.COLORED)

epd.display_string_at(frame_black, epd.width - 10 - len(battery_value)*monaco12.width, 185, battery_value, monaco12, epd1in54b.COLORED)
epd.draw_vertical_line(frame_black, epd.width//2, 0, 180, epd1in54b.COLORED)
epd.draw_horizontal_line(frame_black, 0, 90, epd.width, epd1in54b.COLORED)
epd.draw_horizontal_line(frame_black, 0, 180, epd.width, epd1in54b.COLORED)
epd.display_frame(frame_black, frame_red)

if lock.locked():
    print('waiting for LoRaWAN data transfer')
    while lock.locked():
        machine.idle()

counter.increment()
# sleep for 60 minutes + 2 seconds :)
tear_down(alive_timer, int(3600 / counter.size + 2) * 1000)
