from machine import Pin,I2C,SPI,PWM,Timer
import framebuf
import time
import os

# Tiny2040
DC = 4 #GP4 GREEN
CS = 5 #GP5 ORANGE
SCK = 6 # GP6 YELLOW
MOSI = 7 # GP7 BLUE
# MISO = 4
RST = 3 # GP3 WHITE
BL = 2 #GP2 PURPLE

#LCD Driver  LCD驱动
class LCD_1inch69(framebuf.FrameBuffer):
    def __init__(self): #SPI initialization  SPI初始化
        self.width = 240
        self.height = 280
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(0,100_000_000,polarity=0, phase=0,bits= 8,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
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
        LCD.show()
    except OSError as e:
        print(f"ERROR: could not open {filename}: {e}")

if __name__=='__main__':

    LCD = LCD_1inch69()
    LCD.set_bl_pwm(65535)

    # Touch=Touch_CST816D(mode=1,LCD=LCD)
    # Touch.Touch_Gesture()
    # Touch.Touch_HandWriting()
    # LCD.fill(LCD.red)
    # time.sleep(5)
    
    # LCD.write_text('Gesture test',70,90,1,LCD.black)
    # LCD.write_text('Complete as prompted',35,120,1,LCD.black)
    # LCD.show()
    # time.sleep(1)

    images=list(filter(lambda f: f[-4:]==".raw", os.listdir("")))
    while True:
        for image in images[1:]:
            ViewImage(images[0])
            time.sleep(5)
            print(f"Image: {image}")
            ViewImage(image)
            time.sleep(5)


