import time
import math
import struct
import board
import busio
from . import TMC_2209_reg as reg

class TMC_2209_cp_uart:
    mtr_id=0
    ser = None
    rFrame  = [0x55, 0, 0, 0  ]
    wFrame  = [0x55, 0, 0, 0 , 0, 0, 0, 0 ]
    communication_pause = 0
    _msres = -1

    def __init__(self, TMC_TX, TMC_RX, baud, addr):

        self.mtr_id=0
        #self.ser.init(baud, bits=8, parity=None, stop=1)
        #self.ser.timeout = 20000/baudrate            # adjust per baud and hardware. Sequential reads without some delay fail.
        self.communication_pause = 500/baud    # adjust per baud and hardware. Sequential reads without some delay fail.
        # self.ser = busio.UART(TMC_TX, TMC_RX, baud, bits=8, parity=None, stop=1, timeout=self.communication_pause)
        self.ser = busio.UART(TMC_TX, TMC_RX, baudrate = baud, timeout = self.communication_pause)

#-----------------------------------------------------------------------
# destructor
#-----------------------------------------------------------------------
    def __del__(self):
        return

#-----------------------------------------------------------------------
# this function calculates the crc8 parity bit
#-----------------------------------------------------------------------
    def compute_crc8_atm(self, datagram, initial_value=0):
        crc = initial_value
        # Iterate bytes in data
        for byte in datagram:
            # Iterate bits in byte
            for _ in range(0, 8):
                if (crc >> 7) ^ (byte & 0x01):
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
                # Shift to next bit
                byte = byte >> 1
        return crc

#-----------------------------------------------------------------------
# reads the registry on the TMC with a given address.
# returns the binary value of that register
#-----------------------------------------------------------------------
    def read_reg(self, reg):

        rtn = ""
        #self.ser.reset_output_buffer()
        #self.ser.reset_input_buffer()

        self.rFrame[1] = self.mtr_id
        self.rFrame[2] = reg
        self.rFrame[3] = self.compute_crc8_atm(self.rFrame[:-1])

        rt = self.ser.write(bytes(self.rFrame))
        if rt != len(self.rFrame):
            print("TMC2209: Err in write {}".format(__), file=sys.stderr)
            return False
        time.sleep(self.communication_pause)  # adjust per baud and hardware. Sequential reads without some delay fail.
        #if self.ser.any():
        rtn = self.ser.read()#read what it self
        time.sleep(self.communication_pause)  # adjust per baud and hardware. Sequential reads without some delay fail.
        if rtn == None:
            print("TMC2209: Err in read")
            return ""
#         print("received "+str(len(rtn))+" bytes; "+str(len(rtn)*8)+" bits")
        return(rtn[7:11])
#-----------------------------------------------------------------------
# this function tries to read the registry of the TMC 10 times
# if a valid answer is returned, this function returns it as an integer
#-----------------------------------------------------------------------
    def read_int(self, reg):
        tries = 0
        while(True):
            rtn = self.read_reg(reg)
            tries += 1
            if(len(rtn)>=4):
                break
            else:
                print("TMC2209: did not get the expected 4 data bytes. Instead got "+str(len(rtn))+" Bytes")
            if(tries>=10):
                print("TMC2209: after 10 tries not valid answer. exiting")
                print("TMC2209: is Stepper Powersupply switched on ?")
                raise SystemExit
        val = struct.unpack(">i",rtn)[0]
        return(val)

#-----------------------------------------------------------------------
# this function clear the communication buffers of the Raspberry Pi
#-----------------------------------------------------------------------
    def flushSerialBuffer(self):
        #self.ser.reset_output_buffer()
        #self.ser.reset_input_buffer()
        return

#-----------------------------------------------------------------------
# this sets a specific bit to 1
#-----------------------------------------------------------------------
    def set_bit(self, value, bit):
        return value | (bit)

