from machine import Pin,I2C,SPI,PWM,Timer, SoftI2C
import framebuf
import time
import os
import urtc
import rp2

# Pico 2
#
# Touch
I2C_SDA = 6
I2C_SDL = 7
I2C_IRQ = 1
I2C_RST = 0
#
# LCD
DC = 14
CS = 9
SCK = 10
MOSI = 11
# MISO = 12
RST = 8
BL = 15

# RTC
# CLOCK_I2C_CHANNEL=1
CLOCK_I2C1_SCL=27 
CLOCK_I2C1_SDA=26

BUZZ=28
def RGBtoBRG565(r, g, b):
    # Clamp inputs to keep values strictly between 0.0 and 1.0
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    
    # Scale to maximum bit depths (5 bits = 31, 6 bits = 63)
    r_5 = int(round(r * 31))
    g_6 = int(round(g * 63))
    b_5 = int(round(b * 31))
    
    # Pack into BRG565: B(5 bits) | R(6 bits) | G(5 bits)
    brg565 = (b_5 << 11) | (r_5 << 5) | g_6
    
    # Return as an integer
    return brg565

def RGBtoRGB565(r, g, b):
    # Clamp inputs to keep values strictly between 0.0 and 1.0
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    
    # Scale to maximum bit depths (5 bits = 31, 6 bits = 63)
    r_5 = int(round(r * 31))
    g_6 = int(round(g * 63))
    b_5 = int(round(b * 31))
    
    # Pack into standard RGB565: R(5 bits) | G(6 bits) | B(5 bits)
    rgb565 = (r_5 << 11) | (g_6 << 5) | b_5
    
    return rgb565

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def square_wave():
    wrap_target()
    set(pins, 1)   # Pin HIGH
    set(pins, 0)   # Pin LOW
    wrap()

class Buzzer:
    def __init__(self, freq=2_000):
        self.pin = Pin(BUZZ, Pin.OUT)
        self.sm=rp2.StateMachine(0, square_wave, freq=freq, set_base=self.pin)
    def buzz(self, duration=1):
        # print("buzz on")
        self.sm.active(1)
        time.sleep(duration)
        self.sm.active(0)
        # print("buzz off")

def Alarm():
    buzzer=Buzzer();
    ViewImage("alarm.raw")
    while touch.gesture != "click": 
        buzzer.buzz(duration=0.5)
        time.sleep(0.5)

class Clock:
    def __init__(self):
        self.rtc=urtc.DS1307(SoftI2C(scl=Pin(CLOCK_I2C1_SCL), sda=Pin(CLOCK_I2C1_SDA), freq=100_000))
        self.days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def setTimeFromSystem(self):
        initial_time_tuple = time.localtime() #tuple (microPython)
        initial_time_seconds = time.mktime(initial_time_tuple) # local time in seconds
        initial_time = urtc.seconds2tuple(initial_time_seconds)

        # Sync the RTC
        self.rtc.datetime(initial_time)

    def setTimeFromTuple(self, time_tuple):
        self.rtc.datetime(time_tuple)

    def getTime(self):
        current_datetime = self.rtc.datetime()
        # print('Current date and time:')
        # print('Year:', current_datetime.year)
        # print('Month:', current_datetime.month)
        # print('Day:', current_datetime.day)
        # print('Hour:', current_datetime.hour)
        # print('Minute:', current_datetime.minute)
        # print('Second:', current_datetime.second)
        # print('Day of the Week:', self.days_of_week[current_datetime.weekday])
        return current_datetime

