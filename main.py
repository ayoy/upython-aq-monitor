import pycom
import machine
from machine import Timer, WDT, Pin
from helpers import *
import _thread
from _thread import start_new_thread, allocate_lock
import utime
import adc
from sht1x import SHT1X
from pms5003 import PMS5003, PMSData
import influxdb

alive_timer = Timer.Chrono()
alive_timer.start()

watchdog_timer = WDT(timeout=30000)

pycom.heartbeat(False)

VERSION = '0.2.0'


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
        print('temperature: {}, humidity: {}'.format(data.temperature, data.rel_humidity))
    except SHT1X.AckException:
        print('ACK exception in temperature meter')
        pass
    finally:
        humid.sleep()

    rtc_synced = pycom.nvs_get('rtc_synced')
    if rtc_synced is None:
        print ('RTC not synced, syncing now')
        wlan = connect_to_WLAN('SSID', 'passkey')
        setup_rtc()
        wlan.deinit()
        pycom.nvs_set('rtc_synced', 1)

    lock.release()


_thread.start_new_thread(th_func, (measurements,))
######################

en = Pin(Pin.exp_board.G6, mode=Pin.OUT, pull=Pin.PULL_DOWN) # MOSFET gate
en(True)

aq_sensor = PMS5003(Pin.exp_board.G22, Pin.exp_board.G14, Pin.exp_board.G15, Pin.exp_board.G13)
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

data = 'aqi,indoor=1,version={} pm25={},pm10={},temperature={},humidity={},voltage={},duration={} {}000000000' \
    .format(VERSION, mean_data.pm25, mean_data.pm10, measurements.temperature, measurements.rel_humidity, \
     measurements.voltage, time_alive, timestamp)

influxdb.store_data(data)
alive_timer.stop()
elapsed_ms = int(alive_timer.read()*1000)
alive_timer.reset()
print('sleeping for 10 mins')
machine.deepsleep(600*1000 - elapsed_ms)
