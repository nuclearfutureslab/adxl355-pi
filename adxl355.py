# Copyright (c) 2018 Moritz Kuett
#
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import time

# register addresses
REG_DEVID_AD     = 0x00
REG_DEVID_MST    = 0x01
REG_PARTID       = 0x02
REG_REVID        = 0x03
REG_STATUS       = 0x04
REG_FIFO_ENTRIES = 0x05
REG_TEMP2        = 0x06
REG_TEMP1        = 0x07
REG_XDATA3       = 0x08
REG_XDATA2       = 0x09
REG_XDATA1       = 0x0A
REG_YDATA3       = 0x0B
REG_YDATA2       = 0x0C
REG_YDATA1       = 0x0D
REG_ZDATA3       = 0x0E
REG_ZDATA2       = 0x0F
REG_ZDATA1       = 0x10
REG_FIFO_DATA    = 0x11
REG_OFFSET_X_H   = 0x1E
REG_OFFSET_X_L   = 0x1F
REG_OFFSET_Y_H   = 0x20
REG_OFFSET_Y_L   = 0x21
REG_OFFSET_Z_H   = 0x22
REG_OFFSET_Z_L   = 0x23
REG_ACT_EN       = 0x24
REG_ACT_THRESH_H = 0x25
REG_ACT_THRESH_L = 0x26
REG_ACT_COUNT    = 0x27
REG_FILTER       = 0x28
REG_FIFO_SAMPLES = 0x29
REG_INT_MAP      = 0x2A
REG_SYNC         = 0x2B
REG_RANGE        = 0x2C
REG_POWER_CTL    = 0x2D
REG_SELF_TEST    = 0x2E
REG_RESET        = 0x2F

# Settings
SET_RANGE_2G     = 0b01
SET_RANGE_4G     = 0b10
SET_RANGE_8G     = 0b11

SET_ODR_4000     = 0b0000
SET_ODR_2000     = 0b0001
SET_ODR_1000     = 0b0010
SET_ODR_500      = 0b0011
SET_ODR_250      = 0b0100
SET_ODR_125      = 0b0101
SET_ODR_62_5     = 0b0110
SET_ODR_31_25    = 0b0111
SET_ODR_15_625   = 0b1000
SET_ODR_7_813    = 0b1001
SET_ODR_3_906    = 0b1010

ODR_TO_BIT = {4000: SET_ODR_4000,
              2000: SET_ODR_2000,
              1000: SET_ODR_1000,
              500: SET_ODR_500,
              250: SET_ODR_250,
              125: SET_ODR_125,
              62.5: SET_ODR_62_5,
              31.25: SET_ODR_31_25,
              15.625: SET_ODR_15_625,
              7.813: SET_ODR_7_813,
              3.906: SET_ODR_3_906}

