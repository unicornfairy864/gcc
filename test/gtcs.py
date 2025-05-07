import turtle
import time
from urllib.request import urlopen
import threading
import random
import os
from collections import deque

VENTI = True
try:
    from playsound import playsound
except:
    VENTI = False
    print("Unable to load Venti. Running without voice!")

AUTH="jeangunnhildr"

FONT=('Arial', 10, 'normal')
LEVEL=1
SCTR="http://127.0.0.1:5033/signal"
ZCTR="http://127.0.0.1:5033/zug"
DCTR="http://127.0.0.1:5033/zugdist"
BCTR="http://127.0.0.1:5033/befehl"
LCTR="http://127.0.0.1:5033/lkjdisp"
ICTR="http://127.0.0.1:5033/signaldata"
ZUGNAME="zug1"
SCHUTZ_SIMU=True
SCHUTZ_PROB=1
DARK=True
DRANGE=4000

MYGREEN=("green2" if DARK else "green")
MYWHITE=("white" if DARK else "black")
MYBLUE=("cyan" if DARK else "blue")

# GTCS data collector
nextdist=0
curspeed=0
spdlim=40
lastspdlim = 120
accreq=0
gtcsinfo=[]
sysinfo=[]
thrust=0
eb=False
zugat=""
power=0
curlkj="?"
prereded=False
schutz=False
schutz_info=""

extcmd = []
lastseg = []
furseg = []
lbdisp = 0
zusatz_lastspdlim = 300

show_name=False

# Whether to pass neutral zone
passdz=False

# Superconduct is not a failure sometimes, depending on what you need.
# Volts High == Charged sometimes
apress=0
evolts=0
eamps=0
efreq=50

# 'a' or 'e'
cpsrc="a"
cptype={"a":"Anemo","e":"Electro","p":"Pantograph"}
# 'x' for empty page
syspages = {
    "q":[
        [lambda: cptype[cpsrc], lambda: MYWHITE]
    ],
    "w":[
        [lambda: cptype[cpsrc], lambda: MYWHITE],
        [lambda: ("{} MPa".format(round(apress,1))), lambda: ("red" if (((cpsrc == "a") and (apress < 10)) or apress > 200) else MYGREEN)]
    ],
    "e":[
        [lambda: cptype[cpsrc], lambda: MYWHITE],
        [lambda: ("{} V".format(round(evolts,1))), lambda: ("red" if (((cpsrc == "e") and (evolts < 10)) or evolts > 3000) else MYGREEN)],
        [lambda: ("{} A".format(round(eamps,1))), lambda: ("red" if (((cpsrc == "e") and (eamps < 0.1)) or eamps > 100) else MYGREEN)]
    ],
    "r":[
        [lambda: cptype[cpsrc], lambda: MYWHITE],
        [lambda: ("Neutral Section" if passdz else "Normal"), lambda: ("orange" if passdz else MYWHITE)],
        [lambda: ("{} V".format(round(evolts,1))), lambda: ("red" if (((cpsrc == "e") and (evolts < 10)) or evolts > 3000) else MYGREEN)],
        [lambda: ("{} A".format(round(eamps,1))), lambda: ("red" if (((cpsrc == "e") and (eamps < 0.1)) or eamps > 100) else MYGREEN)]
    ],
    "x":[]
}
csyspage = "q"

failures = {
    "thr":["Thrust No Response", False, lambda: False],
    "brk":["Brake No Response", False, lambda: False],
    "apwrlo":["Anemo Quality Low", False, lambda: ((cpsrc == "a") and (apress < 10))],
    "apwrhi":["Anemo Quality High", False, lambda: apress > 200],
    "epwrlo":["Electro Volts Low", False, lambda: ((cpsrc == "e") and (evolts < 10))],
    "epwrhi":["Electro Volts High", False, lambda: evolts > 3000],
    "epwrslo":["Electro Amps Low", False, lambda: ((cpsrc == "e") and (eamps < 0.1))],
    "epwrshi":["Electro Amps High", False, lambda: eamps > 100],
    "ovldr":["Element Overload", False, lambda: False],
    "scond":["Element Superconduct", False, lambda: False],
    "eblock":["Crystalize Blocking", False, lambda: False]
}

def maxthr_val():
    global apress, evolts, eamps, cpsrc
    if cpsrc == "a":
        return apress*1.5
    else:
        return (evolts*eamps)/250

ps_queue=deque()

def start_sound(name):
    global VENTI, ps_queue
    if VENTI:
        if len(ps_queue) > 0:
            cr = ps_queue.pop()
            ps_queue.append(cr)
            if cr == name:
                return
        ps_queue.append(name)

def sound_thr():
    global VENTI, ps_queue
    cfn = os.path.split(os.path.realpath(__file__))[0]
    if cfn[:-1] not in ["/", "\\"]:
        cfn = cfn + "/"
    cfn = cfn + "audio/"
    while True:
        if len(ps_queue) > 0:
            cur = ps_queue.popleft()
            if VENTI:
                try:
                    playsound(cfn + cur + ".mp3")
                except:
                    pass
        time.sleep(1)

turtle.tracer(False)

turtle2 = turtle.Turtle()
turtle3 = turtle.Turtle()
maxspder = turtle.Turtle()
acreqer = turtle.Turtle()
spdturtle = turtle.Turtle()
thrturtle = turtle.Turtle()
infobar = turtle.Turtle()
spdraw = turtle.Turtle()
limdraw = turtle.Turtle()
befehldisp = turtle.Turtle()
xspdraw = turtle.Turtle()
lkjdraw = turtle.Turtle()
spdhint = turtle.Turtle()
gaspress = turtle.Turtle()
routedisp = turtle.Turtle()
t = turtle.Pen()

if DARK:
    turtle.bgcolor('black')
    turtle.pencolor('white')
    turtle2.pencolor('white')
    turtle3.pencolor('white')
    maxspder.pencolor('white')
    acreqer.pencolor('white')
    spdturtle.pencolor('white')
    thrturtle.pencolor('white')
    infobar.pencolor('white')
    spdraw.pencolor('white')
    befehldisp.pencolor('white')
    xspdraw.pencolor('white')
    #lkjdraw.pencolor('white')
    spdhint.pencolor('white')
    gaspress.pencolor('white')

