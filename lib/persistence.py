import uos
import pycom
import utime
import ujson
from datapoint import DataPoint
from helpers import *

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


def store_datapoint(datapoint):
    sent = False
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

    return sent


def __save_datapoints_to_file(datapoints):
    with open(__filename(), 'a') as data_file:
        for datapoint in datapoints:
            data_file.write(ujson.dumps(datapoint.__dict__))
            data_file.write('\n')