#-----------------------------------------------------------------------
# this sets a specific bit to 0
#-----------------------------------------------------------------------
    def clear_bit(self, value, bit):
        return value & ~(bit)

    def readDRVSTATUS(self):
        print("TMC2209: ---")
        print("TMC2209: DRIVER STATUS:")
        drvstatus =self.read_int(reg.DRVSTATUS)
        if(drvstatus & reg.stst):
            print("TMC2209: Info: motor is standing still")
        else:
            print("TMC2209: Info: motor is running")

        if(drvstatus & reg.stealth):
            print("TMC2209: Info: motor is running on StealthChop")
        else:
            print("TMC2209: Info: motor is running on SpreadCycle")

        cs_actual = drvstatus & reg.cs_actual
        cs_actual = cs_actual >> 16
        print("TMC2209: CS actual: "+str(cs_actual))

        if(drvstatus & reg.olb):
            print("TMC2209: Warning: Open load detected on phase B")

        if(drvstatus & reg.ola):
            print("TMC2209: Warning: Open load detected on phase A")

        if(drvstatus & reg.s2vsb):
            print("TMC2209: Error: Short on low-side MOSFET detected on phase B. The driver becomes disabled")

        if(drvstatus & reg.s2vsa):
            print("TMC2209: Error: Short on low-side MOSFET detected on phase A. The driver becomes disabled")

        if(drvstatus & reg.s2gb):
            print("TMC2209: Error: Short to GND detected on phase B. The driver becomes disabled. ")

        if(drvstatus & reg.s2ga):
            print("TMC2209: Error: Short to GND detected on phase A. The driver becomes disabled. ")

        if(drvstatus & reg.ot):
            print("TMC2209: Error: Driver Overheating!")

        if(drvstatus & reg.otpw):
            print("TMC2209: Warning: Driver Overheating Prewarning!")

        print("---")

    #-----------------------------------------------------------------------
# read the register Adress "GCONF" and prints all current setting
#-----------------------------------------------------------------------
    def readGCONF(self):
        print("TMC2209: ---")
        print("TMC2209: GENERAL CONFIG")
        gconf = self.read_int(reg.GCONF)

        if(gconf & reg.i_scale_analog):
            print("TMC2209: Driver is using voltage supplied to VREF as current reference")
        else:
            print("TMC2209: Driver is using internal reference derived from 5VOUT")
        if(gconf & reg.internal_rsense):
            print("TMC2209: Internal sense resistors. Use current supplied into VREF as reference.")
            print("TMC2209: VREF pin internally is driven to GND in this mode.")
            print("TMC2209: This will most likely destroy your driver!!!")
            raise SystemExit
        else:
            print("TMC2209: Operation with external sense resistors")
        if(gconf & reg.en_spreadcycle):
            print("TMC2209: SpreadCycle mode enabled")
        else:
            print("TMC2209: StealthChop PWM mode enabled")
        if(gconf & reg.shaft):
            print("TMC2209: Inverse motor direction")
        else:
            print("TMC2209: normal motor direction")
        if(gconf & reg.index_otpw):
            print("TMC2209: INDEX pin outputs overtemperature prewarning flag")
        else:
            print("TMC2209: INDEX shows the first microstep position of sequencer")
        if(gconf & reg.index_step):
            print("TMC2209: INDEX output shows step pulses from internal pulse generator")
        else:
            print("TMC2209: INDEX output as selected by index_otpw")
        if(gconf & reg.mstep_reg_select):
            print("TMC2209: Microstep resolution selected by MSTEP register")
        else:
            print("TMC2209: Microstep resolution selected by pins MS1, MS2")

        print("TMC2209: ---")

#-----------------------------------------------------------------------
# read the register Adress "GSTAT" and prints all current setting
#-----------------------------------------------------------------------
    def readGSTAT(self):
        print("TMC2209: ---")
        print("TMC2209: GSTAT")
        gstat = self.read_int(reg.GSTAT)
        if(gstat & reg.reset):
            print("TMC2209: The Driver has been reset since the last read access to GSTAT")
        if(gstat & reg.drv_err):
            print("TMC2209: The driver has been shut down due to overtemperature or short circuit detection since the last read access")
        if(gstat & reg.uv_cp):
            print("TMC2209: Undervoltage on the charge pump. The driver is disabled in this case")
        print("TMC2209: ---")

#-----------------------------------------------------------------------
# read the register Adress "IOIN" and prints all current setting
#-----------------------------------------------------------------------
    def readIOIN(self):
        print("TMC2209: ---")
        print("TMC2209: INPUTS")
        ioin = self.read_int(reg.IOIN)

        if(ioin & reg.io_spread):
            print("TMC2209: spread is high")
        else:
            print("TMC2209: spread is low")

        if(ioin & reg.io_dir):
            print("TMC2209: dir is high")
        else:
            print("TMC2209: dir is low")

        if(ioin & reg.io_step):
            print("TMC2209: step is high")
        else:
            print("TMC2209: step is low")

        if(ioin & reg.io_enn):
            print("TMC2209: en is high")
        else:
            print("TMC2209: en is low")

        print("TMC2209: ---")