spdturtle.penup()
thrturtle.penup()
infobar.penup()
maxspder.penup()
acreqer.penup()
spdraw.penup()
limdraw.penup()
turtle2.penup()
befehldisp.penup()
xspdraw.penup()
lkjdraw.penup()
spdhint.penup()
gaspress.penup()
routedisp.penup()
maxspder.goto(-160, 80)
acreqer.goto(-160, 0)
spdhint.goto(-155, 5)
spdraw.goto(-160, 80)
limdraw.goto(-320, 0)
befehldisp.goto(-160, 220)
xspdraw.goto(-160,40)
lkjdraw.goto(-200, 200)
gaspress.goto(160,40)
routedisp.goto(-340, 0)

xspdraw.speed('fastest')
befehldisp.speed('fastest')
spdturtle.speed('fastest')
thrturtle.speed('fastest')
maxspder.speed('fastest')
acreqer.speed('fastest')
spdraw.speed('fastest')
turtle2.speed('fastest')
turtle3.speed('fastest')
lkjdraw.speed('fastest')
spdhint.speed('fastest')
gaspress.speed('fastest')
routedisp.speed('fastest')
befehldisp.pensize(2)
turtle2.pensize(2)
turtle3.pensize(2)
spdraw.pensize(3)
spdturtle.pensize(3)
thrturtle.pensize(3)
maxspder.pensize(3)
acreqer.pensize(3)
lkjdraw.pensize(2)
spdhint.pensize(3)
maxspder.pencolor('orange')
acreqer.pencolor('orange')
spdhint.pencolor(MYBLUE)
routedisp.pencolor(MYBLUE)
#xspdraw.pencolor('purple')

infobar.speed('fastest')

turtle.speed('fastest')
xspdraw.hideturtle()
befehldisp.hideturtle()
turtle.hideturtle()
turtle2.hideturtle()
turtle3.hideturtle()
infobar.hideturtle()
spdturtle.hideturtle()
thrturtle.hideturtle()
maxspder.hideturtle()
spdraw.hideturtle()
lkjdraw.hideturtle()
gaspress.hideturtle()
routedisp.hideturtle()

if LEVEL < 2:
    limdraw.hideturtle()
#acreqer.hideturtle()
#turtle.tracer(True, 500)

# 320 positions, 40 each, so here are 8
# [S Level] [P] [D] [S] [1] [2] [E] [M]

turtle.pensize(2)

iustr = ["120", "P", "D", "S", "1", "2", "E", "M", "Sifa", "Off"]
tcolor = ["blue", "green", "orange", "red", "green", "green", "blue", "blue", "orange", "blue"]
xcolor = ["white"]*10
#light = [True]*10
light = [True,False,False,False,False,False,False,False,False,False,False]
def render_bar():
    turtle3.clear()
    turtle3.right(turtle3.heading())
    turtle3.goto(-200, -60)
    for i in range(10):
        turtle3.pendown()
        if not light[i]:
            if DARK:
                turtle3.fillcolor('black')
            else:
                turtle3.fillcolor("white")
            turtle3.begin_fill()
            for j in range(4):
                turtle3.forward(40)
                turtle3.right(90)
            turtle3.end_fill()
            turtle3.forward(40)
        else:
            turtle3.fillcolor(tcolor[i])
            turtle3.begin_fill()
            for j in range(4):
                turtle3.forward(40)
                turtle3.right(90)
            #turtle.right(90)
            #print(turtle.heading())
            turtle3.end_fill()
            turtle3.penup()
            turtle3.forward(20)
            turtle3.right(90)
            turtle3.forward(20)
            turtle3.pencolor(xcolor[i])
            turtle3.write(iustr[i],align='center')
            if DARK:
                turtle3.pencolor('white')
            else:
                turtle3.pencolor("black")
            turtle3.left(90)
            turtle3.forward(20)
            turtle3.right(90)
            turtle3.forward(20)
            #turtle.left(turtle.heading())
            
            #turtle.left(90)
            turtle3.right(90)
            turtle3.forward(40)
            turtle3.right(90)
            turtle3.forward(40)
            # For debug,
            turtle3.right(90)
            turtle3.forward(40)
            #turtle.forward(80)
            #turtle.right(90)
            #turtle.forward(40)
            #turtle.right(90)
            #print(turtle.heading())
            turtle3.pendown()
            #time.sleep(4)
            #print("==")

def render_route_tackle(csp, cx, cy):
    global extcmd, lastseg, furseg, DRANGE, LEVEL, FONT, MYBLUE, MYGREEN, MYWHITE, curspeed, show_name
    if (len(csp) < 2):
        return
    dis = int(csp[0])
    routedisp.pencolor(MYBLUE)
    if csp[1] == "La":
        if curspeed > int(csp[3]) or curspeed < int(csp[2]):
            routedisp.pencolor('orange')
        routedisp.write("Lf " + csp[3] + "/" + csp[2], align='right', font=FONT)
    elif csp[1] == "Le":
        routedisp.pencolor(MYGREEN)
        routedisp.write("Lf ---", align='right', font=FONT)
    elif csp[1] == "T":
        routedisp.write(" ".join(csp[2:]), align='right', font=FONT)
    elif csp[1] == "S":
        # Draw signal lights, status represent at csp[3]:
        #routedisp.pencolor(MYWHITE)
        if LEVEL <= 2:
            routedisp.fillcolor('white')
            routedisp.begin_fill()
            routedisp.circle(3)
            routedisp.end_fill()
        else:
            if csp[3] == ".":
                routedisp.fillcolor('green')
                routedisp.begin_fill()
                routedisp.circle(3)
                routedisp.end_fill()
            elif csp[3] == "/":
                routedisp.fillcolor('yellow')
                routedisp.begin_fill()
                routedisp.circle(3)
                routedisp.end_fill()
            elif csp[3] == "|":
                routedisp.fillcolor('green')
                routedisp.begin_fill()
                routedisp.circle(3)
                routedisp.end_fill()
                routedisp.goto(cx-6, cy)
                routedisp.fillcolor('yellow')
                routedisp.begin_fill()
                routedisp.circle(3)
                routedisp.end_fill()
            elif csp[3] in "<>":
                routedisp.fillcolor('yellow')
                routedisp.begin_fill()
                routedisp.circle(3)
                routedisp.end_fill()
                routedisp.goto(cx-6, cy)
                routedisp.fillcolor('yellow')
                routedisp.begin_fill()
                routedisp.circle(3)
                routedisp.end_fill()
            elif csp[3].isdigit() and csp[3] != "0":
                if curspeed > int(csp[3])*10:
                    routedisp.pencolor('orange')
                routedisp.write("Hp " + csp[3] + "0", align='right', font=FONT)
            else:
                routedisp.fillcolor('red')
                routedisp.begin_fill()
                routedisp.circle(3)
                routedisp.end_fill()
        if show_name:
            routedisp.goto(cx-10, cy)
            routedisp.pencolor(MYBLUE)
            routedisp.write(csp[2], align='right', font=FONT)
    elif csp[1] == "P0":
        routedisp.pencolor('orange')
        routedisp.write("El 1", align='right', font=FONT)
    elif csp[1] == "P1":
        routedisp.write("El 2", align='right', font=FONT)