class ADXL355():
    def __init__(self, transfer_function):
        self.transfer = transfer_function
        # self.factor = 2.048 * 2 / 2 ** 20
        self.setrange(SET_RANGE_2G) # sets factor correctly

    def read(self, register, length=1):
        address = (register << 1) | 0b1
        if length == 1:
            result = self.transfer([address, 0x00])
            return result[1]
        else:
            result = self.transfer([address] + [0x00] * (length))
            return result[1:]

    def write(self, register, value):
        # Shift register address 1 bit left, and set LSB to zero
        address = (register << 1) & 0b11111110
        result = self.transfer([address, value])

    def fifofull(self):
        return self.read(REG_STATUS) & 0b10

    def fifooverrange(self):
        return self.read(REG_STATUS) & 0b100
    
    def start(self):
        tmp = self.read(REG_POWER_CTL)
        self.write(REG_POWER_CTL, tmp & 0b0)

    def stop(self):
        tmp = self.read(REG_POWER_CTL)
        self.write(REG_POWER_CTL, tmp | 0b1)
        
    def dumpinfo(self):
        print("ADXL355 SPI Info Dump")
        print("========================================")
        idad = self.read(REG_DEVID_AD)
        print("Analog Devices ID: 0x{:X}".format(idad))
        memsid = self.read(REG_DEVID_MST)
        print("Analog Devices MEMS ID: 0x{:X}".format(memsid))
        devid = self.read(REG_PARTID)
        print("Device ID: 0x{0:X} (octal: {0:o})".format(devid))

        powerctl = self.read(REG_POWER_CTL)
        print("Power Control Status: 0b{:08b}".format(powerctl))
        if(powerctl & 0b1):
            print("--> Standby")
        else:
            print("--> Measurement Mode")

        rng = self.read(REG_RANGE)
        if rng & 0b11 == SET_RANGE_2G:
            print("Operating in 2g range")
        if rng & 0b11 == SET_RANGE_4G:
            print("Operating in 4g range")
        if rng & 0b11 == SET_RANGE_8G:
            print("Operating in 8g range")
              
    def whoami(self):
        t = self.read(REG_PARTID)
        return t

    def setrange(self, r):
        self.stop()
        temp = self.read(REG_RANGE)
        if r == SET_RANGE_2G:
            self.write(REG_RANGE, (temp & 0b11111100) | SET_RANGE_2G)
            self.factor = 2.048 * 2 / 2 ** 20
        if r == SET_RANGE_4G:
            self.write(REG_RANGE, (temp & 0b11111100) | SET_RANGE_4G)
            self.factor = 4.096 * 2 / 2 ** 20
        if r == SET_RANGE_8G:
            self.write(REG_RANGE, (temp & 0b11111100) | SET_RANGE_8G)
            self.factor = 8.192 * 2 / 2 ** 20
        self.start()
        # not sure why, but without it does not work
        time.sleep(0.05)

    def setfilter(self, hpf=0b000, lpf=0b0000):
        self.stop()
        self.write(REG_FILTER, (hpf << 4) | lpf)
        self.start()
        time.sleep(0.05)
    
    def temperatureRaw(self):
        high = self.read(REG_TEMP2)
        low = self.read(REG_TEMP1)
        res = ((high & 0b00001111) << 8) | low
        return res

    def temperature(self, bias = 1852.0, slope=-9.05):
        temp = self.temperatureRaw()
        res = ((temp - bias) / slope) + 25;
        return res
    
    def getXRaw(self):
        datal = self.read(REG_XDATA3, 3)
        low = (datal[2] >> 4)
        mid = (datal[1] << 4)
        high = (datal[0] << 12)
        res = low | mid | high
        res = self.twocomp(res)
        return res
    
    def getX(self):
        return float(self.getXRaw()) * self.factor

    def getYRaw(self):
        datal = self.read(REG_YDATA3, 3)
        low = (datal[2] >> 4)
        mid = (datal[1] << 4)
        high = (datal[0] << 12)
        res = low | mid | high
        res = self.twocomp(res)
        return res

    def getY(self):
        return float(self.getYRaw()) * self.factor

    def getZRaw(self):
        datal = self.read(REG_ZDATA3, 3)
        low = (datal[2] >> 4)
        mid = (datal[1] << 4)
        high = (datal[0] << 12)
        res = low | mid | high
        res = self.twocomp(res)
        return res

    def getZ(self):
        return float(self.getZRaw()) * self.factor
    

    def get3V(self):
        return [self.getX(), self.getY(), self.getZ()]

    def get3Vfifo(self):
        res = []
        x = self.read(REG_FIFO_DATA, 3)
        while(x[2] & 0b10 == 0):
            y = self.read(REG_FIFO_DATA, 3)
            z = self.read(REG_FIFO_DATA, 3)
            res.append([x, y, z])
            x = self.read(REG_FIFO_DATA, 3)
        return res

    def emptyfifo(self):
        x = self.read(REG_FIFO_DATA, 3)
        while(x[2] & 0b10 == 0):
            x = self.read(REG_FIFO_DATA, 3)

    def hasnewdata(self):
        res = self.read(REG_STATUS)
        if res & 0b1:
            return True
        return False

    def fastgetsamples(self, sampleno = 1000):
        """Get specified numbers of samples from FIFO, without any processing.

        This function is needed for fast sampling, without loosing samples. While FIFO should be enough for many situations, there is no check for FIFO overflow implemented (yet).
        """
        res = []
        while(len(res) < sampleno):
            res += self.get3Vfifo()
        return res[0:sampleno]

    def getsamplesRaw(self, sampleno = 1000):
        """Get specified numbers of samples from FIFO, and process them into signed integers"""
        data = self.fastgetsamples(sampleno)
        return self.convertlisttoRaw(data)

    def getsamples(self, sampleno = 1000):
        """Get specified numbers of samples from FIFO, process and convert to g values"""
        data = self.getsamplesRaw(sampleno)
        return self.convertRawtog(data)

    # def getsamples(self, sampleno = 1000):
    #     data = [0] * sampleno
    #     for i in range(sampleno):
    #         while(not self.hasnewdata()):
    #             continue
    #         data[i] = self.get3V()
    #     return data

    def convertlisttoRaw(self, data):
        """Convert a list of 'list' style samples into signed integers"""
        res = []
        for i in range(len(data)):
            row3v = []
            for j in range(3):
                low = (data[i][j][2] >> 4)
                mid = (data[i][j][1] << 4)
                high = (data[i][j][0] << 12)
                value = 1 * self.twocomp(low | mid | high)
                row3v.append(value)
            res.append(row3v)
        return res

    def convertRawtog(self, data):
        """Convert a list of raw style samples into g values"""
        res = [[d[0] * self.factor, d[1] * self.factor, d[2] * self.factor] for d in data]
        return res
    
    def twocomp(self, value):
        if (0x80000 & value):
            ret = - (0x0100000 - value)
            # from ADXL355_Acceleration_Data_Conversion function from EVAL-ADICUP360 repository
            # value = value | 0xFFF00000
        else:
            ret = value
        return ret
    
    
