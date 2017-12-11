from machine import Pin
import utime
import pycom

class SHT1X:

    class AckException(Exception):
        pass

    class CRCException(Exception):
        pass

    MEASURE_T  = 0b00000011
    MEASURE_RH = 0b00000101
    SOFT_RESET = 0b00011110
    READ_STATUS_REGISTER = 0b000000111
    WRITE_STATUS_REGISTER = 0b000000110

    CLOCK_TIME_US = 10

    CRC_TABLE = [
        0, 49, 98, 83, 196, 245, 166, 151, 185, 136, 219, 234, 125, 76, 31, 46,
        67, 114, 33, 16, 135, 182, 229, 212, 250, 203, 152, 169, 62, 15, 92, 109,
        134, 183, 228, 213, 66, 115, 32, 17, 63, 14, 93, 108, 251, 202, 153, 168,
        197, 244, 167, 150, 1, 48, 99, 82, 124, 77, 30, 47, 184, 137, 218, 235,
        61, 12, 95, 110, 249, 200, 155, 170, 132, 181, 230, 215, 64, 113, 34, 19,
        126, 79, 28, 45, 186, 139, 216, 233, 199, 246, 165, 148, 3, 50, 97, 80,
        187, 138, 217, 232, 127, 78, 29, 44, 2, 51, 96, 81, 198, 247, 164, 149,
        248, 201, 154, 171, 60, 13, 94, 111, 65, 112, 35, 18, 133, 180, 231, 214,
        122, 75, 24, 41, 190, 143, 220, 237, 195, 242, 161, 144, 7, 54, 101, 84,
        57, 8, 91, 106, 253, 204, 159, 174, 128, 177, 226, 211, 68, 117, 38, 23,
        252, 205, 158, 175, 56, 9, 90, 107, 69, 116, 39, 22, 129, 176, 227, 210,
        191, 142, 221, 236, 123, 74, 25, 40, 6, 55, 100, 85, 194, 243, 160, 145,
        71, 118, 37, 20, 131, 178, 225, 208, 254, 207, 156, 173, 58, 11, 88, 105,
        4, 53, 102, 87, 192, 241, 162, 147, 189, 140, 223, 238, 121, 72, 27, 42,
        193, 240, 163, 146, 5, 52, 103, 86, 120, 73, 26, 43, 188, 141, 222, 239,
        130, 179, 224, 209, 70, 119, 36, 21, 59, 10, 89, 104, 255, 206, 157, 172
        ]

    def __init__(self, gnd, sck, data, vcc):
        self.gnd = gnd
        self.sck = sck
        self.data = data
        self.vcc = vcc

        self.gnd.mode(Pin.OUT)
        self.gnd.mode(Pin.PULL_DOWN)
        self.vcc.mode(Pin.PULL_UP)
        self.vcc.mode(Pin.OUT)
        self.sck.mode(Pin.OUT)
        self.sck.pull(None)
        self.data.mode(Pin.OPEN_DRAIN)
        self.data.pull(Pin.PULL_UP)

        self.sleep()


    def sleep(self):
        self.gnd(False)
        self.vcc(False)


    def wake_up(self):
        self.gnd(False)
        self.vcc(True)
        utime.sleep_ms(11)


    def temperature(self):
        readout = self.__send_command(self.MEASURE_T)
        return readout/2**14 * 163.8 - 40


    def humidity(self, temperature=25):
        readout = self.__send_command(self.MEASURE_RH)
        humidity = -2.0468 + 0.0367*readout - 1.5955e-6*readout**2
        if temperature != 25:
            humidity += (temperature - 25) * (0.01 + 8e-5 * readout)
        return humidity


    def __send_command(self, command):
        self.__command_start()
        self.__write_byte(command)
        self.__ack_bit()
        utime.sleep_ms(330)

        # data should be low when ready to read
        if self.data() == True:
            raise self.AckException

        msb = self.__read_byte()
        lsb = self.__read_byte()
        readout = (msb << 8) + lsb

        crc = self.__read_byte()
        utime.sleep_ms(11)
        computed_crc = self.__crc(command, msb, lsb)
        if crc != computed_crc:
            print('crc: {}, computed: {}'.format(crc, computed_crc))
            raise self.CRCException

        return readout

    def __crc(self, command, msb, lsb):
        crc = self.CRC_TABLE[command]
        crc ^= msb
        crc = self.CRC_TABLE[crc]
        crc ^= lsb
        crc = self.CRC_TABLE[crc]
        reversed_crc = 0
        for pos in range(8):
            bit = crc & 1<<pos != 0
            if bit == 1:
                reversed_crc |= 1<<7-pos
        return reversed_crc


    def __read_byte(self):
        byte = 0
        for pos in range(8, 0, -1):
            bit = self.__read()
            byte |= bit << pos-1
            # print('{} {} {}'.format(pos-1, bit, byte))

        self.data(False)
        self.__ack_bit(0)
        self.data(True)
        return byte


    def __read(self):
        self.sck(False)
        self.__noop()
        self.sck(True)
        self.__noop()
        data = self.data()
        self.sck(False)
        self.__noop()
        return data


    def __write_byte(self, byte):
        for pos in range(8, 0, -1):
            bit = byte & 1<<pos-1 != 0
            self.__write(bit)


    def __write(self, value):
        self.sck(False)
        self.data(value)
        self.__noop()
        self.sck(True)
        self.__noop()
        self.sck(False)
        self.__noop()


    def __ack_bit(self, value=True):
        self.sck(False)
        self.__noop()
        self.sck(True)
        self.__noop()
        self.sck(False)
        self.__noop()
        if self.data() != value:
            raise self.AckException


    def __command_start(self):
        self.data(True)
        self.sck(True)
        self.__noop()
        self.data(False)
        self.__noop()
        self.sck(False)
        self.__noop()
        self.sck(True)
        self.__noop()
        self.data(True)
        self.__noop()
        self.sck(False)
        self.__noop()


    def __noop(self):
        utime.sleep_us(self.CLOCK_TIME_US)