def render_route():
    global extcmd, lastseg, furseg, DRANGE, LEVEL, FONT, MYBLUE, MYGREEN, MYWHITE, curspeed
    routedisp.penup()
    routedisp.clear()
    cx = -340
    if LEVEL == 1:
        cx = -320
    clastseg = [-1000000, []]
    cfurseg = [1000000, []]
    for i in extcmd[1:]:
        csp = i.split(" ")
        dis = int(csp[0])
        if dis < 0:
            if dis > clastseg[0]:
                clastseg = [dis, csp]
        elif dis > DRANGE:
            if dis < cfurseg[0]:
                cfurseg = [dis, csp]
        else:
            routedisp.goto(cx, dis/20)
            render_route_tackle(csp, cx, dis/20)
    routedisp.goto(cx, -20)
    render_route_tackle(clastseg[1], cx, -20)
    routedisp.goto(cx, 240)
    render_route_tackle(cfurseg[1], cx, 240)
    routedisp.goto(cx, 255)
    if len(cfurseg[1]) >= 2:
        routedisp.pencolor(MYBLUE)
        routedisp.write(str(round(cfurseg[0]/1000, 2)), align='right', font=FONT)

def gtcs3_load():
    global LEVEL, curspeed, lastspdlim, zusatz_lastspdlim, lbdisp
    if LEVEL < 2:
        return
    limdraw.showturtle()
    limdraw.clear()
    limdraw.goto(-320, 0)
    limdraw.pendown()
    limdraw.pencolor('orange')
    limdraw.pensize(3)
    limdraw.goto(-320, min(220, nextdist/20))
    limdraw.penup()
    if (nextdist/20) >= 220:
        limdraw.goto(-320, 240)
        limdraw.write(str(round(nextdist/1000, 2)), font=FONT)
        limdraw.hideturtle()
    xspdraw.clear()
    xspdraw.penup()
    xspdraw.goto(-160, 40)
    if min(lastspdlim, zusatz_lastspdlim) < curspeed:
        xspdraw.pencolor('orange')
    else:
        if DARK:
            xspdraw.pencolor('green2')
        else:
            xspdraw.pencolor('green')
    smj = str(min(lastspdlim, zusatz_lastspdlim))
    if lbdisp > 0:
        smj += "/" + str(lbdisp)
        if curspeed < lbdisp:
            xspdraw.pencolor('maroon1')
    xspdraw.write(smj,align='center',font=FONT)

def gtcs3_init(noload=False):
    global LEVEL
    if LEVEL == 3:
        return
    LEVEL = 3
    if not noload:
        gtcs3_load()

def gtcs3_exit(level=1):
    global LEVEL
    if LEVEL < level:
        return
    LEVEL = level
    lkj_draw('white')
    #turtle2.clear()
    if LEVEL == 1:
        limdraw.clear()
        limdraw.hideturtle()
        xspdraw.clear()
    start_sound("gexit")

