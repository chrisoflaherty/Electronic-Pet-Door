from time import sleep_ms,sleep
from machine import Pin, SPI
#from lib.rfid.mfrc522 import MFRC522
from os import uname



class MFRC522:

    OK = 0
    NOTAGERR = 1
    ERR = 2

    REQIDL = 0x26
    REQALL = 0x52
    AUTHENT1A = 0x60
    AUTHENT1B = 0x61

    def __init__(self, spi2, cs):

        self.spi = spi2
        self.cs = cs
        self.cs.value(1)
        self.spi.init()
        self.init()

    def _wreg(self, reg, val):

        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & ((reg << 1) & 0x7e)))
        self.spi.write(b'%c' % int(0xff & val))
        self.cs.value(1)

    def _rreg(self, reg):

        self.cs.value(0)
        self.spi.write(b'%c' % int(0xff & (((reg << 1) & 0x7e) | 0x80)))
        val = self.spi.read(1)
        self.cs.value(1)

        return val[0]

    def _sflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tocard(self, cmd, send):

        recv = []
        bits = irq_en = wait_irq = n = 0
        stat = self.ERR

        if cmd == 0x0E:
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == 0x0C:
            irq_en = 0x77
            wait_irq = 0x30

        self._wreg(0x02, irq_en | 0x80)
        self._cflags(0x04, 0x80)
        self._sflags(0x0A, 0x80)
        self._wreg(0x01, 0x00)

        for c in send:
            self._wreg(0x09, c)
        self._wreg(0x01, cmd)

        if cmd == 0x0C:
            self._sflags(0x0D, 0x80)

        i = 2000
        while True:
            n = self._rreg(0x04)
            i -= 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                break

        self._cflags(0x0D, 0x80)

        if i:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                stat = self.OK

                if n & irq_en & 0x01:
                    stat = self.NOTAGERR
                elif cmd == 0x0C:
                    n = self._rreg(0x0A)
                    lbits = self._rreg(0x0C) & 0x07
                    if lbits != 0:
                        bits = (n - 1) * 8 + lbits
                    else:
                        bits = n * 8

                    if n == 0:
                        n = 1
                    elif n > 16:
                        n = 16

                    for _ in range(n):
                        recv.append(self._rreg(0x09))
            else:
                stat = self.ERR

        return stat, recv, bits

    def _crc(self, data):

        self._cflags(0x05, 0x04)
        self._sflags(0x0A, 0x80)

        for c in data:
            self._wreg(0x09, c)

        self._wreg(0x01, 0x03)

        i = 0xFF
        while True:
            n = self._rreg(0x05)
            i -= 1
            if not ((i != 0) and not (n & 0x04)):
                break

        return [self._rreg(0x22), self._rreg(0x21)]

    def init(self):

        self.reset()
        self._wreg(0x2A, 0x8D)
        self._wreg(0x2B, 0x3E)
        self._wreg(0x2D, 30)
        self._wreg(0x2C, 0)
        self._wreg(0x15, 0x40)
        self._wreg(0x11, 0x3D)
        self.antenna_on()

    def reset(self):
        self._wreg(0x01, 0x0F)

    def antenna_on(self, on=True):

        if on and ~(self._rreg(0x14) & 0x03):
            self._sflags(0x14, 0x03)
        else:
            self._cflags(0x14, 0x03)

    def request(self, mode):

        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tocard(0x0C, [mode])

        if (stat != self.OK) | (bits != 0x10):
            stat = self.ERR

        return stat, bits

    def anticoll(self):

        ser_chk = 0
        ser = [0x93, 0x20]

        self._wreg(0x0D, 0x00)
        (stat, recv, bits) = self._tocard(0x0C, ser)

        if stat == self.OK:
            if len(recv) == 5:
                for i in range(4):
                    ser_chk = ser_chk ^ recv[i]
                if ser_chk != recv[4]:
                    stat = self.ERR
            else:
                stat = self.ERR

        return stat, recv

    def select_tag(self, ser):

        buf = [0x93, 0x70] + ser[:5]
        buf += self._crc(buf)
        (stat, recv, bits) = self._tocard(0x0C, buf)
        return self.OK if (stat == self.OK) and (bits == 0x18) else self.ERR

    def auth(self, mode, addr, sect, ser):
        return self._tocard(0x0E, [mode, addr] + sect + ser[:4])[0]

    def stop_crypto1(self):
        self._cflags(0x08, 0x08)

    def read(self, addr):

        data = [0x30, addr]
        data += self._crc(data)
        (stat, recv, _) = self._tocard(0x0C, data)
        return recv if stat == self.OK else None

    def write(self, addr, data):

        buf = [0xA0, addr]
        buf += self._crc(buf)
        (stat, recv, bits) = self._tocard(0x0C, buf)

        if not (stat == self.OK) or not (bits == 4) or not ((recv[0] & 0x0F) == 0x0A):
            stat = self.ERR
        else:
            buf = []
            for i in range(16):
                buf.append(data[i])
            buf += self._crc(buf)
            (stat, recv, bits) = self._tocard(0x0C, buf)
            if not (stat == self.OK) or not (bits == 4) or not ((recv[0] & 0x0F) == 0x0A):
                stat = self.ERR

        return stat

