# MicroPython DS3231 precison real time clock driver for Pycom devices.
# Adapted from Pyboard driver at https://github.com/peterhinch/micropython-samples
# Adapted by Dominik Kapusta, Jan 2018
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Peter Hinch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import utime
from machine import RTC, I2C

DS3231_I2C_ADDR = 0x68

class DS3231Exception(OSError):
    pass

rtc = RTC()

def now():  # Return the current time from the RTC in millisecs from year 2000
    secs = utime.time()
    ms = int(rtc.now()[6]/1000)
    if ms < 50:                                 # Might have just rolled over
        secs = utime.time()
    return 1000 * secs + ms

def bcd2dec(bcd):
    return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

def dec2bcd(dec):
    tens, units = divmod(dec, 10)
    return (tens << 4) + units

class DS3231:
    def __init__(self, bus, pins, baudrate=400000):
        self.ds3231 = I2C(bus, pins=pins, mode=I2C.MASTER, baudrate=baudrate)
        self.timebuf = bytearray(7)
        if DS3231_I2C_ADDR not in self.ds3231.scan():
            raise DS3231Exception("DS3231 not found on I2C bus at %s" % hex(DS3231_I2C_ADDR))

    def deinit(self):
        self.ds3231.deinit()

    def get_time(self, set_rtc = False):
        if set_rtc:
            data = self.await_transition()      # For accuracy set RTC immediately after a seconds transition
        else:
            self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf)
            data = self.timebuf
        ss = bcd2dec(data[0])
        mm = bcd2dec(data[1])
        if data[2] & 0x40:
            hh = bcd2dec(data[2] & 0x1f)
            if data[2] & 0x20:
                hh += 12
        else:
            hh = bcd2dec(data[2])
        wday = data[3]
        DD = bcd2dec(data[4])
        MM = bcd2dec(data[5] & 0x1f)
        YY = bcd2dec(data[6])
        if data[5] & 0x80:
            YY += 2000
        else:
            YY += 1900
        if set_rtc:
            rtc.init((YY, MM, DD, hh, mm, ss, 0))
        return (YY, MM, DD, hh, mm, ss, 0, 0) # Time from DS3231 in time.time() format (less yday)

    def save_time(self):
        (YY, MM, DD, hh, mm, ss, wday, yday) = utime.gmtime()
        wday += 1 # needs to be 1 == Monday, 7 == Sunday

        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 0, dec2bcd(ss))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 1, dec2bcd(mm))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 2, dec2bcd(hh))      # Sets to 24hr mode
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 3, dec2bcd(wday))    # 1 == Monday, 7 == Sunday
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 4, dec2bcd(DD))
        if YY >= 2000:
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 5, dec2bcd(MM) | 0b10000000)
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 6, dec2bcd(YY-2000))
        else:
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 5, dec2bcd(MM))
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 6, dec2bcd(YY-1900))

    def delta(self):                            # Return no. of mS RTC leads DS3231
        self.await_transition()
        rtc_ms = now()
        t_ds3231 = utime.mktime(self.get_time())  # To second precision, still in same sec as transition
        return rtc_ms - 1000 * t_ds3231

    def await_transition(self):                 # Wait until DS3231 seconds value changes
        self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf)
        ss = self.timebuf[0]
        while ss == self.timebuf[0]:
            self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf)
        return self.timebuf