# GTCS renderer
def render_gtcs():
    global curspeed, spdlim, accreq, gtcsinfo, sysinfo, thrust
    turtle.clear()
    turtle.penup()
    turtle.goto(-160, 0)
    turtle.pendown()
    turtle.circle(80)
    turtle.penup()
    # Set number indications
    turtle.goto(-160, 0)
    #turtle.circle(80, -60)
    for i in range(0, 300, 60):
        turtle.circle(80, -60)
        turtle.write(str(i//2),font=FONT)
    turtle.right(turtle.heading())
    #turtle.circle(80, -60)
    turtle.goto(160, 0)
    turtle.pendown()
    turtle.circle(80)
    turtle.penup()
    turtle.goto(160, 0)
    #turtle.circle(80, -60)
    for i in range(0, 300, 60):       
        turtle.circle(80, -60)
        turtle.write(str(abs(i-120)//2),font=FONT)
    #turtle.left(90)
    if LEVEL >= 3:
        gtcs3_init(True)
    # Also available for GTCS-1 now
    turtle2.clear()
    turtle2.penup()
    turtle2.goto(-300, 0)
    for i in range(0,200,20):
        turtle2.goto(-300, i)
        turtle2.write(str(i*20),font=FONT)
    render_bar()
    spdturtle.goto(-160, 80)
    thrturtle.goto(160, 80)
    infobar.goto(-160, -120)
    turtle.update()

# 'Yellow-2' requires special operations
# at (-200, 200) by default, size 20.
def lkj_draw(col1,col2=""):
    lkjdraw.clear()
    lkjdraw.penup()
    lkjdraw.right(lkjdraw.heading())
    lkjdraw.goto(-200, 200)
    if col2 == "":
        lkjdraw.pendown()
        lkjdraw.fillcolor(col1)
        lkjdraw.begin_fill()
        lkjdraw.circle(20)
        lkjdraw.end_fill()
    else:
        lkjdraw.penup()
        lkjdraw.goto(-220, 220)
        lkjdraw.fillcolor(col2)
        lkjdraw.right(90)
        lkjdraw.pendown()
        lkjdraw.begin_fill()
        lkjdraw.circle(20, 180)
        lkjdraw.end_fill()
        lkjdraw.goto(-220, 220)
        lkjdraw.goto(-180, 220)
        lkjdraw.fillcolor(col1)
        lkjdraw.begin_fill()
        lkjdraw.circle(20, 180)
        lkjdraw.end_fill()

prelkj = "?"
gfailind = False

def render_gtcs_main():
    global gfailind, prelkj, light, caccel, prereded, curspeed, acreqspd, spdlim, lastspdlim, accreq, gtcsinfo, sysinfo, thrust, eb, nextdist, failures, zusatz_lastspdlim
    #print("GTCS Renderer")
    gaspress.clear()
    acreqer.hideturtle()
    acreqer.goto(-160, 0)
    spdhint.clear()
    spdhint.penup()
    # 5 radius differ
    spdhint.goto(-160, 0)
    if light[3]:
        maxspder.pencolor('red')
        acreqer.pencolor('red')
    else:
        maxspder.pencolor('orange')
        acreqer.pencolor('orange')
    maxspder.clear()
    acreqer.clear()
    spdturtle.clear()
    thrturtle.clear()
    maxspder.clear()
    spdturtle.left(210)
    maxspder.left(210)
    thrturtle.left(90)
    # Generate speed info
    # Generate thrust
    spdturtle.pendown()
    spdturtle.right(curspeed*2)
    spdturtle.forward(75)
    spdturtle.penup()
    if LEVEL >= 2:
        gtcs3_load()
    spdraw.clear()
    maxspder.pendown()
    maxspder.right(spdlim*2)
    maxspder.forward(75)
    maxspder.penup()
    acreqer.right(acreqer.heading())
    acreqer.circle(80, 60 + (120-curspeed)*2)
    #acreqer.right(accreq/4)
    acreqer.pendown()
    if (acreqspd) < curspeed:
        wacreqspd = curspeed + accreq * (20 * 3.6)
        if wacreqspd < min(spdlim, lastspdlim, zusatz_lastspdlim):
            wacreqspd = min(spdlim, lastspdlim, zusatz_lastspdlim)
        acreqer.circle(80, (wacreqspd-curspeed)*(-2))
    acreqer.left(90)
    acreqer.penup()
    spdhint.right(spdhint.heading())
    spdhint.circle(80, 60 + (120-curspeed)*2)
    spdhint.pendown()
    cspdexp = curspeed + (caccel*100)
    if cspdexp > 120:
        cspdexp = 120
    elif cspdexp < 0:
        cspdexp = 0
    # debug
    #print(cspdexp)
    spdhint.circle(80, (cspdexp-curspeed)*(-2))
    spdhint.left(90)
    spdhint.penup()
    thrturtle.pendown()
    thrturtle.right(thrust)
    thrturtle.forward(75)
    thrturtle.penup()
    spdraw.goto(-160, 70)
    spdraw.fillcolor('white')
    spdraw.pencolor('black')
    spdraw.pendown()
    spdraw.begin_fill()
    spdraw.circle(20)
    spdraw.end_fill()
    spdraw.penup()
    spdraw.goto(-160, 80)
    #spdraw.
    spdraw.write(str(int(curspeed)),align='center',font=FONT)
    infobar.clear()
    if thrust >= 0:
        gaspress.write("600",align='center',font=FONT)
    else:
        gpress = max(0, int(600+(power*6.4) - 5 + random.randint(0, 10)))
        if gpress > 600:
            gpress = 600
        if gpress < 100:
            if not gfailind:
                gfailind = True
                start_sound("braking")
        else:
            gfailind = False
        gaspress.write(str(gpress),align='center',font=FONT)
    # Generate info
    for i in failures:
        if failures[i][1] or (failures[i][2]()):
            gtcsinfo.append([failures[i][0], "maroon1"])
    for i in gtcsinfo:
        if DARK and i[1] == "blue":
            i[1] = "cyan"
        infobar.pencolor(i[1])
        infobar.pendown()
        infobar.write(i[0],font=FONT)
        infobar.penup()
        infobar.goto(infobar.xcor(), infobar.ycor()-30)
    infobar.goto(120, -120)
    for i in sysinfo:
        infobar.pencolor(i[1])
        infobar.pendown()
        infobar.write(i[0],font=FONT)
        infobar.penup()
        infobar.goto(infobar.xcor(), infobar.ycor()-30)
    if curlkj == "0" or curlkj == "00":
        if curlkj == "00" or prereded:
            lkj_draw("red")
            start_sound("red")
        else:
            lkj_draw("red", "yellow")
    elif curlkj == "1":
        lkj_draw('yellow')
    elif curlkj in "<>":
        lkj_draw('yellow', 'yellow')
    elif curlkj == "2":
        lkj_draw('green', 'yellow')
    elif curlkj == "@":
        lkjdraw.color('white')
        lkj_draw('yellow')
        lkjdraw.penup()
        lkjdraw.goto(-200,215)
        lkjdraw.color('black')
        lkjdraw.write("2",font=FONT)
    elif curlkj in "34567":
        lkj_draw('green')
    else:
        lkj_draw('white')
    if prelkj != curlkj:
        prelkj = curlkj
        if curlkj == "0" or curlkj == "00":
            if not (curlkj == "00" or prereded):
                start_sound("red-yellow")
        elif curlkj == "1":
            start_sound("yellow")
        elif curlkj in "<>":
            start_sound("double-yellow")
        elif curlkj == "2":
            start_sound("green-yellow")
        elif curlkj == "@":
            start_sound("yellow2")
        elif curlkj in "34567":
            start_sound("green")

    lkjdraw.penup()
    maxspder.right(maxspder.heading())
    spdturtle.right(spdturtle.heading())
    thrturtle.right(thrturtle.heading())
    spdturtle.goto(-160, 80)
    spdraw.goto(-160, 80)
    maxspder.goto(-160, 80)
    acreqer.showturtle()
    thrturtle.goto(160, 80)
    infobar.goto(-160, -120)
    lkjdraw.goto(-200, 200)
    render_bar()
    render_route()
    turtle.update()
    turtle.ontimer(render_gtcs_main, 200)

def kup():
    global power, thrust
    #print("Keyup")
    if power > 120:
        return
    power = (power//10)*10+10

def kdn():
    global power, thrust
    #print("Keydn")
    if power < -70:
        return
    power = (power//10)*10-10

def ksupp():
    global accreq, spdlim, lastspdlim, on_keyboard
    if on_keyboard:
        keyboard_add('8')
        return
    if not light[9]:
        gtcs3_exit()
        accreq = 0
        spdlim = 40
        light[2] = False
        light[3] = False
        lastspdlim = 120
    light[9] = not light[9]

acreqspd = 160
accuer = 0
limitz = []
caccel = 0
contnz = 0
plog = []
tcnter1 = 0

def physics():
    global lastspdlim, tcnter1, plog, contnz, caccel, limitz, accuer, curspeed, thrust, gtcsinfo, accreq, power, acreqspd, LEVEL, schutz, schutz_info, sysinfo, zusatz_lastspdlim
    if power < 0 or curspeed < 20:
        thrust = power / 2
    else:
        thrust = power / (curspeed / 10)
    thrust -= 10
    accuer += (curspeed / 3.6) * 0.2
    caccel = thrust / 50
    curspeed += thrust / 50
    if (thrust > 0) and light[1]:
        tcnter1 += 1
        if tcnter1 > 20:
            light[1] = False
            tcnter1 = 0
    else:
        tcnter1 = 0
    if curspeed < 0:
        curspeed = 0
    if power < 0:
        tcolor[4] = "red"
        tcolor[5] = "red"
    else:
        tcolor[4] = "green"
        tcolor[5] = "green"

    light[4] = (abs(power) > 0)
    light[5] = (abs(power) > 30)
    light[6] = (power < -40)
    
    gtcsinfo = []
    if light[9]:
        gtcsinfo = [["GTCS-1 Overridden", "blue"]]
    else:
        if spdlim < 120:
            gtcsinfo = [["GTCS-"+str(LEVEL)+" speed limit " + str(spdlim) + " km/h", "orange"]]
        cspdlim = spdlim
        #light[3] = False
        cacreqspd = acreqspd
        if curspeed > spdlim:
            #if len(limitz) >= 10:
            #cacreqspd = max(acreqspd,limitz[0] + 5)
            #    if len(limitz) > 10:
            #        limitz = limitz[1:]
            #if cacreqspd < 120:
            #    gtcsinfo.append(["GTCS-"+str(LEVEL)+" deflection " + str(int(cacreqspd)) + " km/h","orange"])
            #gtcsinfo.append(["Acceleration " + str(round(accreq,2)),"orange"])
            if accreq < -1.5:
                gtcsinfo.append(["Deflect now", "orange"])
                start_sound("deflect")
            light[2] = True
        if ((LEVEL >= 2) and curspeed > (cacreqspd + 3)) and (accreq < -2):
            contnz += 0.5
        if (LEVEL <= 1) and (contnz > 12):
            light[3] = True
        if (contnz > 50) or (accreq < -8):
            light[3] = True
            plog.append(time.ctime() + " GTCS: vcac = " + str(round(cacreqspd, 2)) + ", cntz = " + str(contnz))
        ccspdlim = min(spdlim, lastspdlim, zusatz_lastspdlim)
        if (LEVEL <= 1) and (curspeed > ccspdlim):
            if (curspeed - ccspdlim > 80):
                accreq = -12
                contnz += 1
            elif (curspeed - ccspdlim > 60):
                accreq = -6
                contnz += 0.5
            elif curspeed > ccspdlim:
                accreq = -4
                contnz += 0.25
        if (curspeed < lastspdlim) and (curspeed < spdlim):
            accreq = 0
            contnz = 0
            light[2] = False
            light[3] = False
        if (accreq >= 0):
            acreqspd = 160
        else:
            acreqspd = curspeed + accreq * (2 * 3.6)
            if acreqspd < 0:
                acreqspd = 0
            if acreqspd < min(lastspdlim,spdlim):
                acreqspd = min(lastspdlim,spdlim)
        if schutz:
            light[3] = True
            gtcsinfo.append([schutz_info, "red"])
        #limitz.append(acreqspd)
        #gtcsinfo = []
        if light[3]:
            if thrust >= -40:
                if curspeed > 60 and power < 0:
                    power -= 4
                else:
                    power -= 10
            if schutz:
                gtcsinfo.append(["Schutzbremsung", "red"])
                start_sound("schutz")
            else:
                gtcsinfo.append(["Zwangsbremsung", "red"])
                start_sound("zb")
    turtle.ontimer(physics, 200)

### TODO: Use requests library.

def test1():
    global spdlim
    spdlim -= 1

def test2():
    global spdlim
    spdlim += 1

def test3():
    global accreq
    accreq -= 1

def test4():
    global accreq
    accreq += 1
    
befehltext = ""
bns = ""
befconf = False

keyboard = ""
on_keyboard = False
next_keyboard = lambda: None

def befshow(bcset=False):
    global bns, befehltext, befconf, keyboard, on_keyboard
    befehldisp.clear()
    befehldisp.goto(-160, 240)
    bs = befehltext.split("\n")
    bs.append(bns)
    if on_keyboard:
        bs.append(keyboard)
    for i in bs:
        befehldisp.write(i,font=FONT)
        befehldisp.goto(-160, befehldisp.ycor()-15)
    if bcset:
        befconf = True

def keyboard_add(char):
    global keyboard, on_keyboard
    if on_keyboard:
        keyboard += char
        befshow()

def befshow2():
    global on_keyboard
    if on_keyboard:
        keyboard_add('7')
        return
    befshow(True)

def befclr():
    global befehltext, on_keyboard
    if on_keyboard:
        keyboard_add('8')
        return
    befehldisp.clear()

def locupd():
    tloc = turtle.textinput("GTCS", "Input current location:")
    if tloc != "":
        update_loc(tloc)

def schutz_cancel():
    global schutz, on_keyboard, ps_queue
    if on_keyboard:
        keyboard_add('5')
        return
    schutz = False
    light[3] = False
    ps_queue.clear()

def locshow():
    global zugat, befehltext, on_keyboard
    if on_keyboard:
        keyboard_add('6')
        return
    befehltext = "Current location: " + zugat
    befshow()

def change_loc_nxstep():
    global keyboard, on_keyboard, next_keyboard
    update_loc(keyboard)
    on_keyboard = False
    next_keyboard = lambda: None
    befclr()

def change_loc():
    global bns, on_keyboard, next_keyboard, gauto
    if on_keyboard:
        keyboard_add('4')
        return
    keyboard = ""
    bns = "Input new location:"
    next_keyboard = change_loc_nxstep
    gauto = True
    on_keyboard = True
    befshow()

t.screen.onkey(kup, 'Up')
t.screen.onkey(kdn, 'Down')
t.screen.onkey(ksupp, '9')
t.screen.onkey(befclr, '8')
# Also for confirmation.
t.screen.onkey(befshow2, '7')
t.screen.onkey(locshow, '6')
t.screen.onkey(schutz_cancel, '5')
t.screen.onkey(change_loc, '4')

def wind_charge():
    global apress, on_keyboard
    if on_keyboard:
        keyboard_add('o')
        return
    apress += random.randint(50,150)/10

def wind_release():
    global apress, on_keyboard
    if on_keyboard:
        keyboard_add('p')
        return
    apress -= random.randint(50,150)/10
    if apress < 0:
        apress = 0

def elec_charge():
    global eamps, evolts, on_keyboard
    if on_keyboard:
        keyboard_add('k')
        return
    evolts += random.randint(10,30)
    eamps += random.randint(10,30)/20

def elec_release():
    global eamps, evolts, on_keyboard
    if on_keyboard:
        keyboard_add('l')
        return
    evolts -= random.randint(10,30)
    eamps -= random.randint(10,30)/20
    if evolts < 0:
        evolts = 0
    if eamps < 0:
        eamps = 0
        
def swtc_pwr():
    global cpsrc, on_keyboard
    if on_keyboard:
        keyboard_add('a')
        return
    if cpsrc == "a":
        cpsrc = "e"
    else:
        cpsrc = "a"

def panto_swtc():
    global cpsrc, on_keyboard
    if on_keyboard:
        keyboard_add('s')
        return
    cpsrc = "p"
    
def name_disp():
    global show_name, on_keyboard
    if on_keyboard:
        keyboard_add('0')
        return
    show_name = not show_name

t.screen.onkey(wind_charge, 'o')
t.screen.onkey(wind_release, 'p')
t.screen.onkey(elec_charge, 'k')
t.screen.onkey(elec_release, 'l')
t.screen.onkey(swtc_pwr, 'a')
t.screen.onkey(panto_swtc, 's')

t.screen.onkey(name_disp, '0')

def syspage_switch(ckey):
    global csyspage, on_keyboard
    if on_keyboard:
        keyboard_add(ckey)
        return
    csyspage = ckey

for i in syspages:
    t.screen.onkey(eval("lambda: syspage_switch('{}')".format(i)), i)

for i in '123tyuidfghjzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM':
    t.screen.onkey(eval("lambda: keyboard_add('{}')".format(i)), i)

t.screen.onkey(lambda: keyboard_add('_'), ',')

def discard_keyboard():
    global on_keyboard, keyboard, next_keyboard
    on_keyboard = False
    keyboard = ""
    next_keyboard = lambda: None
    befclr()

def proceed_keyboard():
    global on_keyboard, keyboard, next_keyboard
    next_keyboard()

t.screen.onkey(discard_keyboard, '.')
t.screen.onkey(proceed_keyboard, '/')

t.screen.listen()

def translate(signal):
    cspdlim = 0
    if signal == "." or signal == "|":
        cspdlim = 120
    elif signal == "/" or signal == "<" or signal == ">":
        cspdlim = 60
    elif signal.isdigit():
        cspdlim = (int(signal))*10
    else:
        cspdlim = 0
    if cspdlim > 120:
        return 120
    return cspdlim

autog3 = True
ospeed = spdlim
geschw = 120

def update_loc(target):
    global geschw, curlkj, prereded, accuer, lastspdlim, g3err, LEVEL, zugat, spdlim, accreq, ZUGNAME, autog3, ospeed, AUTH
    try:
        if zugat != "":
            u = urlopen(ZCTR + "?sid=" + zugat + "&type=1&name=" + ZUGNAME + "&auth=" + AUTH)
            u.read()
            u.close()
        u = urlopen(SCTR + "?sid=" + target)
        su = u.read().decode('utf-8')
        u.close()
        #print("Full text:",su)
        sus = su.strip()
        signal = "0"
        if len(sus) > 1:
            signal = sus[:2]
        else:
            signal = sus[0]
        g3err.append(time.ctime() + " GTCS-1: Receiving signal " + str(signal))
        cspdlim = translate(signal)
        if cspdlim == 0:
            prereded = True
        else:
            prereded = False
        if LEVEL <= 1:
            spdlim = cspdlim
            if spdlim > ospeed:
                light[1] = True
            elif spdlim < ospeed:
                light[1] = False
            ospeed = spdlim
        lastspdlim = cspdlim
        geschw = cspdlim
        zugat = target
        if LEVEL <= 1:
            accuer = 0
        elif LEVEL >= 2:
            accuer = 1
        if autog3:
            gtcs3_init()
            autog3 = False
        u = urlopen(LCTR + "?sid=" + zugat)
        su = u.read().decode('utf-8')
        u.close()
        curlkj = su
        u = urlopen(ZCTR + "?sid=" + target + "&type=0&name=" + ZUGNAME + "&auth=" + AUTH)
        u.read()
        u.close()
    except Exception as e:
        print("Error:",str(e))
        spdlim = 0

g3err = []

GLOGGING = False
PLOGGING = False

def schutz_broadcast(info):
    global schutz, schutz_info
    schutz = True
    schutz_info = info


def console():
    global SCHUTZ_PROB, SCHUTZ_SIMU, SCTR, ZCTR, DCTR, BCTR, LCTR, ICTR, GLOGGING, PLOGGING, plog, ZUGNAME, spdlim, zugat, gtcsinfo, accreq, acreqspd, thrust, accuer, LEVEL, g3err, autog3, failures
    while True:
        ip = input(">>> ")
        cmd = ip.split(" ")
        if len(cmd) < 1:
            print("Invalid command - too short")
            continue
        if cmd[0] == "at":
            #zugat = cmd[1]
            if len(cmd) < 2:
                print("Invalid at command")
                continue
            update_loc(cmd[1])
            print("Successfully updated location")
        elif cmd[0] == "ren":
            if len(cmd) < 2:
                print("Current name",ZUGNAME)
                continue
            ZUGNAME = cmd[1]
            print("Successfully updated name")
        elif cmd[0] == "gi":
            if len(cmd) < 2:
                print("Invalid at command")
                continue
            if cmd[1] == "0":
                print(gtcsinfo)
            elif cmd[1] == "1":
                print(spdlim)
            elif cmd[1] == "2":
                print(acreqspd)
            elif cmd[1] == "2a":
                print(accreq)
            elif cmd[1] == "3":
                print(thrust)
            elif cmd[1] == "4":
                print(accuer)
            elif cmd[1] == "5":
                print(curlkj)
            elif cmd[1] == "6":
                print(maxthr_val())
        elif cmd[0] == "glog":
            print("Currently GTCS",LEVEL)
            print("\n".join(g3err))
        elif cmd[0] == "gclr":
            g3err = []
        elif cmd[0] == "plog":
            print("\n".join(plog))
        elif cmd[0] == "pclr":
            plog = []
        elif cmd[0] == "genter":
            if zugat.strip() == "":
                print("No initial position information")
            else:
                gtcs3_init()
        elif cmd[0] == "gexit":
            if (len(cmd) > 1) and (cmd[1].isdigit()):
                print("Quit to special GTCS-{}".format(cmd[1]))
                gtcs3_exit(int(cmd[1]))
            else:
                gtcs3_exit()
        elif cmd[0] == "gauto":
            autog3 = not autog3
            print("GTCS-3 automatic activate is now",autog3)
        elif cmd[0] == "sset":
            if len(cmd) < 2:
                print("Invalid at command")
                continue
            spdlim = int(cmd[1])
        elif cmd[0] == "glstat":
            GLOGGING = not GLOGGING
            print("GLog is now",GLOGGING)
        elif cmd[0] == "plstat":
            PLOGGING = not PLOGGING
            print("PLog is now",GLOGGING)
        elif cmd[0] == "ip":
            if len(cmd) < 2:
                print("Invalid ip command")
                continue
            SCTR="http://{ip}:5033/signal".format(ip=cmd[1])
            ZCTR="http://{ip}:5033/zug".format(ip=cmd[1])
            DCTR="http://{ip}:5033/zugdist".format(ip=cmd[1])
            BCTR="http://{ip}:5033/befehl".format(ip=cmd[1])
            LCTR="http://{ip}:5033/lkjdisp".format(ip=cmd[1])
            ICTR="http://{ip}:5033/signaldata".format(ip=cmd[1])
        elif cmd[0] == "schutz":
            if len(cmd) < 2:
                SCHUTZ_SIMU = not SCHUTZ_SIMU
                print("Schutz simulator is now",SCHUTZ_SIMU)
            else:
                if cmd[1].isdigit():
                    SCHUTZ_PROB = int(cmd[1])
                    print("Schutz probability is now",SCHUTZ_PROB)
                else:
                    schutz_broadcast(cmd[1])
        elif cmd[0] == "failmgmt":
            if len(cmd) < 2:
                for i in failures:
                    failures[i][1] = False
                print("All failures cleared")
            else:
                try:
                    failures[cmd[1]][1] = not failures[cmd[1]][1]
                    print("Failure item '{}' is configured to".format(failures[cmd[1]][0]),failures[cmd[1]][1])
                except Exception as e:
                    print("Unable to configure",e)
        else:
            print("Invalid command")

def accelreq(spdlim, sd):
    global curspeed, caccel
    raw = 0
    if curspeed > spdlim:
        if sd > 100:
            raw = (((spdlim/3.6)**2 - ((curspeed + max(0,caccel+0.2) * 3)/3.6)**2)/(2*(sd-100)))
            if sd < 500:
                raw -= 0.25
            elif sd < 1200:
                raw -= 0.15
            elif sd < 2000:
                raw -= 0.1
        else:
            raw = -4
    return raw

def gtcs3():
    global lbdisp, passdz, geschw, lastseg, furseg, extcmd, LCTR, curlkj, lastspdlim, g3err, accuer, curspeed, caccel, nextdist, spdlim, accreq, acreqspd, zugat, ospeed, zusatz_lastspdlim
    while True:
        # Load actual special command
        zusatz_spdlim = 300
        zusatz_spdlim_at = 10000000
        tmpz = 300
        tmplb = 0
        last_cancel = -100000
        last_fcancel = 100000
        pass_p0 = -100000
        pass_p1 = -99999
        try:
            # Resolve actual information:
            if (zugat != "") and (zugat != "?"):
                u = urlopen(ICTR + "?sid=" + zugat + "&dev=" + str(int(accuer)))
                extinf = u.read().decode('utf-8')
                u.close()
                extcmd = extinf.split("\n")
                remdis = int(extcmd[0])
                sname = "?"
                esc = extcmd[1:]
                for i in esc:
                    csp = i.split(" ")
                    dis = int(csp[0])
                    if csp[1] == "S" and sname == "?":
                        sname = csp[2]
                    elif csp[1] == "Le":
                        if dis < 0:
                            last_cancel = max(last_cancel, dis)
                        else:
                            last_fcancel = min(last_fcancel, dis)
                    elif csp[1] == "P0":
                        if dis < 0:
                            pass_p0 = max(pass_p0, dis)
                    elif csp[1] == "P1":
                        if dis < 0:
                            pass_p1 = max(pass_p1, dis)
                passdz = (pass_p0 >= pass_p1)
                for i in esc:
                    csp = i.split(" ")
                    if csp[1] == "La":
                        dis = int(csp[0])
                        if dis < 0:
                            if dis > last_cancel:
                                tmpz = min(tmpz, int(csp[3]))
                                tmplb = max(tmplb, int(csp[2]))
                        else:
                            if dis < last_fcancel and int(csp[3]) <= zusatz_spdlim:
                                zusatz_spdlim = int(csp[3])
                                zusatz_spdlim_at = min(zusatz_spdlim_at, dis)
                lbdisp = tmplb
                zusatz_lastspdlim = tmpz
                if LEVEL == 1:
                    if remdis <= 0:
                        accuer = 0
                        update_loc(sname)
        except Exception as e:
            g3err.append(time.ctime() + " GTCS-3: [To gtcs-2]" + str(e))
            gtcs3_exit(2)
        
        # Tackle with:
        # 1. Neutral area
        # 2. Speed limits
        # (for display, let gtcs loader tackle)
        if LEVEL >= 2:
            #print("Toggle#")
            try:
                u = urlopen(DCTR + "?sid=" + zugat + "&dev=" + str(int(accuer)) + "&spd=" + str(int(geschw)))
                su = u.read().decode('utf-8')
                u.close()
                sr = su.split(" ")
                sd = int(sr[0])
                if sd <= 0:
                    #lastspdlim = spdlim
                    accuer = 0
                    update_loc(sr[2])
                else:
                    spdlim = translate(sr[1])
                    if spdlim > ospeed:
                        light[1] = True
                    elif spdlim < ospeed:
                        light[1] = False
                    ospeed = spdlim
                    # Dynamic value already.
                    #if (zusatz_spdlim <= spdlim) or (zusatz_spdlim_at <= sd):
                    #    spdlim = zusatz_spdlim
                    #    sd = zusatz_spdlim_at
                    # 2s speed monitor, but acceleration here, unit: m/s^2
                    raw = accelreq(spdlim, sd)
                    for i in extcmd[1:]:
                        csp = i.split(" ")
                        dis = int(csp[0])
                        if csp[1] == "S":
                            if LEVEL >= 3:
                                cslim = translate(csp[3])
                                cac = accelreq(cslim, dis)
                                if cac < raw:
                                    raw = cac
                                    sd = dis
                                    spdlim = cslim
                        elif csp[1] == "La":
                            if (dis < last_fcancel) and (dis > 0):
                                cac = accelreq(int(csp[3]), dis)
                                if cac < raw:
                                    raw = cac
                                    sd = dis
                                    spdlim = int(csp[3])
                    #if sd > 3500:
                    #    raw = 0
                    clastspdlim = min(lastspdlim, zusatz_lastspdlim)
                    if (curspeed > clastspdlim):
                        if (curspeed - clastspdlim > 80):
                            raw = min(raw,-12)
                            #contnz += 1
                        elif (curspeed - clastspdlim > 60):
                            raw = min(raw,-6)
                            #contnz += 0.5
                        else:
                            raw = min(raw,-4)
                            #contnz += 0.25
                    g3err.append(time.ctime() + " GTCS-3: Raw acceleration " + str(round(raw,2)) + ", with vacr = " + str(round(acreqspd,2)))
                    accreq = min(0,raw)
                    #acreqspd = curspeed + (max(0,caccel+0.2) * 3) + accreq * (2 / 3.6)
                    #acreqspd = curspeed + accreq * (2 * 3.6)
                    if acreqspd < 0:
                        acreqspd = 0
                    nextdist = sd
                    if zugat != sr[3]:
                        accuer = 1
                        update_loc(sr[3])
                u = urlopen(LCTR + "?sid=" + zugat)
                su = u.read().decode('utf-8')
                u.close()
                curlkj = su
                if lastspdlim <= 0:
                    curlkj = "00"
                    prereded = True
                #print("Accumulate",accuer,nextdist)
            except Exception as e:
                g3err.append(time.ctime() + " GTCS-3:" + str(e))
                gtcs3_exit()
        
        time.sleep(2)

def logclr():
    global GLOGGING, PLOGGING, g3err, plog, SCHUTZ_SIMU, SCHUTZ_PROB, failures, curspeed

    SCHUTZ_AFFAIR = ["Hilichurlwarnung", "Slimenwarnung", "Eisenbahnfaulwarnung", "Unerwartetelementwarnung", "Abyssmagewarnung"]

    while True:
        if not GLOGGING:
            g3err = []
        if not PLOGGING:
            plog = []
        if SCHUTZ_SIMU:
            if not schutz:
                if random.randint(0, 1000) < SCHUTZ_PROB:
                    rc = random.choice(SCHUTZ_AFFAIR)
                    schutz_broadcast(rc)
                    if rc == "Unerwartetelementwarnung":
                        rw = random.choice(["ovldr", "scond", "eblock"])
                        failures[rw][1] = True
        if (curspeed > 15) and (maxthr_val() < 10):
            start_sound("thrust")
        time.sleep(5)
        

def befread():
    global g3err, BCTR, AUTH, befehltext, befconf, ZUGNAME
    while True:
        try:
            u = urlopen(BCTR + "?auth=" + AUTH + "&mode=get&name=" + ZUGNAME)
            su = u.read().decode('utf-8').strip()
            u.close()
            moded = False
            if su != befehltext:
                befconf = False
                moded = True
            befehltext = su
            if befconf:
                befconf = False
                u = urlopen(BCTR + "?auth=" + AUTH + "&mode=confirm&name=" + ZUGNAME)
                u.close()
            if moded:
                befshow()
        except Exception as e:
            g3err.append(time.ctime() + " GTCS Befehl: " + str(e))
        time.sleep(2)

def gsmgmt():
    global failures, power, SCHUTZ_PROB, apress, evolts, eamps, efreq, sysinfo, syspages, csyspage, cpsrc, passdz
    while True:
        if random.randint(0, 35000) < SCHUTZ_PROB:
            rf = random.choice(list(failures))
            failures[rf][1] = not failures[rf][1]
        # Failure effects
        if failures["thr"][1]:
            if power > 0:
                power -= min(power, 5)
        if failures["brk"][1]:
            if power < 0:
                power += min(-power, 5)
        if failures["apwrlo"][1]:
            if apress > 10:
                apress -= random.randint(10,40)/10
        if failures["apwrhi"][1]:
            if apress < 200:
                apress += random.randint(10,40)/10
        if failures["epwrlo"][1] or failures["eblock"][1]:
            if evolts > 10:
                evolts -= random.randint(10,40)/10
        if failures["epwrhi"][1] or failures["ovldr"][1]:
            if evolts < 3000:
                evolts += random.randint(10,40)/10
        if failures["epwrslo"][1] or failures["eblock"][1]:
            if eamps > 0.1:
                eamps -= random.randint(10,40)/10
        if failures["epwrshi"][1] or failures["scond"][1]:
            if eamps < 100:
                eamps += random.randint(10,40)/20
        sysinfo = []
        for i in syspages[csyspage]:
            sysinfo.append([i[0](), i[1]()])
        if cpsrc == "p":
            if passdz:
                evolts = 0
                eamps = 0
            else:
                evolts = 2500
                eamps = 80
        apress += (random.randint(0,10)-5)/10
        evolts += (random.randint(0,10)-5)/10
        eamps += (random.randint(0,10)-5)/50
        if apress < 0:
            apress = 0
        if evolts < 0:
            evolts = 0
        if eamps < 0:
            eamps = 0
        pmc = maxthr_val()
        if power > pmc:
            power -= min(power-pmc, random.randint(10,30))
        #power = min(power, maxthr_val())
        time.sleep(0.1)

#turtle.right(90)
render_gtcs()
turtle.ontimer(render_gtcs_main, 100)
turtle.ontimer(physics, 200)
th = threading.Thread(target=console)
t3 = threading.Thread(target=gtcs3)
tl = threading.Thread(target=logclr)
tb = threading.Thread(target=befread)
tsh = threading.Thread(target=sound_thr)
tgs = threading.Thread(target=gsmgmt)
th.start()
t3.start()
tl.start()
tb.start()
tsh.start()
tgs.start()
turtle.mainloop()
#print(turtle.heading())
#input()
#render_bar()