#END
sck = Pin(5, Pin.OUT)
mosi = Pin(18, Pin.OUT)
miso = Pin(19, Pin.OUT)
off = Pin(12,Pin.OUT) #new
spi = SPI(baudrate=96000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)
#spi2 = SPI(baudrate=96000, polarity=1, phase=1, sck=sck, mosi=mosi, miso =miso) 
cs2 = Pin(33, Pin.OUT) #33 old pin
cs1 = Pin(13, Pin.OUT) #pin sda
test = Pin(26,Pin.OUT)
Config = Pin(14,Pin.IN)
save = Pin(32,Pin.OUT)
door = Pin(15,Pin.OUT)

#print(myint)

#test.value(1)
  #  while True:
#print("access1")


def do_read():   #read tag ids
    global uid
    global value
    global value2
       # while True:
    rdr = MFRC522(spi, cs1)
   # rdr2 = MFRC522_2(spi2, cs2) #device 2
    value = ""
    (status, tag_type) = rdr.request(rdr.REQIDL)
    if status == rdr.OK:
        (status, raw_uid) = rdr.anticoll()
        if status == rdr.OK:
            value = ("0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
            print(value)
            sleep_ms(100)

def do_read2():   #read tag ids for second sensor
    global uid
    global value
    global value2
       # while True:
    rdr = MFRC522(spi, cs2)
   # rdr2 = MFRC522_2(spi2, cs2) #device 2
    value2 = ""
    (status, tag_type) = rdr.request(rdr.REQIDL)
    if status == rdr.OK:
        (status, raw_uid2) = rdr.anticoll()
        if status == rdr.OK:
            value2 = ("0x%02x%02x%02x%02x" % (raw_uid2[0], raw_uid2[1], raw_uid2[2], raw_uid2[3]))
            print(value2)
            sleep_ms(100) 
       
def setup():      #setup the tag id
    global uid
    off.value(0)
    rdr = MFRC522(spi, cs1)
    uid = ""
    (status, tag_type) = rdr.request(rdr.REQIDL)
    if status == rdr.OK:
        (status, raw_uid) = rdr.anticoll()
        if status == rdr.OK:
            uid = ("0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
            print(uid)
            sleep_ms(100)

# def wait():     #Not used
#     while True:
#         print("waiting")
#         sleep(0.01)
#         if Config.value(switch):
#             print("switch")

global value
global uid
global value2
#var1 = Config #Pin 14 is config and var1
while True:
    if Config.value():   #config pin high then setup uid
        while True:
            print("setup begins")
            print("scan card")
            save.value(1)  #turn on setup id
            setup()
            if uid:
                for z in range (0,2):
                    print("led")   #flash led when setup is complete
                    save.value(1)
                    sleep_ms(1000)
                    save.value(0)
                    sleep_ms(1000)
                off.value(1)
                break
    else: #config pin low so constant reading
        do_read()
        if value == uid:
            door.value(1)
            sleep(5)
            door.value(0)
        do_read2()
        if value2 == uid:   #if read uid is uid LED turn on for 5 second
            door.value(1)
            sleep(5)
            door.value(0)
        #print(value2)
       # print(value2)
        while value2 != uid or value != uid:    #if read uid is not uid repeat read
            if Config.value():
                break
            else:
                do_read()
                if value == uid:
                    door.value(1)
                    sleep(5)
                    door.value(0)

                do_read2()
                if value2 == uid:   #if read uid is uid LED turn on for 5 second
                    door.value(1)
                    sleep(5)
                    door.value(0)


print("end program")