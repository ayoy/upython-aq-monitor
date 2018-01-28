from network import LoRa
import socket
import binascii
import struct
import time
import machine
from keychain import NETWORK_KEY, APP_KEY, DEVICE_ADDRES


def _connect_to_LoRaWAN(lora):
    # create an ABP authentication params
    dev_addr = struct.unpack(">l", binascii.unhexlify(DEVICE_ADDRES.replace(' ','')))[0]
    nwk_swkey = binascii.unhexlify(NETWORK_KEY.replace(' ',''))
    app_swkey = binascii.unhexlify(APP_KEY.replace(' ',''))

    # remove all the non-default channels
    for i in range(3, 16):
        lora.remove_channel(i)

    # set the 3 default channels to the same frequency
    lora.add_channel(0, frequency=868100000, dr_min=0, dr_max=5)
    lora.add_channel(1, frequency=868100000, dr_min=0, dr_max=5)
    lora.add_channel(2, frequency=868100000, dr_min=0, dr_max=5)

    # join a network using ABP (Activation By Personalization)
    lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))


def send_bytes(payload):
    # initialize LoRa in LORAWAN mode.
    lora = LoRa(mode=LoRa.LORAWAN)
    if machine.reset_cause() in [machine.DEEPSLEEP_RESET, machine.SOFT_RESET, machine.WDT_RESET]:
        print('Restoring LoRa state from NVS')
        lora.nvram_restore()

    if not lora.has_joined():
        print('No state stored in NVS or LoRa disconnected')
        print('Connecting ...')
        _connect_to_LoRaWAN(lora)
        if not lora.has_joined():
            print('Could not connect to LoRaWAN')
            return False

    # create a LoRa socket
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    # set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
    # make the socket blocking
    s.setblocking(False)

    print('Sending bytes: {}'.format(payload))
    s.send(payload)
    # time.sleep(4)
    # rx, port = s.recvfrom(256)
    # if rx:
    #     print('Received: {}, on port: {}'.format(rx, port))

    s.close()
    lora.nvram_save()
    return True
