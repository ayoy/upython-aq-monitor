import urequests
from helpers import *

def send_to_influx(datapoints):
    data = '\n'.join(d.to_influx() for d in datapoints)

    print('sending data\n{}'.format(data))
    influx_url = 'http://rpi.local:8086/write?db=mydb'
    success = False
    number_of_retries = 3

    while not success and number_of_retries > 0:
        try:
            urequests.post(influx_url, data=data)
            success = True
        except OSError as e:
            print('network error: {}'.format(e.errno))
            number_of_retries -= 1
            pass

    return success
