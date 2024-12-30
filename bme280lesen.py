#!/usr/bin/python3

## @package : bme280lesen
#  Read data from a digital pressure sensor.
#
#  Official datasheet available from :
#  https://www.bosch-sensortec.com/bst/products/all_products/bme280
#
# @author Matt Hawkins http://www.raspberrypi-spy.co.uk/
# @date   25/07/2016
#
#
# 

#--------------------------------------
#    ___  ___  _ ____
#   / _ \/ _ \(_) __/__  __ __
#  / , _/ ___/ /\ \/ _ \/ // /
# /_/|_/_/  /_/___/ .__/\_, /
#                /_/   /___/
#
#           bme280.py
#--------------------------------------
import time
from math import exp
from machine import I2C, Pin


class SMBus(I2C):
    """ Provides an 'SMBus' module which supports some of the py-smbus
        i2c methods, as well as being a subclass of machine.I2C

        Hopefully this will allow you to run code that was targeted at
        py-smbus unmodified on micropython.

        Use it like you would the machine.I2C class:

            import usmbus.SMBus

            bus = SMBus(id=0, scl=machine.Pin(15), sda=machine.Pin(10), freq=100000)
            bus.read_byte_data(addr, register)
            ... etc
    """

    def read_byte_data(self, addr, register):
        """ Read a single byte from register of device at addr
            Returns a single byte """
        return self.readfrom_mem(addr, register, 1)[0]

    def read_i2c_block_data(self, addr, register, length):
        """ Read a block of length from register of device at addr
            Returns a bytes object filled with whatever was read """
        register_size = 8
        if isinstance(register, list):
            temp = 0
            register_size = 0
            for r in bytes(register):
                temp <<= 8
                temp |= r
                register_size += 8
            register = temp
        return self.readfrom_mem(addr, register, length, addrsize=register_size)

    def write_byte_data(self, addr, register, data):
        """ Write a single byte from buffer `data` to register of device at addr
            Returns None """
        # writeto_mem() expects something it can treat as a buffer
        if isinstance(data, int):
            data = bytes([data])
        return self.writeto_mem(addr, register, data)

    def write_i2c_block_data(self, addr, register, data):
        """ Write multiple bytes of data to register of device at addr
            Returns None """
        # writeto_mem() expects something it can treat as a buffer
        if not isinstance(data, bytes):
            if not isinstance(data, list):
                data = [data]
            data = bytes(data)

        register_size = 8
        if isinstance(register, list):
            temp = 0
            register_size = 0
            for r in bytes(register):
                temp <<= 8
                temp |= r
                register_size += 8
            register = temp

        return self.writeto_mem(addr, register, data, addrsize=register_size)

#     # The following haven't been implemented, but could be.
#     def read_byte(self, *args, **kwargs):
#         """ Not yet implemented """
#         raise RuntimeError("Not yet implemented")
# 
#     def write_byte(self, *args, **kwargs):
#         """ Not yet implemented """
#         raise RuntimeError("Not yet implemented")
# 
#     def read_word_data(self, *args, **kwargs):
#         """ Not yet implemented """
#         raise RuntimeError("Not yet implemented")
# 
#     def write_word_data(self, *args, **kwargs):
#         """ Not yet implemented """
#         raise RuntimeError("Not yet implemented")
# 

## I²C Device-Adresse.
# 0x76 AZDElivery Default device I2C address,
# 0x77 Watterott Default device I2C address
DEVICE = 0x76 # AZDElivery Default device I2C address
#DEVICE = 0x77 # Watterott Default device I2C address

## I²C Bus-Nummer.
# Rev 2 Pi, Pi 2 & Pi 3 uses bus 1,
# Rev 1 Pi uses bus 0
scl_pin = Pin(11)
sda_pin = Pin(10)
bus = SMBus(1, scl=scl_pin, sda=sda_pin) 

def convert_16bit_to_twos_complement(byte):
    leftmost_bit = (1 << 15) & byte
    if not leftmost_bit:
        return int(byte)
    
    flipped_sign = byte & 0b0111111111111111
    return int(flipped_sign) - (1 << 15)

## return two bytes from data as a signed 16-bit value
def getShort(data, index):
  unsigned_int16 = getUShort(data, index)
  return convert_16bit_to_twos_complement(unsigned_int16)

## return two bytes from data as an unsigned 16-bit value
def getUShort(data, index):
  return (data[index+1] << 8) + data[index]

## return one byte from data as a signed char
def getChar(data,index): 
  result = data[index]
  if result > 127:
    result -= 256
  return result

## return one byte from data as an unsigned char
def getUChar(data,index): 
  result =  data[index] & 0xFF
  return result

## Chip ID Register Address
def readBME280ID(addr=DEVICE): 
  REG_ID     = 0xD0
  (chip_id, chip_version) = bus.read_i2c_block_data(addr, REG_ID, 2)
  return (chip_id, chip_version)