#-----------------------------------------------------------------------
# read the register Adress "CHOPCONF" and prints all current setting
#-----------------------------------------------------------------------
    def readCHOPCONF(self):
        print("TMC2209: ---")
        print("TMC2209: CHOPPER CONTROL")
        chopconf = self.read_int(reg.CHOPCONF)

        print("TMC2209: native "+str(self.getMicroSteppingResolution())+" microstep setting")

        if(chopconf & reg.intpol):
            print("TMC2209: interpolation to 256 microsteps")

        if(chopconf & reg.vsense):
            print("TMC2209: 1: High sensitivity, low sense resistor voltage")
        else:
            print("TMC2209: 0: Low sensitivity, high sense resistor voltage")

        print("TMC2209: ---")

#-----------------------------------------------------------------------
# this function can write a value to the register of the tmc
# 1. use read_int to get the current setting of the TMC
# 2. then modify the settings as wished
# 3. write them back to the driver with this function
#-----------------------------------------------------------------------
    def write_reg(self, reg, val):

        #self.ser.reset_output_buffer()
        #self.ser.reset_input_buffer()

        self.wFrame[1] = self.mtr_id
        self.wFrame[2] =  reg | 0x80;  # set write bit

        self.wFrame[3] = 0xFF & (val>>24)
        self.wFrame[4] = 0xFF & (val>>16)
        self.wFrame[5] = 0xFF & (val>>8)
        self.wFrame[6] = 0xFF & val

        self.wFrame[7] = self.compute_crc8_atm(self.wFrame[:-1])

        rtn = self.ser.write(bytes(self.wFrame))
        if rtn != len(self.wFrame):
            print("TMC2209: Err in write {}".format(__), file=sys.stderr)
            return False
        time.sleep(self.communication_pause)

        return(True)

#-----------------------------------------------------------------------
# this function als writes a value to the register of the TMC
# but it also checks if the writing process was successfully by checking
# the InterfaceTransmissionCounter before and after writing
#-----------------------------------------------------------------------
    def write_reg_check(self, reg, val):
        IFCNT           =   0x02

        ifcnt1 = self.read_int(IFCNT)
        self.write_reg(reg, val)
        ifcnt2 = self.read_int(IFCNT)
        ifcnt2 = self.read_int(IFCNT)

        if(ifcnt1 >= ifcnt2):
            print("TMC2209: writing not successful!")
            print("reg:{} val:{}", reg, val)
            print("ifcnt:",ifcnt1,ifcnt2)
            return False
        else:
            return True

#-----------------------------------------------------------------------
# returns the current native microstep resolution (1-256)
#-----------------------------------------------------------------------
    def getMicroSteppingResolution(self):
        chopconf = self.read_int(reg.CHOPCONF)
        msresdezimal = chopconf & (reg.msres0 | reg.msres1 | reg.msres2 | reg.msres3)
        msresdezimal = msresdezimal >> 24
        msresdezimal = 8 - msresdezimal
        self._msres = int(math.pow(2, msresdezimal))
        print(self._msres)
        return self._msres

#-----------------------------------------------------------------------
# sets the current native microstep resolution (1,2,4,8,16,32,64,128,256)
#-----------------------------------------------------------------------
    def setMicrosteppingResolution(self, msres):
        chopconf = self.read_int(reg.CHOPCONF)
        print(chopconf)
        chopconf = chopconf & (~reg.msres0 | ~reg.msres1 | ~reg.msres2 | ~reg.msres3) #setting all bits to zero
        print(chopconf)
        msresdezimal = int(math.log(msres, 2))
        print(msresdezimal)
        msresdezimal = 8 - msresdezimal
        print(msresdezimal)
        chopconf = int(chopconf) & int(4043309055)
        print(chopconf)
        chopconf = chopconf | msresdezimal <<24
        print(chopconf)
        print("TMC2209: writing "+str(msres)+" microstep setting")
        self.write_reg_check(reg.CHOPCONF, chopconf)
        return True
