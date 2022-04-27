# Untitled - By: thanakornwongsanit - Fri Apr 22 2022
#connect2port and Cone detect
import sensor, image, time, lcd, math
from machine import I2C,UART
from fpioa_manager import fm
from Maix import GPIO

lcd.init()
lcd.rotation(2)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)


stock = []
stopTag = 50


i2c = I2C(I2C.I2C0, freq=100000, scl=34, sda=32)

laneColor = [(93, 100, -53, -9, -128, 127)]
hiCut =[(80,100,-10,10,-10,10)] #ใช้เพื่อป้องกันแสงสะท้อน เช่น สีขาวสีเหลืองมันคล้ายๆกัน
cone = [(52, 89, 10, 127, -10, 127)] #สีกรวย
old_cx_normal = 0

def motorControl(speedL, speedR):
    i2c.writeto(0x12, bytes( [int(speedL+127),int(speedR+127)] )) #ส่งข้อมูลไป2byteไปที่address 0x12
#motorControl(50,50)
#time.sleep(1)
#motorControl(0,0)

def sw_OK_press():  #ให้รอกดก่อนจึงจะเริ่มหมุนล้อ
    while True:
        swok = i2c.readfrom(0x12,1)
        #print(swok)
        if int(swok[0]) ==1 :
            break
#sw_OK_press()
#motorControl(50,50)
#time.sleep(1)
#motorControl(0,0)

def getError(showLine):
        global old_cx_normal
        cy = img.height() / 2
        cx = (laneLine.rho() - (cy * math.sin(math.radians(laneLine.theta())))) / math.cos(math.radians(laneLine.theta()))
        cx_middle = cx - (img.width() /2)
        cx_normal = cx_middle / (img.width() /2)
        if old_cx_normal != None :
            old_cx_normal = (cx_normal * 0.9) + (old_cx_normal * 0.1)
        else :
            old_cx_normal = cx_normal
        #print(old_cx_normal)
        if showLine and laneLine:
            img.draw_line(laneLine.line(),thickness=2,color=(0,255,0))
        return old_cx_normal

def findCone(inputImage,detectArea): #ใช้areaเพิ่มเพื่อถ้าเห็นไกลๆ พื้นที่น้อยๆ จะไม่หลบ
    if inputImage :
        detectCone = inputImage.find_blobs(cone,area_threshold=detectArea,pixels_threshold=int(detectArea*0.7))
        #print(detectCone)
        if detectCone :
            return detectCone[0].cx() #ถ้าเจอให้ส่งตำแหน่งตรงกลางออกไป
    else :
        return 0

sw_OK_press()
lastError = 0
Kp = 24
Kd = 9
nSpeed = 30


while(True):
    img = sensor.snapshot()
    img.binary(hiCut,zero=True) #แสงสะท้องให้เป็น0หมด กลายเป็นสีดำหมด เราไม่สนใจ
    #lane = img.find_blobs(laneColor,area_threshold=200,pixels_threshold=120) #หาสีlaneที่ต้องการ
    #for x in lane:
        #img.draw_rectangle(x[:4],thickness=2,color=(0,255,0),fill=False) #ตีกรอบสีที่ต้องการ
    coneDetect = img.find_blobs(cone,area_threshold=200,pixels_threshold=120) #หาสีconeที่ต้องการ
    for x in coneDetect:
        img.draw_rectangle(x[:4],thickness=2,color=(255,0,0),fill=False) #ตีกรอบสีที่ต้องการ

    #print(findCone(img,23000))
    laneLine = img.get_regression(laneColor,area_threshold=200,pixels_threshold=120)
    coneNaja = findCone(img,20000)
    if coneNaja :
        if coneNaja <= (img.width()//2)-25 : #ถ้าอยู่ทางซ้าย กลางจอเถิบเลย25pixelเป็นต้นไป
            motorControl(30,0)
            time.sleep_ms(500)
            motorControl(35,35)
            time.sleep_ms(1000)
            motorControl(20,35)
            time.sleep_ms(2000)
            motorControl(35,0)
            time.sleep_ms(500)
            #หลบไปทางขวา
        elif coneNaja >= (img.width()//2)-25 : #ถ้าอยู่ทาขวา กลางจอเถิบขวาเลย25pixelเป็นต้นไป
            motorControl(0,30)
            time.sleep_ms(500)
            motorControl(35,35)
            time.sleep_ms(1000)
            motorControl(35,20)
            time.sleep_ms(2000)
            motorControl(0,35)
            time.sleep_ms(500)
            #หลบไปทางleft
        else : #ถ้าอยู่กลางให้หลบไปทางขวา
            motorControl(30,0)
            time.sleep_ms(500)
            motorControl(35,35)
            time.sleep_ms(1)
            motorControl(20,35)
            time.sleep_ms(2000)
            motorControl(35,0)
            time.sleep_ms(500)
            #หลบไปทางขวา

    elif laneLine :
        #img.draw_line(laneLine.line(),thickness=2,color=(255,0,0))  #ถ้ามีเส้นให้ตีเส้น
        #print(getError(True))
        error = getError(True)
        PDValue = (Kp * error) + (Kd*(error-lastError))
        lastError = error
        leftPower = nSpeed + PDValue
        rightPower = nSpeed - PDValue
        if leftPower > 100 :
            leftPower = 100
        if rightPower > 100 :
            rightPower = 100
        if leftPower < -100 :
            leftPower = -100
        if rightPower < -100 :
            rightPower = -100
        motorControl(leftPower, rightPower)
    else :
        motorControl(0,0)

    lcd.display(img)