#LCD Driver  LCD驱动
class LCD_1inch69(framebuf.FrameBuffer):
    red   =   0x07E0
    green =   0x001f
    blue  =   0xf800
    white =   0xffff
    black =   0x0000
    # brown =   0X8430
    orange=RGBtoBRG565(1, 0.8, 0)
    cyan=RGBtoBRG565(0, 1, 1)

    def __init__(self): #SPI initialization  SPI初始化
        self.width = 240
        self.height = 280

        self.textwh=8
        self.textbuf = framebuf.FrameBuffer(bytearray(self.height * self.textwh * 2), self.height, self.textwh, framebuf.RGB565) # Rotated buffer for text

        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1,100_000_000,polarity=0, phase=0,bits= 8,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()
                
        self.fill(self.white) #Clear screen  清屏
        self.show()#Show  显示

        self.pwm = PWM(Pin(BL))
        self.pwm.freq(5000) #Turn on the backlight  开背光
        
    def write_cmd(self, cmd): #Write command  写命令
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf): #Write data  写数据
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)
        
    def set_bl_pwm(self,duty): #Set screen brightness  设置屏幕亮度
        self.pwm.duty_u16(duty)#max 65535
        
    def init_display(self): #LCD initialization  LCD初始化
        """Initialize dispaly"""  
        self.rst(1)
        time.sleep(0.01)
        self.rst(0)
        time.sleep(0.01)
        self.rst(1)
        time.sleep(0.05)
        
        self.write_cmd(0x36);
        self.write_data(0x00);

        self.write_cmd(0x3A);
        self.write_data(0x05);

        self.write_cmd(0xB2);
        self.write_data(0x0B);
        self.write_data(0x0B);
        self.write_data(0x00);
        self.write_data(0x33);
        self.write_data(0x35);

        self.write_cmd(0xB7);
        self.write_data(0x11);

        self.write_cmd(0xBB);
        self.write_data(0x35);

        self.write_cmd(0xC0);
        self.write_data(0x2C);

        self.write_cmd(0xC2);
        self.write_data(0x01);

        self.write_cmd(0xC3);
        self.write_data(0x0D);

        self.write_cmd(0xC4);
        self.write_data(0x20);

        self.write_cmd(0xC6);
        self.write_data(0x13);

        self.write_cmd(0xD0);
        self.write_data(0xA4);
        self.write_data(0xA1);

        self.write_cmd(0xD6);
        self.write_data(0xA1);

        self.write_cmd(0xE0);
        self.write_data(0xF0);
        self.write_data(0x06);
        self.write_data(0x0B);
        self.write_data(0x0A);
        self.write_data(0x09);
        self.write_data(0x26);
        self.write_data(0x29);
        self.write_data(0x33);
        self.write_data(0x41);
        self.write_data(0x18);
        self.write_data(0x16);
        self.write_data(0x15);
        self.write_data(0x29);
        self.write_data(0x2D);

        self.write_cmd(0xE1);
        self.write_data(0xF0);
        self.write_data(0x04);
        self.write_data(0x08);
        self.write_data(0x08);
        self.write_data(0x07);
        self.write_data(0x03);
        self.write_data(0x28);
        self.write_data(0x32);
        self.write_data(0x40);
        self.write_data(0x3B);
        self.write_data(0x19);
        self.write_data(0x18);
        self.write_data(0x2A);
        self.write_data(0x2E);

        self.write_cmd(0xE4);
        self.write_data(0x25);
        self.write_data(0x00);
        self.write_data(0x00);

        self.write_cmd(0x21);

        self.write_cmd(0x11);
        time.sleep(0.12);
        self.write_cmd(0x29);
    
    #设置窗口    
    def setWindows(self,Xstart,Ystart,Xend,Yend): 
        self.write_cmd(0x2A)
        self.write_data(Xstart >> 8)
        self.write_data(Xstart)
        self.write_data((Xend-1) >> 8)
        self.write_data(Xend-1)
        
        self.write_cmd(0x2B)
        self.write_data((Ystart+20) >> 8)
        self.write_data(Ystart+20)
        self.write_data(((Ystart+20)-1) >> 8)
        self.write_data((Ystart+20)-1)
        
        self.write_cmd(0x2C)
     
    #Show  显示   
    def show(self): 
        self.setWindows(0,0,self.width,self.height)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
        
    '''
        Partial display, the starting point of the local
        display here is reduced by 10, and the end point
        is increased by 10
    '''
    #Partial display, the starting point of the local display here is reduced by 10, and the end point is increased by 10
    #局部显示，这里的局部显示起点减少10，终点增加10
    def Windows_show(self,Xstart,Ystart,Xend,Yend):
        if Xstart > Xend:
            data = Xstart
            Xstart = Xend
            Xend = data
            
        if (Ystart > Yend):        
            data = Ystart
            Ystart = Yend
            Yend = data
            
        if Xstart <= 10:
            Xstart = 10
        if Ystart <= 10:
            Ystart = 10
            
        Xstart -= 10;Xend += 10
        Ystart -= 10;Yend += 10
        
        self.setWindows(Xstart,Ystart,Xend,Yend)      
        self.cs(1)
        self.dc(1)
        self.cs(0)
        for i in range (Ystart,Yend-1):             
            Addr = (Xstart * 2) + (i * 240 * 2)                
            self.spi.write(self.buffer[Addr : Addr+((Xend-Xstart)*2)])
        self.cs(1)
        
    # Write characters, size is the font size, the minimum is 1  
    def write_text(self, text, xin, yin, size, colour, rot90=False):
        ''' Method to write Text on OLED/LCD Displays
            with a variable font size

            Args:
                text: the string of chars to be displayed
                x: x co-ordinate of starting position
                y: y co-ordinate of starting position
                size: font size of text
                color: color of text to be displayed
        '''

        if rot90:
            x=self.height-yin
            y=xin
        else:
            x=xin
            y=yin

        # background = self.pixel(x,y)
        info = []
        # Creating reference charaters to read their values
        self.textbuf.fill(LCD_1inch69.white)
        self.textbuf.text(text, 0, 0, LCD_1inch69.black)
        for i in range(self.textwh*len(text)):
            for j in range(self.textwh):
                # Fetching amd saving details of pixels, such as
                # x co-ordinate, y co-ordinate, and color of the pixel
                info.append((i, j, colour)) if self.textbuf.pixel(i,j) == LCD_1inch69.black else None
        # Clearing the reference characters from the screen
        # self.text(text,x,y,background)
        # Writing the custom-sized font characters on screen
        for px_info in info:
            if rot90:
                # i=self.textwh-px_info[1]
                i=-px_info[1]
                j=px_info[0]
            else:
                i=px_info[0]
                j=px_info[1]
            # self.fill_rect(size*(i+x) - (size-1)*x , size*(j+y) - (size-1)*y, size, size, px_info[2]) 
            for ii in range(size):
                for jj in range(size):
                    thisx, thisy=size*i+x+ii, size*j+y+jj
                    self.pixel(thisx, thisy, px_info[2])

