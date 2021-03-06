import pycom
import machine
from machine import Timer, Pin, PWM
from helpers import *
import _thread
import utime
import adc
from sht1x import SHT1X
from pms5003 import PMS5003, PMSData
import persistence
from datapoint import DataPoint
from ds3231 import DS3231

pycom.heartbeat(False)

VERSION = '0.7.0'


alive_timer = Timer.Chrono()
alive_timer.start()

def tear_down(timer, initial_time_remaining):
    timer.stop()
    elapsed_ms = int(timer.read()*1000)
    timer.reset()
    time_remaining = initial_time_remaining - elapsed_ms
    print('sleeping for {}ms ({})'.format(time_remaining, ertc.get_time()))

    # deepsleep_pin = Pin('P10', mode=Pin.IN, pull=Pin.PULL_UP)
    # machine.pin_deepsleep_wakeup(pins=[deepsleep_pin], mode=machine.WAKEUP_ALL_LOW, enable_pull=True)
    machine.deepsleep(time_remaining)


######################
#  External RTC
######################
ertc = DS3231(0, (Pin.module.P21, Pin.module.P20))


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
    global ertc

    lock.acquire()
    ertc.get_time(True)

    data.voltage = adc.vbatt()

                    # gnd not used
    humid = SHT1X(gnd=Pin.module.P3, sck=Pin.module.P23, data=Pin.module.P22, vcc=Pin.module.P19)
    humid.wake_up()
    try:
        data.temperature = humid.temperature()
        data.rel_humidity = humid.humidity(data.temperature)
        print('temperature: {}, humidity: {}'.format(data.temperature, data.rel_humidity))
    except SHT1X.AckException:
        print('ACK exception in temperature meter')
        pycom.rgbled(0x443300)
        pass
    finally:
        humid.sleep()

    rtc_synced = pycom.nvs_get('rtc_synced')
    if rtc_synced is None:
        print ('RTC not synced, syncing now')
        wlan = connect_to_WLAN()
        setup_rtc()
        ertc.save_time()
        wlan.deinit()
        pycom.nvs_set('rtc_synced', 1)
    else:
        print('RTC synced: {}'.format(ertc.get_time()))

    lock.release()


_thread.start_new_thread(th_func, (measurements,))
######################

en = Pin('P4', mode=Pin.OUT, pull=Pin.PULL_DOWN) # MOSFET gate
en(True)

aq_sensor = PMS5003(Pin.module.P8, Pin.module.P10, Pin.module.P11, Pin.module.P9)
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

# store datapoints, and if sent, the RTC was synced so update the external RTC
if persistence.store_datapoint(datapoint) is True:
    ertc.save_time()

# sleep for 10 minutes - 2 seconds :)
tear_down(alive_timer,598*1000)
