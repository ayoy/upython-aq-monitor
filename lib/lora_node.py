from network import LoRa
import socket
import binascii
import struct
import time
import machine
import pycom
from keychain import NETWORK_KEY, APP_SESSION_KEY, DEVICE_ADDRES
from keychain import APP_EUI, APP_KEY

def _connect_to_LoRaWAN(lora):
    # create an ABP authentication params
    dev_addr = struct.unpack(">l", binascii.unhexlify(DEVICE_ADDRES))[0]
    nwk_swkey = binascii.unhexlify(NETWORK_KEY)
    app_swkey = binascii.unhexlify(APP_SESSION_KEY)
    #
    # # join a network using ABP (Activation By Personalization)
    lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

    # app_eui = binascii.unhexlify(APP_EUI)
    # app_key = binascii.unhexlify(APP_KEY)
    # join a network using OTAA (Over the Air activation)
    # lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
    # print('Sending OTAA join...')

    # Loop until joined
    while not lora.has_joined():
        machine.idle()
    print('... joined!')

def send_bytes(payload):
    # initialize LoRa in LORAWAN mode.
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868, adr=True)
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
    s.setblocking(True)
    s.bind(1)

    print('Sending bytes: {}'.format(payload))
    s.send(payload)
    # time.sleep(4)
    # rx, port = s.recvfrom(256)
    # if rx:
    #     print('Received: {}, on port: {}'.format(rx, port))

    s.close()
    print('Payload sent')
    lora.nvram_save()
    return True
