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

pycom.heartbeat(False)

VERSION = '0.4.1'

# enable expansion board LED while keeping it disabled in deep sleep
led_pin = Pin('P9', mode=Pin.OUT)
try:
    pwm = PWM(0, frequency=5000)
    pwmchannel = pwm.channel(0, pin='P9', duty_cycle=0.99)
except ValueError:
    led_pin(True)
    pass


alive_timer = Timer.Chrono()
alive_timer.start()

def tear_down(timer, pwmchannel, initial_time_remaining):
    timer.stop()
    elapsed_ms = int(timer.read()*1000)
    timer.reset()
    time_remaining = initial_time_remaining - elapsed_ms
    print('sleeping for {}ms'.format(time_remaining))
    pwmchannel.duty_cycle(1)

    deepsleep_pin = Pin('P10', mode=Pin.IN, pull=Pin.PULL_UP)
    machine.pin_deepsleep_wakeup(pins=[deepsleep_pin], mode=machine.WAKEUP_ALL_LOW, enable_pull=True)
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

def th_func(data):
    global lock
    lock.acquire()

    data.voltage = adc.vbatt()

    humid = SHT1X(gnd=Pin.exp_board.G10, sck=Pin.exp_board.G9, data=Pin.exp_board.G8, vcc=Pin.exp_board.G7)
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

datapoint = DataPoint(timestamp=timestamp, pm10=mean_data.pm10, pm25=mean_data.pm25, temperature=measurements.temperature,
                      humidity=measurements.rel_humidity, voltage=measurements.voltage, duration=time_alive, version=VERSION)

persistence.store_datapoint(datapoint)
# sleep for 10 minutes - 5 seconds :)
tear_down(alive_timer, pwmchannel, 595*1000)