Gestures0={
    0x02: 'up',
    0x01: 'down',
    0x03: 'left',
    0x04: 'right',
    0x05: 'click',
    0x0C: 'long_press',
    0x0B: 'double_click',
}
Gestures90={
    0x02: 'left',
    0x01: 'right',
    0x03: 'down',
    0x04: 'up',
    0x05: 'click',
    0x0C: 'long_press',
    0x0B: 'double_click',
}
Gestures=Gestures90

#Touch drive  触摸驱动
class Touch_CST816D(object):
    #Initialize the touch chip  初始化触摸芯片
    def __init__(self,address=0x15,mode=0,i2c_num=1,i2c_sda=I2C_SDA,i2c_scl=I2C_SDL,irq_pin=I2C_IRQ,rst_pin=I2C_RST,LCD=None):
        self._bus = I2C(id=i2c_num,scl=Pin(i2c_scl),sda=Pin(i2c_sda),freq=400_000) #Initialize I2C 初始化I2C
        self._address = address #Set slave address  设置从机地址
        self.int=Pin(irq_pin,Pin.IN, Pin.PULL_UP)         
        self.rst=Pin(rst_pin,Pin.OUT)
        self.Reset()
        bRet=self.WhoAmI()
        if bRet :
            print("Success:Detected CST816D.")
            Rev= self.Read_Revision()
            print("CST816D Revision = {}".format(Rev))
            self.Stop_Sleep()
        else    :
            print("Error: Not Detected CST816D.")
            return None
        self.Mode = mode
        self.gesture="None"
        self.Flag = self.Flgh =self.l = 0
        self.X_point = self.Y_point = 0
        self.int.irq(handler=self.Int_Callback,trigger=Pin.IRQ_FALLING)
      
    def _read_byte(self,cmd):
        rec=self._bus.readfrom_mem(int(self._address),int(cmd),1)
        return rec[0]
    
    def _read_block(self, reg, length=1):
        rec=self._bus.readfrom_mem(int(self._address),int(reg),length)
        return rec
    
    def _write_byte(self,cmd,val):
        self._bus.writeto_mem(int(self._address),int(cmd),bytes([int(val)]))

    def WhoAmI(self):
        if (0xB5) != self._read_byte(0xA7):
            return False
        return True
    
    def Read_Revision(self):
        return self._read_byte(0xA9)
      
    #Stop sleeping  停止睡眠
    def Stop_Sleep(self):
        self._write_byte(0xFE,0x01)
    
    #Reset  复位    
    def Reset(self):
        self.rst(0)
        time.sleep_ms(1)
        self.rst(1)
        time.sleep_ms(50)
    
    #Set mode  设置模式   
    def Set_Mode(self,mode,callback_time=10,rest_time=5): 
        self.Mode=mode
        # mode = 0 gestures mode 
        # mode = 1 point mode 
        # mode = 2 mixed mode 
        if (mode == 1):      
            self._write_byte(0xFA,0X41)
            
        elif (mode == 2) :
            self._write_byte(0xFA,0X71)
            
        else:
            self._write_byte(0xFA,0X11)
            self._write_byte(0xEC,0X01)
     
    #Get the coordinates of the touch  获取触摸的坐标
    def get_point(self):
        xy_point = self._read_block(0x03,4)
        
        x_point= ((xy_point[0]&0x0f)<<8)+xy_point[1]
        y_point= ((xy_point[2]&0x0f)<<8)+xy_point[3]
        
        self.X_point=x_point
        self.Y_point=y_point
    
    #Draw points and show  画点并显示  
    def Touch_HandWriting(self):
        x = y = data = 0
        color = 0
        self.Flgh = 0
        self.Flag = 0
        self.Set_Mode(1)
        
        LCD.fill(LCD_1inch69.white)
        LCD.rect(118,138,2,2,LCD_1inch69.black)
        LCD.show()
        
        try:
            while True:              
                if self.Flag == 1:  
                    LCD.pixel(self.X_point,self.Y_point,color)
                    LCD.rect(self.X_point - 1,self.Y_point - 1,2,2,color)
                    LCD.Windows_show(x,y,self.X_point,self.Y_point)

        except KeyboardInterrupt:
            pass
    
    #Gesture  手势
    def Touch_Gesture(self, rtc=None):
        self.Set_Mode(0)
        # LCD.fill(LCD_1inch69.white)
        while self.gesture != 'double_click':
            # LCD.fill(LCD_1inch69.white)
            LCD.write_text('Double click',25,70,2,LCD_1inch69.black, rot90=True)
            LCD.write_text('to finish...',25,90,2,LCD_1inch69.black, rot90=True)
            LCD.write_text(f'{self.gesture.upper()}',25,130,3,LCD_1inch69.red, rot90=True)
            if rtc is not None:
                rt=rtc.getTime()
                LCD.write_text(f"{rt.day:02d}/{rt.month:02d}/{rt.year:4d}", 25, 180, 3, LCD_1inch69.green, rot90=True, savebg=True)
                LCD.write_text(f"{rt.hour:02d}:{rt.minute:02d}:{rt.second:02d}", 25, 210, 3, LCD_1inch69.green, rot90=True, restorebg=True, savebg=True)
                # print('Current date and time:')
                # print('Year:', rt.year)
                # print('Month:', rt.month)
                # print('Day:', rt.day)
                # print('Hour:', rt.hour)
                # print('Minute:', rt.minute)
                # print('Second:', rt.second)
                # print('Day of the Week:', rtc.days_of_week[rt.weekday])
            else:
                yy, mm, dd=time.localtime()[:3]
                LCD.write_text("%02d/%02d/%4d" % (dd, mm, yy), 25, 170, 2, LCD_1inch69.brown)
                LCD.write_text("%02d:%02d:%02d" % time.localtime()[3:6], 25, 200, 2, LCD_1inch69.brown)
            LCD.show()
        
    def Int_Callback(self,pin):
        if self.Mode == 0 :
            gbyte=self._read_byte(0x01)
            # print(f"Gesture {self.gesture}")
            self.gesture = Gestures.get(gbyte, f"Unknown {gbyte}")
            Buzzer().buzz(duration=0.2)

        elif self.Mode == 1:           
            self.Flag = 1
            self.get_point()

    def Timer_callback(self,t):
        self.l += 1
        if self.l > 100:
            self.l = 50

