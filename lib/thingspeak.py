from mqtt import MQTTClient
import machine
import binascii
from datapoint import DataPoint
from helpers import *
from keychain import *

def send_to_thingspeak(datapoints):
    mean_data = DataPoint.mean(datapoints)

    thingspeak_data = mean_data.to_thingspeak()
    print('sending data\n{}'.format(thingspeak_data))

    success = False
    number_of_retries = 3

    while not success and number_of_retries > 0:
        try:
            client_id = binascii.hexlify(machine.unique_id())
            client = MQTTClient(client_id, 'mqtt.thingspeak.com', user='wipy#1', password=MQTT_API_KEY, port=8883, ssl=True)
            client.connect()
            client.publish(topic='channels/379710/publish/{}'.format(MQTT_WRITE_API_KEY), msg=thingspeak_data)
            client.disconnect()
            success = True
        except OSError as e:
            print('network error: {}'.format(e.errno))
            number_of_retries -= 1
            pass

    return success
