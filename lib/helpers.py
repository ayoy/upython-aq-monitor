import utime
import machine
import pycom

# uart.write(b'\x42\x4D\x00\x00\xE4\x01\x73') # sleep
# uart.write(b'\x42\x4D\x01\x00\xE4\x01\x74') # wake up
# uart.write(b'\x42\x4D\x00\x00\xE1\x01\x70') # passive
# uart.write(b'\x42\x4D\x00\x00\xE2\x01\x71') # read data

def printt(objects):
    t = utime.localtime(utime.time())
    timestamp = '{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(t[0], t[1], t[2], t[3], t[4], t[5])
    print('{} {}'.format(timestamp, objects))


def sum_of_bytes(bytes):
    s = 0
    for b in bytes:
        s += b
    return s

def wait_for_data(uart, byte_count):
    def idle_timer(alarm):
        pycom.rgbled(0x550000)

    alarm = None
    u = uart.any()
    if u < byte_count:
        alarm = machine.Timer.Alarm(idle_timer, 3)
        printt('waiting for data {}'.format(str(u)))
    while u < byte_count:
        u = uart.any()
        machine.idle()
        machine.Timer.sleep_us(27)
    try:
        alarm.cancel()
    except AttributeError:
        pass
    pycom.rgbled(0x000000)
    printt('data ready {}'.format(str(uart.any())))