def load_raw(filename):
    """Load a raw RGB565 binary file into a bytearray."""
    print("Loading...")
    with open(filename, "rb") as f:
        return bytearray(f.read())

def ViewImage(filename):
    print(f"Loading {filename}...")
    try:
        with open(filename, "rb") as f:
            f.readinto(LCD.buffer)   # read directly into the existing buffer
        # LCD.write_text(filename, 25, 90, 2, LCD_1inch69.white)
        LCD.show()
    except OSError as e:
        print(f"ERROR: could not open {filename}: {e}")


def ViewImageWithClock(
        filename,
        # time_opts={'x': 55, 'y': 75, 'size': 3, 'colour': LCD_1inch69.black, 'outline_thick': 2, 'outline_colour': RGBtoBRG565(1, 0.97, 0)},
        time_opts={'x': 40, 'y': 75, 'size': 4, 'colour': LCD_1inch69.black, 'outline_thick': 2, 'outline_colour': RGBtoRGB565(0.9, 0.87, 0.9)},
        sec_opts={'x': 210, 'y': 75, 'size': 3, 'colour': LCD_1inch69.black, 'outline_thick': 2, 'outline_colour': RGBtoRGB565(0.9, 0.87, 0.9)},
        date_opts={'x': 70, 'y': 248, 'size': 2, 'colour': LCD_1inch69.white, 'shadow_offset': 3, 'shadow_colour': LCD_1inch69.black},
    ):
    # print(f"Loading {filename}...")
    try:

        # Image
        with open(filename, "rb") as f:
            f.readinto(LCD.buffer)   # read directly into the existing buffer

        rt=clock.getTime()
        # print(rt)

        # Time
        timestr=f"{rt.hour:02d}:{rt.minute:02d}" #:{rt.second:02d}"
        for (dx, dy) in zip(
                [v*time_opts['outline_thick'] for v in [-1,  1,  1, -1]],
                [v*time_opts['outline_thick'] for v in [-1, -1,  1,  1]],
                # [v*time_opts['outline_thick'] for v in [-1, -1, -1,  0,  1,  1,  1,  0]],
                # [v*time_opts['outline_thick'] for v in [-1,  0,  1,  1,  1,  0, -1, -1]],
            ):
            LCD.write_text(timestr, time_opts['x']+dx, time_opts['y']+dy, time_opts['size'], time_opts['outline_colour'], rot90=True)
        LCD.write_text(timestr, time_opts['x'], time_opts['y'], time_opts['size'], time_opts['colour'], rot90=True)

        # Seconds
        secstr=f"{rt.second:02d}"
        for (dx, dy) in zip(
                [v*sec_opts['outline_thick'] for v in [-1,  1,  1, -1]],
                [v*sec_opts['outline_thick'] for v in [-1, -1,  1,  1]],
                # [v*sec_opts['outline_thick'] for v in [-1, -1, -1,  0,  1,  1,  1,  0]],
                # [v*sec_opts['outline_thick'] for v in [-1,  0,  1,  1,  1,  0, -1, -1]],
            ):
            LCD.write_text(secstr, sec_opts['x']+dx, sec_opts['y']+dy, sec_opts['size'], sec_opts['outline_colour'], rot90=True)
        LCD.write_text(secstr, sec_opts['x'], sec_opts['y'], sec_opts['size'], sec_opts['colour'], rot90=True)

        # Date
        LCD.write_text(f"{rt.day:02d}/{rt.month:02d}/{rt.year:4d}", date_opts['x']+date_opts['shadow_offset'], date_opts['y']+date_opts['shadow_offset'], 2, date_opts['shadow_colour'], rot90=True)
        LCD.write_text(f"{rt.day:02d}/{rt.month:02d}/{rt.year:4d}", date_opts['x'], date_opts['y'], 2, date_opts['colour'], rot90=True)

        LCD.show()
    except OSError as e:
        print(f"ERROR: could not open {filename}: {e}")


if __name__=='__main__':

    # buzzer=Buzzer()
    # buzzer.buzz(duration=10, freq=2000)

    LCD = LCD_1inch69()
    LCD.set_bl_pwm(65535)

    clock=Clock()
    # clock.setTimeFromSystem()

    touch=Touch_CST816D(mode=1,LCD=LCD)
    touch.Set_Mode(0)

    images=list(filter(lambda f: f[-4:]==".raw" and f!="alarm.raw", os.listdir("")))

    while True:
        ViewImageWithClock(images[0])
        if touch.gesture=="double_click":
            touch.gesture=None
            Alarm()
        # time.sleep_ms(1000)

    # while True:
    #     # Alarm()
    #     for image in images[1:]:
    #         if touch.gesture=="long_press": break
    #         ViewImageWithClock(images[0])
    #         # time.sleep(5)
    #         # print(f"Image: {image}")
    #         if touch.gesture=="long_press": break
    #         ViewImageWithClock(image)
    #         # time.sleep(5)


