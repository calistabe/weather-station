import machine
import time

from machine import SPI, Pin
import time

# Display resolution
EPD_WIDTH       = 200
EPD_HEIGHT      = 200

class EPD:
    def __init__(self, epdconfig: "RaspberryPi"):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.epdconfig = epdconfig

    lut_vcom0 = [0x0E, 0x14, 0x01, 0x0A, 0x06, 0x04, 0x0A, 0x0A, 0x0F, 0x03, 0x03, 0x0C, 0x06, 0x0A, 0x00]
    lut_w = [0x0E, 0x14, 0x01, 0x0A, 0x46, 0x04, 0x8A, 0x4A, 0x0F, 0x83, 0x43, 0x0C, 0x86, 0x0A, 0x04]
    lut_b = [0x0E, 0x14, 0x01, 0x8A, 0x06, 0x04, 0x8A, 0x4A, 0x0F, 0x83, 0x43, 0x0C, 0x06, 0x4A, 0x04]
    lut_g1 = [0x8E, 0x94, 0x01, 0x8A, 0x06, 0x04, 0x8A, 0x4A, 0x0F, 0x83, 0x43, 0x0C, 0x06, 0x0A, 0x04]
    lut_g2 = [0x8E, 0x94, 0x01, 0x8A, 0x06, 0x04, 0x8A, 0x4A, 0x0F, 0x83, 0x43, 0x0C, 0x06, 0x0A, 0x04]
    lut_vcom1 = [0x03, 0x1D, 0x01, 0x01, 0x08, 0x23, 0x37, 0x37, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    lut_red0 = [0x83, 0x5D, 0x01, 0x81, 0x48, 0x23, 0x77, 0x77, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    lut_red1 = [0x03, 0x1D, 0x01, 0x01, 0x08, 0x23, 0x37, 0x37, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] 
    
    # Hardware reset
    def reset(self):
        self.epdconfig.digital_write(self.reset_pin, 1)
        self.epdconfig.delay_ms(200) 
        self.epdconfig.digital_write(self.reset_pin, 0) # module reset
        self.epdconfig.delay_ms(5)
        self.epdconfig.digital_write(self.reset_pin, 1)
        self.epdconfig.delay_ms(200)   

    def send_command(self, command: int):
        self.epdconfig.digital_write(self.dc_pin, 0)
        self.epdconfig.digital_write(self.cs_pin, 0)
        # TODO error handling
        command_in_bytes = command.to_bytes(1, "big")
        self.epdconfig.spi_writebyte(command_in_bytes)
        self.epdconfig.digital_write(self.cs_pin, 1)

    def send_data(self, data: int):
        self.epdconfig.digital_write(self.dc_pin, 1)
        self.epdconfig.digital_write(self.cs_pin, 0)
        # TODO error handling
        data_in_bytes = data.to_bytes(1, "big")
        self.epdconfig.spi_writebyte(data_in_bytes)
        self.epdconfig.digital_write(self.cs_pin, 1)
        
    def ReadBusy(self):
        print("e-Paper busy")
        while(self.epdconfig.digital_read(self.busy_pin) == 0):
            self.epdconfig.delay_ms(100)    
        print("e-Paper busy release")
      
    def set_lut_bw(self):
        self.send_command(0x20) # vcom
        for count in range(0, 15):
            self.send_data(self.lut_vcom0[count])
        self.send_command(0x21) # ww --
        for count in range(0, 15):
            self.send_data(self.lut_w[count])
        self.send_command(0x22) # bw r
        for count in range(0, 15):
            self.send_data(self.lut_b[count])
        self.send_command(0x23) # wb w
        for count in range(0, 15):
            self.send_data(self.lut_g1[count])
        self.send_command(0x24) # bb b
        for count in range(0, 15):
            self.send_data(self.lut_g2[count])

    def set_lut_red(self):
        self.send_command(0x25)
        for count in range(0, 15):
            self.send_data(self.lut_vcom1[count])
        self.send_command(0x26)
        for count in range(0, 15):
            self.send_data(self.lut_red0[count])
        self.send_command(0x27)
        for count in range(0, 15):
            self.send_data(self.lut_red1[count])
            
    def init(self):
        if (self.epdconfig.module_init() != 0):
            # will never happen
            return -1
        # EPD hardware init start
        self.reset()
        
        self.send_command(0x01) # POWER_SETTING
        self.send_data(0x07)
        self.send_data(0x00)
        self.send_data(0x08)
        self.send_data(0x00)
        self.send_command(0x06) # BOOSTER_SOFT_START
        self.send_data(0x07)
        self.send_data(0x07)
        self.send_data(0x07)
        self.send_command(0x04) # POWER_ON

        self.ReadBusy()

        self.send_command(0X00) # PANEL_SETTING
        self.send_data(0xCF)
        self.send_command(0X50) # VCOM_AND_DATA_INTERVAL_SETTING
        self.send_data(0x17)
        self.send_command(0x30) # PLL_CONTROL
        self.send_data(0x39)
        self.send_command(0x61) # TCON_RESOLUTION set x and y
        self.send_data(0xC8)
        self.send_data(0x00)
        self.send_data(0xC8)
        self.send_command(0x82) # VCM_DC_SETTING_REGISTER
        self.send_data(0x0E)
        
        self.set_lut_bw()
        self.set_lut_red()
        return 0

    def getbuffer(self, image):
        buf = [0xFF] * int(self.width * self.height / 8)
        # Set buffer to value of Python Imaging Library image.
        # Image must be in mode 1.
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError('Image must be same dimensions as display \
                ({0}x{1}).' .format(self.width, self.height))

        pixels = image_monocolor.load()
        for y in range(self.height):
            for x in range(self.width):
                # Set the bits for the column of pixels at the current position.
                if pixels[x, y] == 0:
                    buf[int((x + y * self.width) / 8)] &= ~(0x80 >> (x % 8))
        return buf
    
    def transform_black_picture(self, data_array: list[list[int]]) -> list[int]:
        """
        Input: 200 x 200 array of pixels in binary: either 0b00, 0b01, 0b10, 0b11
        Output: list of length 200 x 200 / 8 * 2 bytes for transmitting to display
        """
        if len(data_array) != self.height:
            raise ValueError(f"Data array has height {len(data_array)}; must be {self.height}")
        
        def process_row(row):
            new_row = []
            for i in range(len(row) // 4):
                start_index = 4 * i
                val = 0b0
                for j in range(4):
                    val += row[start_index + j] << (4 - j)
                new_row.append(val)
            return new_row

        final_data = []
        for row in data_array:
            final_data.extend(process_row(row))
        
        if len(final_data) != self.width * self.height / 4:
            raise ValueError(f"Final data has length {len(final_data)}")
        
        return final_data
    
    def set_black_pixel(self, data, x_coord, y_coord, new_val):
        # TODO error handling
        byte_index = y_coord * self.width // 4 + x_coord // 4
        orig_byte = data[byte_index]
        shift = ((3 - x_coord % 4) * 2)
        bit_mask = (0b11 << shift) ^ 0b11111111
        orig_byte &= bit_mask
        orig_byte |= new_val << shift
        data[byte_index] = orig_byte

    def display_pattern(self):
        CMD_DATA_START_TRANSMISSION_1 = 0x10
        CMD_DISPLAY_REFRESH = 0x12

        self.send_command(CMD_DATA_START_TRANSMISSION_1)
        data = [0b11111111 for _ in range(self.width * self.height // 4)]
        for i in range(10, 20):
            for j in range(10, 191):
                self.set_black_pixel(data, j, i, 0b00)

        for i in range(20, 180):
            for j in range(95, 106):
                self.set_black_pixel(data, j, i, 0b00)


        for x in data:
            self.send_data(x)


        # self.send_command(0x13) # DATA_START_TRANSMISSION_2
        # for i in range(0, int(self.width * self.height / 8)):
        #     self.send_data(0x0F)  

        self.send_command(CMD_DISPLAY_REFRESH)
        self.ReadBusy()

    def display(self, blackimage, redimage):
        # send black data
        if (blackimage != None):
            self.send_command(0x10) # DATA_START_TRANSMISSION_1
            for i in range(0, int(self.width * self.height / 8)):
                temp = 0x00
                for bit in range(0, 4):
                    if (blackimage[i] & (0x80 >> bit) != 0):
                        temp |= 0xC0 >> (bit * 2)
                self.send_data(temp)  
                temp = 0x00
                for bit in range(4, 8):
                    if (blackimage[i] & (0x80 >> bit) != 0):
                        temp |= 0xC0 >> ((bit - 4) * 2)
                self.send_data(temp)
                
        # send red data        
        if (redimage != None):
            self.send_command(0x13) # DATA_START_TRANSMISSION_2
            for i in range(0, int(self.width * self.height / 8)):
                self.send_data(redimage[i])  

        self.send_command(0x12) # DISPLAY_REFRESH
        self.ReadBusy()

    def Clear(self):
        self.send_command(0x10) # DATA_START_TRANSMISSION_1
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
            self.send_data(0xFF)
            
        self.send_command(0x13) # DATA_START_TRANSMISSION_2
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)

        self.send_command(0x12) # DISPLAY_REFRESH
        self.ReadBusy()

    def sleep(self):
        self.send_command(0x50) # VCOM_AND_DATA_INTERVAL_SETTING
        self.send_data(0x17)
        self.send_command(0x82) # to solve Vcom drop 
        self.send_data(0x00)        
        self.send_command(0x01) # power setting      
        self.send_data(0x02) # gate switch to external
        self.send_data(0x00)
        self.send_data(0x00) 
        self.send_data(0x00) 
        self.ReadBusy()
        
        self.send_command(0x02) # power off
        
        self.epdconfig.delay_ms(2000)
        self.epdconfig.module_exit()

class RaspberryPi:
    # Pin definition
    RST_PIN  = 17
    DC_PIN   = 3
    CS_PIN   = 8
    BUSY_PIN = 4
    PWR_PIN  = 18 # missing
    MOSI_PIN = 7 # DIN on e-paper
    SCLK_PIN = 2 # CLK on e-paper

    def __init__(self):
        # spi init from epdconfig which we don't understand
        # # SPI device, bus = 0, device = 0
        # self.SPI.open(0, 0)
        # self.SPI.max_speed_hz = 4000000
        # self.SPI.mode = 0b00

        self.GPIO_RST_PIN    = Pin(self.RST_PIN, mode=Pin.OUT)
        self.GPIO_DC_PIN     = Pin(self.DC_PIN, mode=Pin.OUT)
        self.GPIO_CS_PIN     = Pin(self.CS_PIN, mode=Pin.OUT, value=1)

        self.GPIO_PWR_PIN    = Pin(self.PWR_PIN)
        self.GPIO_BUSY_PIN   = Pin(self.BUSY_PIN, mode=Pin.IN)
        self.GPIO_SCLK_PIN = Pin(self.SCLK_PIN, Pin.OUT)
        self.GPIO_MOSI_PIN = Pin(self.MOSI_PIN, Pin.OUT)
        
        print("init spi")
        print("sck", self.GPIO_SCLK_PIN)
        self.SPI = SPI(id=0, baudrate=40000000, sck=self.GPIO_SCLK_PIN, mosi=self.GPIO_MOSI_PIN)
        print("init spi done")

        

    def digital_write(self, pin, value):
        if pin == self.RST_PIN:
            if value:
                self.GPIO_RST_PIN.on()
            else:
                self.GPIO_RST_PIN.off()
        elif pin == self.DC_PIN:
            if value:
                self.GPIO_DC_PIN.on()
            else:
                self.GPIO_DC_PIN.off()
        elif pin == self.CS_PIN:
            if value:
                self.GPIO_CS_PIN.on()
            else:
                self.GPIO_CS_PIN.off()
        elif pin == self.PWR_PIN:
            if value:
                self.GPIO_PWR_PIN.on()
            else:
                self.GPIO_PWR_PIN.off()

    def digital_read(self, pin):
        if pin == self.BUSY_PIN:
            return self.GPIO_BUSY_PIN.value()
        elif pin == self.RST_PIN:
            return self.GPIO_RST_PIN.value()
        elif pin == self.DC_PIN:
            return self.GPIO_DC_PIN.value()
        elif pin == self.CS_PIN:
            return self.GPIO_CS_PIN.value()
        elif pin == self.PWR_PIN:
            return self.GPIO_PWR_PIN.value()

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.write(data)

    def module_init(self, cleanup=False):
        self.GPIO_PWR_PIN.on()
        
        return 0

    def module_exit(self):
        print("spi end")
        # self.SPI.close()
        # maybe deinit? then will need to re-init?

        self.GPIO_RST_PIN.off()
        self.GPIO_DC_PIN.off()
        self.GPIO_PWR_PIN.off()
        print("close 5V, Module enters 0 power consumption ...")

sensor = machine.ADC(4) # Create object sensor and init as pin ADC(4)
conversion_factor = 3.3 / 65535 # 3.3V are 16bit (65535)

def print_temp():
    valueTemp = sensor.read_u16() * conversion_factor
    temp = 27 - (valueTemp - 0.706) / 0.001721

    print(f"Temperature: {temp}")

pi = RaspberryPi()
epd = EPD(pi)

print("Init...")
epd.init()

print("Theoretically initted")

print("Clearing...")
epd.Clear()
print("Done")

#epd.display_pattern()
epd.sleep()