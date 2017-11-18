from helpers import *

class PMSData:
    def __init__(self, cpm25, cpm10, pm25, pm10):
        self.pm25 = pm25
        self.pm10 = pm10
        self.cpm25 = cpm25
        self.cpm10 = cpm10


    @classmethod
    def from_bytes(cls, frame):
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
                return cls(cpm25, cpm10, pm25, pm10)

            raise ValueError('control sum is {}, expected {}'.format(str(control_sum_data), str(control_sum)))
