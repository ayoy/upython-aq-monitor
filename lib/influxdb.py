import uos
import pycom
import urequests
import utime
from helpers import connect_to_WLAN, setup_rtc

__max_queue_size = const(5)

def cleanup():
    uos.unlink(__filename())

def __queue_size():
    return pycom.nvs_get('queue_size') or 0

def __filename():
    return '{}{}data.txt'.format(uos.getcwd(), uos.sep)

def store_data(data):
    queue_size = __queue_size()
    print('queue size: {}'.format(queue_size))
    if queue_size >= __max_queue_size:
        all_data = None
        try:
            with open(__filename(), 'r') as data_file:
                all_data = data_file.read()
            uos.unlink(__filename())
            all_data += data
            __send_data(all_data)
        except OSError as e:
            print('file access error: {}'.format(e.errno))
            __save_data_to_file(data)
            pass
        pycom.nvs_set('queue_size', 0)
    else:
        __save_data_to_file(data)
        pycom.nvs_set('queue_size', queue_size+1)

def __save_data_to_file(data):
    with open(__filename(), 'a') as data_file:
        data_file.write(data)
        data_file.write('\n')


def __send_data(data):
    print('sending data\n{}'.format(data))
    influx_url = 'http://rpi.local:8086/write?db=mydb'
    success = False
    number_of_retries = 3

    while not success and number_of_retries > 0:
        try:
            wlan = connect_to_WLAN('SSID', 'passkey')
            urequests.post(influx_url, data=data)
            setup_rtc()
            wlan.deinit()
            pycom.rgbled(0x008800)
            utime.sleep_ms(20)
            pycom.rgbled(0x000000)

            success = True
        except OSError as e:
            print('network error: {}'.format(e.errno))
            number_of_retries -= 1
            pass
