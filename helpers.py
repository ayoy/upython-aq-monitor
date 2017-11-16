import utime

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

def read_frame(frame):
    cpm25 = 0
    cpm10 = 0
    pm25 = 0
    pm10 = 0
    control_sum = 0x42 + 0x4d
    o = 2
    frame_length = int.from_bytes(frame[o:o+2], 'big')
    control_sum += sum_of_bytes(frame[o:o+2])
    o += 2

    if frame_length == 28:
        control_sum += sum_of_bytes(frame[o:o+2]) # cpm1.0
        o += 2

        cpm25 = int.from_bytes(frame[o:o+2], 'big')
        control_sum += sum_of_bytes(frame[o:o+2])
        o += 2

        cpm10 = int.from_bytes(frame[o:o+2], 'big')
        control_sum += sum_of_bytes(frame[o:o+2])
        o += 2

        control_sum += sum_of_bytes(frame[o:o+2]) # pm1.0
        o += 2

        pm25 = int.from_bytes(frame[o:o+2], 'big')
        control_sum += sum_of_bytes(frame[o:o+2])
        o += 2

        pm10 = int.from_bytes(frame[o:o+2], 'big')
        control_sum += sum_of_bytes(frame[o:o+2])
        o += 2

        control_sum += sum_of_bytes(frame[o:o+14])
        o += 14

        control_sum_data = int.from_bytes(frame[o:o+2], 'big')
        if control_sum == control_sum_data:
            # print('control sum is {}'.format(str(control_sum)))
            return (cpm25, cpm10, pm25, pm10)

        printt('skipping frame, control sum is {}, expected {}'.format(str(control_sum_data), str(control_sum)))
        return (-1, -1, -1, -1)
