import pycom
import machine
from machine import Timer, Pin, PWM
from helpers import *
import _thread
import utime
import adc
from dht import DHT, DHTResult
from pms5003 import PMS5003, PMSData
import persistence
from datapoint import DataPoint
import lora_node

pycom.heartbeat(False)

VERSION = '1.0.0'

adc_dht_en = Pin('P3', mode=Pin.OUT, pull=Pin.PULL_DOWN) # MOSFET gate

# set to false to enable battery voltage measurement
adc_dht_en(False)
voltage = adc.vbatt()
print("battery voltage: {}mv".format(voltage))

# set to true to enable temperature/humidity measurement
adc_dht_en(True)
adc_dht_en.hold(True)

if voltage < 3700:
    print('Battery voltage is too low, entering deep sleep')
    machine.deepsleep()


alive_timer = Timer.Chrono()
alive_timer.start()

def tear_down(timer, initial_time_remaining):
    timer.stop()
    elapsed_ms = int(timer.read()*1000)
    timer.reset()
    time_remaining = initial_time_remaining - elapsed_ms
    print('sleeping for {}ms'.format(time_remaining))
    machine.deepsleep(time_remaining)


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

def th_func(en_pin, data, voltage):
    global lock

    lock.acquire()

    data.voltage = voltage

    dht_pin = Pin('P23', mode=Pin.OPEN_DRAIN)
    dht = DHT(dht_pin, sensor=1)
    result = dht.read()
    data.temperature = result.temperature
    data.rel_humidity = result.humidity
    print('temperature: {}, humidity: {}'.format(data.temperature, data.rel_humidity))
    lock.release()


_thread.start_new_thread(th_func, (adc_dht_en, measurements,voltage))
######################

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


mean_data = PMSData(cpm25/len(frames), cpm10/len(frames), \
                    pm25/len(frames), pm10/len(frames))

if lock.locked():
    print('waiting for humidity/temp/voltage reading')
    while lock.locked():
        machine.idle()

time_alive = alive_timer.read_ms()
timestamp = utime.time()

print('cPM25: {}, cPM10: {}, PM25: {}, PM10: {}, temp: {}, rh: {}, Vbat: {}, time: {}' \
        .format(mean_data.cpm25, mean_data.cpm10, mean_data.pm25, mean_data.pm10, \
         measurements.temperature, measurements.rel_humidity, measurements.voltage, time_alive))

datapoint = DataPoint(timestamp=timestamp, pm10=mean_data.pm10, pm25=mean_data.pm25, temperature=measurements.temperature,
                      humidity=measurements.rel_humidity, voltage=measurements.voltage, duration=time_alive, version=VERSION)

# if lora_node.send_bytes(datapoint.to_bytes()):
#     flash_led(0x888888)
# else:
#     flash_led(0x880000)

# sleep for 30 minutes + 2 seconds :)
# tear_down(alive_timer, 1802*1000)
