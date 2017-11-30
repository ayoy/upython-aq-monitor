import uos
import pycom
import urequests
import utime
from helpers import *

__max_queue_size = const(5)

def cleanup():
    try:
        uos.unlink(__filename())
    except OSError as e:
        print('error while removing data file: {}'.format(e.errno))
        pass


def __queue_size():
    return pycom.nvs_get('queue_size') or 0


def __filename():
    return '{}{}data.txt'.format(uos.getcwd(), uos.sep)


def send_data_adhoc():
    queue_size = __queue_size()
    if queue_size > 0:
        try:
            all_data = None
            with open(__filename(), 'r') as data_file:
                all_data = data_file.read()

            if __send_data(all_data):
                cleanup()
                flash_led(0x008800, 10)
            else:
                flash_led(0x880000, 10)

        except OSError as e:
            print('file access error: {}'.format(e.errno))
            flash_led(0x880000, 5)
            pass
    else:
        # no data to send
        flash_led(0x000088, 1)


def store_data(data):
    queue_size = __queue_size()
    print('queue size: {}'.format(queue_size))
    if queue_size >= __max_queue_size:
        all_data = None
        try:
            with open(__filename(), 'r') as data_file:
                all_data = data_file.read()

            cleanup()
            all_data += data

            if __send_data(all_data):
                flash_led(0x008800, 3)
                pycom.nvs_set('queue_size', 0)
            else:
                flash_led(0x880000, 3)
                with open(__filename(), 'w') as data_file:
                    __save_data_to_file(all_data)
                    pycom.nvs_set('queue_size', queue_size+1)

        except OSError as e:
            print('file access error: {}'.format(e.errno))
            __save_data_to_file(data)
            pass
    else:
        __save_data_to_file(data)
        flash_led(0x888888)
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
            setup_rtc()
            urequests.post(influx_url, data=data)
            wlan.deinit()
            success = True
        except OSError as e:
            print('network error: {}'.format(e.errno))
            number_of_retries -= 1
            pass

    return success
