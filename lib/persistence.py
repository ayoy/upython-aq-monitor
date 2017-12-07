import uos
import pycom
import urequests
import utime
import ujson
from datapoint import DataPoint
from helpers import *
from influxdb import send_to_influx
from thingspeak import send_to_thingspeak

__max_queue_size = const(5)

def cleanup():
    try:
        uos.unlink(__filename())
        pycom.nvs_set('queue_size', 0)
    except OSError as e:
        print('error while removing data file: {}'.format(e.errno))
        pass


def __queue_size():
    return pycom.nvs_get('queue_size') or 0


def __filename():
    return '{}{}datapoints.txt'.format(uos.getcwd(), uos.sep)


def send_datapoints_adhoc():
    queue_size = __queue_size()
    if queue_size > 0:
        try:
            datapoints = []
            with open(__filename(), 'r') as data_file:
                try:
                    json_dict = ujson.loads(data_file.readline().rstrip())
                    datapoints.append(DataPoint(**json_dict))
                except ValueError:
                    pass


            if __send_data(datapoints):
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


def store_datapoint(datapoint):
    queue_size = __queue_size()
    print('queue size: {}'.format(queue_size))
    if queue_size >= __max_queue_size:
        datapoints = []
        try:
            with open(__filename(), 'r') as data_file:
                for line in data_file:
                    try:
                        json_dict = ujson.loads(line.rstrip())
                        datapoints.append(DataPoint(**json_dict))
                    except ValueError as e:
                        print('error while reading data from flash: {}'.format(e.errno))
                        pass

            datapoints.append(datapoint)

            if __send_datapoints(datapoints):
                flash_led(0x008800, 3)
                cleanup()
            else:
                flash_led(0x880000, 3)
                with open(__filename(), 'w') as data_file:
                    __save_datapoints_to_file([datapoints])
                    pycom.nvs_set('queue_size', queue_size+1)

        except OSError as e:
            print('file access error: {}'.format(e.errno))
            cleanup()
            __save_datapoints_to_file([datapoint])
            flash_led(0x888888)
            pycom.nvs_set('queue_size', 1)
            pass
    else:
        __save_datapoints_to_file([datapoint])
        flash_led(0x888888)
        pycom.nvs_set('queue_size', queue_size+1)


def __save_datapoints_to_file(datapoints):
    with open(__filename(), 'a') as data_file:
        for datapoint in datapoints:
            data_file.write(ujson.dumps(datapoint.__dict__))
            data_file.write('\n')


def __send_datapoints(datapoints):
    wlan = connect_to_WLAN()
    setup_rtc()
    success = send_to_thingspeak(datapoints) and send_to_influx(datapoints)
    wlan.deinit()
    return success