## alles lesen.
# die wichtigste Funktion
def readBME280All(addr=DEVICE):
  # Register Addresses
  REG_DATA = 0xF7
  REG_CONTROL = 0xF4
  REG_CONFIG  = 0xF5

  REG_CONTROL_HUM = 0xF2
  REG_HUM_MSB = 0xFD
  REG_HUM_LSB = 0xFE

  # Oversample setting - page 27
  # sinnvoll Oversampling 1 und forced mode fuer Wetterdaten
  OVERSAMPLE_TEMP = 1
  OVERSAMPLE_PRES = 1
  MODE = 1  #forced mode

  # Oversample setting for humidity register - page 26
  OVERSAMPLE_HUM = 1
  bus.write_byte_data(addr, REG_CONTROL_HUM, OVERSAMPLE_HUM)

  control = OVERSAMPLE_TEMP<<5 | OVERSAMPLE_PRES<<2 | MODE
  bus.write_byte_data(addr, REG_CONTROL, control)

  # Read blocks of calibration data from EEPROM
  # See Page 22 data sheet
  cal1 = bus.read_i2c_block_data(addr, 0x88, 24)
  cal2 = bus.read_i2c_block_data(addr, 0xA1, 1)
  cal3 = bus.read_i2c_block_data(addr, 0xE1, 7)

  # Convert byte data to word values
  dig_T1 = getUShort(cal1, 0)
  dig_T2 = getShort(cal1, 2)
  dig_T3 = getShort(cal1, 4)

  dig_P1 = getUShort(cal1, 6)
  dig_P2 = getShort(cal1, 8)
  dig_P3 = getShort(cal1, 10)
  dig_P4 = getShort(cal1, 12)
  dig_P5 = getShort(cal1, 14)
  dig_P6 = getShort(cal1, 16)
  dig_P7 = getShort(cal1, 18)
  dig_P8 = getShort(cal1, 20)
  dig_P9 = getShort(cal1, 22)

  dig_H1 = getUChar(cal2, 0)
  dig_H2 = getShort(cal3, 0)
  dig_H3 = getUChar(cal3, 2)

  dig_H4 = getChar(cal3, 3)
  dig_H4 = (dig_H4 << 24) >> 20
  dig_H4 = dig_H4 | (getChar(cal3, 4) & 0x0F)

  dig_H5 = getChar(cal3, 5)
  dig_H5 = (dig_H5 << 24) >> 20
  dig_H5 = dig_H5 | (getUChar(cal3, 4) >> 4 & 0x0F)

  dig_H6 = getChar(cal3, 6)

  # Wait in ms (Datasheet Appendix B: Measurement time and current calculation)
  wait_time = 1.25 + (2.3 * OVERSAMPLE_TEMP) + ((2.3 * OVERSAMPLE_PRES) + 0.575) + ((2.3 * OVERSAMPLE_HUM)+0.575)
  time.sleep(wait_time/1000)  # Wait the required time  

  # Read temperature/pressure/humidity
  data = bus.read_i2c_block_data(addr, REG_DATA, 8)
  pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
  temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
  hum_raw = (data[6] << 8) | data[7]
  
  #Refine temperature
  var1 = ((((temp_raw>>3)-(dig_T1<<1)))*(dig_T2)) >> 11
  var2 = (((((temp_raw>>4) - (dig_T1)) * ((temp_raw>>4) - (dig_T1))) >> 12) * (dig_T3)) >> 14
  t_fine = var1+var2
  temperature = float(((t_fine * 5) + 128) >> 8)

  # Refine pressure and adjust for temperature
  var1 = t_fine / 2.0 - 64000.0
  var2 = var1 * var1 * dig_P6 / 32768.0
  var2 = var2 + var1 * dig_P5 * 2.0
  var2 = var2 / 4.0 + dig_P4 * 65536.0
  var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
  var1 = (1.0 + var1 / 32768.0) * dig_P1
  if var1 == 0:
    pressure=0
  else:
    pressure = 1048576.0 - pres_raw
    pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
    var1 = dig_P9 * pressure * pressure / 2147483648.0
    var2 = pressure * dig_P8 / 32768.0
    pressure = pressure + (var1 + var2 + dig_P7) / 16.0

  # Refine humidity
  humidity = t_fine - 76800.0
  humidity = (hum_raw - (dig_H4 * 64.0 + dig_H5 / 16384.0 * humidity)) * (dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * humidity * (1.0 + dig_H3 / 67108864.0 * humidity)))
  humidity = humidity * (1.0 - dig_H1 * humidity / 524288.0)
  if humidity > 100:
    humidity = 100
  elif humidity < 0:
    humidity = 0

  return temperature/100.0,pressure/100.0,humidity

## lesen, ausgeben und Druck auf Meereshöhe umrechnen
# eher eine Testfunktion
def bme280lesen():

  (chip_id, chip_version) = readBME280ID()
  print("Chip ID     :", chip_id)
  print("Version     :", chip_version)

  temperature,pressure,humidity = readBME280All()

  print("Temperature : ", temperature, "C")
  print("   Pressure : ", pressure, "hPa")
  print("   Humidity : ", humidity, "%")
  # M, die mittlere molare Masse der Atmosphaerengase (0,02896 kg mol-1)
  # g, die Schwerebeschleunigung (9,807 m s-2),
  # R, die universelle Gaskonstante (8,314 J K-1 mol-1) und
  # TEMP, die absolute Temperatur (Jahresmittel)
  # nur mit Aussentemp: TEMP=273.25+temperature
  TEMP=273.25+21
  HOEHE=200
  redukt=exp((0.02896*9.807*HOEHE)/(8.314*TEMP))
  print ("        QNH : ", pressure*redukt, "hPa")

  #with open("/tmp/daten.txt", mode="w+t", encoding="utf-8") as file_a:
  #  file_a.write(temperature.hex()+pressure.hex()+humidity.hex()+(pressure*redukt).hex())


bme280lesen()