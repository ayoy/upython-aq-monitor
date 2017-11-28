import machine
from machine import UART, Pin
from helpers import *

class PMS5003:
    def __init__(self, en, tx, rx, rst):
        self.en = en
        self.tx = tx
        self.rx = rx
        self.rst = rst
        self.en.mode(Pin.OUT)
        self.rst.mode(Pin.OUT)

        self.uart = UART(1, baudrate=9600, pins=(self.tx, self.rx))
        self.uart.deinit()


    def wake_up(self):
        self.en(True)
        self.rst(True)
        self.uart.init(pins=(self.tx, self.rx))


    def idle(self):
        self.en(False)
        self.uart.deinit()


    def read_frames(self, count):
        frames = []
        # skip first frame because initial reading tends to be skewed
        odd_frame = True
        while len(frames) < count:
            self.__wait_for_data(32)

            while self.uart.read(1) != b'\x42':
                machine.idle()

            if self.uart.read(1) == b'\x4D':
                self.__wait_for_data(30)

                if odd_frame:
                    self.uart.readall()
                else:
                    try:
                        data = PMSData.from_bytes(b'\x42\x4D' + self.uart.read(30))
                        frames.append(data)
                    except ValueError as e:
                        print('error reading frame: {}'.format(e.message))
                        pass
                odd_frame = not odd_frame

        return frames


    def __wait_for_data(self, byte_count):
        def idle_timer(alarm):
            pycom.rgbled(0x550000)

        alarm = None
        u = self.uart.any()
        if u < byte_count:
            alarm = machine.Timer.Alarm(idle_timer, 3)
            print('waiting for data {}'.format(str(u)))
        while u < byte_count:
            u = self.uart.any()
            # 32*8*1000/9600 (32 bytes @9600kbps)
            # but let's assume byte is 10 bits to skip complex math
            machine.Timer.sleep_us(byte_count)
        try:
            alarm.cancel()
        except AttributeError:
            pass
        pycom.rgbled(0x000000)
        print('data ready {}'.format(str(self.uart.any())))


class PMSData:
    def __init__(self, cpm25, cpm10, pm25, pm10):
        self.pm25 = pm25
        self.pm10 = pm10
        self.cpm25 = cpm25
        self.cpm10 = cpm10


    @classmethod
    def from_bytes(cls, frame):

        def __sum_of_bytes(bytes):
            s = 0
            for b in bytes:
                s += b
            return s

        cpm25 = 0
        cpm10 = 0
        pm25 = 0
        pm10 = 0
        control_sum = 0x42 + 0x4d
        o = 2
        frame_length = int.from_bytes(frame[o:o+2], 'big')
        control_sum += __sum_of_bytes(frame[o:o+2])
        o += 2

        if frame_length == 28:
            control_sum += __sum_of_bytes(frame[o:o+2]) # cpm1.0
            o += 2

            cpm25 = int.from_bytes(frame[o:o+2], 'big')
            control_sum += __sum_of_bytes(frame[o:o+2])
            o += 2

            cpm10 = int.from_bytes(frame[o:o+2], 'big')
            control_sum += __sum_of_bytes(frame[o:o+2])
            o += 2

            control_sum += __sum_of_bytes(frame[o:o+2]) # pm1.0
            o += 2

            pm25 = int.from_bytes(frame[o:o+2], 'big')
            control_sum += __sum_of_bytes(frame[o:o+2])
            o += 2

            pm10 = int.from_bytes(frame[o:o+2], 'big')
            control_sum += __sum_of_bytes(frame[o:o+2])
            o += 2

            control_sum += __sum_of_bytes(frame[o:o+14])
            o += 14

            control_sum_data = int.from_bytes(frame[o:o+2], 'big')
            if control_sum == control_sum_data:
                # print('control sum is {}'.format(str(control_sum)))
                return cls(cpm25, cpm10, pm25, pm10)

            raise ValueError('control sum is {}, expected {}'.format(str(control_sum_data), str(control_sum)))
