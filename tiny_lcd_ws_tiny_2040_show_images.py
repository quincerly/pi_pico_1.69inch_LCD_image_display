from machine import Pin,I2C,SPI,PWM,Timer, SoftI2C
import framebuf
import time
import os
import urtc

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
    def __init__(self): #SPI initialization  SPI初始化
        self.width = 240
        self.height = 280
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1,100_000_000,polarity=0, phase=0,bits= 8,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()
        
        #Define color, Micropython fixed to BRG format  定义颜色，Micropython固定为BRG格式
        self.red   =   0x07E0
        self.green =   0x001f
        self.blue  =   0xf800
        self.white =   0xffff
        self.black =   0x0000
        self.brown =   0X8430
        self.magenta = 0XF81F
        
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
        
    #Write characters, size is the font size, the minimum is 1  
    #写字符，size为字体大小,最小为1
    def write_text(self,text,x,y,size,color):
        ''' Method to write Text on OLED/LCD Displays
            with a variable font size

            Args:
                text: the string of chars to be displayed
                x: x co-ordinate of starting position
                y: y co-ordinate of starting position
                size: font size of text
                color: color of text to be displayed
        '''
        background = self.pixel(x,y)
        info = []
        # Creating reference charaters to read their values
        self.text(text,x,y,color)
        for i in range(x,x+(8*len(text))):
            for j in range(y,y+8):
                # Fetching amd saving details of pixels, such as
                # x co-ordinate, y co-ordinate, and color of the pixel
                px_color = self.pixel(i,j)
                info.append((i,j,px_color)) if px_color == color else None
        # Clearing the reference characters from the screen
        self.text(text,x,y,background)
        # Writing the custom-sized font characters on screen
        for px_info in info:
            self.fill_rect(size*px_info[0] - (size-1)*x , size*px_info[1] - (size-1)*y, size, size, px_info[2]) 
    
Gestures={
    0x02: 'up',
    0x01: 'down',
    0x03: 'left',
    0x04: 'right',
    0x05: 'click',
    0x0C: 'long_press',
    0x0B: 'double_click',
}
   
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
        self.Mode = 1
        self.Set_Mode(self.Mode)
        
        LCD.fill(LCD.white)
        LCD.rect(118,138,2,2,LCD.black)
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
        self.Mode = 0
        self.Set_Mode(self.Mode)
        LCD.fill(LCD.white)
        while self.gesture != 'double_click':
            LCD.fill(LCD.white)
            LCD.write_text('Double click',25,70,2,LCD.black)
            LCD.write_text('to finish...',25,90,2,LCD.black)
            LCD.write_text(f'{self.gesture}',25,130,2,LCD.red)
            yy, mm, dd=time.localtime()[:3]
            LCD.write_text("%02d/%02d/%4d" % (dd, mm, yy), 25, 170, 2, LCD.magenta)
            LCD.write_text("%02d:%02d:%02d" % time.localtime()[3:6], 25, 190, 2, LCD.magenta)
            if rtc is not None:
                rt=rtc.getTime()
                LCD.write_text(f"{rt.day:02d}/{rt.month:02d}/{rt.year:4d}", 25, 210, 2, LCD.green)
                LCD.write_text(f"{rt.hour:02d}:{rt.minute:02d}:{rt.second:02d}", 25, 230, 2, LCD.green)
                # print('Current date and time:')
                # print('Year:', rt.year)
                # print('Month:', rt.month)
                # print('Day:', rt.day)
                # print('Hour:', rt.hour)
                # print('Minute:', rt.minute)
                # print('Second:', rt.second)
                # print('Day of the Week:', rtc.days_of_week[rt.weekday])

            LCD.show() 
        
    def Int_Callback(self,pin):
        if self.Mode == 0 :
            gbyte=self._read_byte(0x01)
            # print(f"Gesture {self.gesture}")
            self.gesture = Gestures.get(gbyte, f"Unknown {gbyte}")

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
        # LCD.write_text(filename, 25, 90, 2, LCD.white)
        LCD.show()
    except OSError as e:
        print(f"ERROR: could not open {filename}: {e}")

if __name__=='__main__':

    LCD = LCD_1inch69()
    LCD.set_bl_pwm(65535)

    clock=Clock()
    # clock.setTimeFromSystem()

    touch=Touch_CST816D(mode=1,LCD=LCD)

    images=list(filter(lambda f: f[-4:]==".raw", os.listdir("")))

    while True:
        touch.Touch_Gesture(rtc=clock)
        for image in images[1:]:
            if touch.gesture=="long_press": break
            ViewImage(images[0])
            time.sleep(5)
            # print(f"Image: {image}")
            if touch.gesture=="long_press": break
            ViewImage(image)
            time.sleep(5)


