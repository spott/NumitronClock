#!/usr/bin/env python3
"""Create the initial, editable KiCad schematic. Explicit --write prevents accidental overwrite.

The .kicad_sch files are the design deliverables and can be edited normally in KiCad.
This script records the initial capture; do not rerun over later GUI edits.
All coordinates use KiCad's 1.27 mm grid. No third-party Python dependencies.
"""
from pathlib import Path
import argparse
import json
import math
import uuid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/top-board"
NS = uuid.UUID("ba7d337f-8b04-4a0b-bdbd-4e5c73e208d5")
def uid(name): return str(uuid.uuid5(NS, name))
def q(s): return json.dumps(str(s), ensure_ascii=False)
def n(v): return f"{v:.5f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)
def xy(x, y): return f"{n(x)} {n(y)}"
def fx(size=1.27, justify="", hide=False):
    return f'(effects (font (size {size} {size})) {"(justify " + justify + ")" if justify else ""} {"hide" if hide else ""})'
def prop(key, val, x=0, y=0, hide=True, justify="", angle=0):
    return f'(property {q(key)} {q(val)} (at {xy(x,y)} {angle}) {fx(1.27,justify,hide)})'
def line(a,b,width=.254):
    return f'(polyline (pts (xy {xy(*a)}) (xy {xy(*b)})) (stroke (width {width}) (type default)) (fill (type none)))'
def rect(x1,y1,x2,y2):
    return f'(rectangle (start {xy(x1,y1)}) (end {xy(x2,y2)}) (stroke (width 0.254) (type default)) (fill (type background)))'

LIB = {}
def symbol(name, pins, graphics, ref="U", footprint="", datasheet="", desc=""):
    """Pin tuple: number, name, electrical type, x, y, orientation, optional shape."""
    pintext=[]
    for p in pins:
        num, pname, typ, x, y, angle, *shape = p
        pintext.append(f'(pin {typ} {shape[0] if shape else "line"} (at {xy(x,y)} {angle}) (length 2.54) '
                       f'(name {q(pname)} {fx(1.016)}) (number {q(num)} {fx(1.016)}))')
    body = f'''(pin_names (offset 0.635)) (in_bom yes) (on_board yes)
      {prop("Reference",ref,0,5.08,False)} {prop("Value",name,0,-5.08,False)}
      {prop("Footprint",footprint)} {prop("Datasheet",datasheet)} {prop("Description",desc)}
      (symbol {q(name+"_0_1")} {graphics})
      (symbol {q(name+"_1_1")} {''.join(pintext)})'''
    LIB[name] = {"body":body, "pins":pins,"fp":footprint,"ds":datasheet,"desc":desc}

def setup_library():
    symbol("R", [(1,"~","passive",0,5.08,270),(2,"~","passive",0,-5.08,90)],
           rect(-1.016,2.54,1.016,-2.54),"R","Resistor_SMD:R_0603_1608Metric","${KIPRJMOD}/../../datasheets/RC0603FR-0710KL.pdf")
    symbol("C", [(1,"~","passive",0,3.81,270),(2,"~","passive",0,-3.81,90)],
           line((-2.54,.635),(2.54,.635))+line((-2.54,-.635),(2.54,-.635))+
           line((0,1.27),(0,.635))+line((0,-1.27),(0,-.635)),"C","Capacitor_SMD:C_0603_1608Metric","${KIPRJMOD}/../../datasheets/avx-x7r.pdf")
    symbol("PWR_FLAG", [(1,"pwr","power_out",0,0,90)],
           line((0,2.54),(-1.27,3.81))+line((-1.27,3.81),(0,5.08))+
           line((0,5.08),(1.27,3.81))+line((1.27,3.81),(0,2.54)),"#FLG",desc="External supply declaration for ERC")
    symbol("TestPoint", [(1,"1","passive",0,0,90)],
           '(circle (center 0 3.81) (radius 1.27) (stroke (width 0.254) (type default)) (fill (type none)))',
           "TP","TestPoint:TestPoint_Pad_D1.5mm",desc="Bare PCB test pad")
    symbol("AP7361C_Y5",[(4,"IN","power_in",-10.16,5.08,0),(1,"EN","input",-10.16,0,0),
           (5,"OUT","power_out",10.16,5.08,180),(3,"ADJ","input",10.16,0,180),(2,"GND","power_in",0,-7.62,90)],
           rect(-7.62,7.62,7.62,-5.08),footprint="Package_TO_SOT_SMD:SOT-89-5",
           datasheet="${KIPRJMOD}/../../datasheets/AP7361C.pdf",desc="Adjustable LDO; SOT89-5 pinout, tab = pin 2 GND")
    pins=[]
    for i,(a,y,oe) in enumerate([(2,3,1),(5,6,4),(9,8,10),(12,11,13)]):
        pos=12.7-i*7.62
        pins += [(a,f"{i+1}A","input",-15.24,pos,0),(y,f"{i+1}Y","tri_state",15.24,pos,180),
                 (oe,f"~{{{i+1}OE}}","input",-15.24,pos-2.54,0)]
    pins += [(14,"VCC","power_in",0,20.32,270),(7,"GND","power_in",0,-20.32,90)]
    symbol("74AHCT125",pins,rect(-12.7,17.78,12.7,-17.78),footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
           datasheet="${KIPRJMOD}/../../datasheets/sn74ahct125.pdf",desc="Four independent non-inverting TTL-input buffers, 5 V supply")
    symbol("MMBT3904",[(1,"B","input",-7.62,0,0),(3,"C","passive",2.54,7.62,270),(2,"E","passive",2.54,-7.62,90)],
           line((-5.08,0),(-1.27,0))+line((-1.27,3.81),(-1.27,-3.81))+line((-1.27,1.905),(2.54,5.08))+
           line((-1.27,-1.905),(2.54,-5.08))+line((2.54,-5.08),(.254,-4.445))+line((2.54,-5.08),(1.778,-2.921)),
           "Q","Package_TO_SOT_SMD:SOT-23","${KIPRJMOD}/../../datasheets/mmbt3904.pdf",desc="NPN, B=1 E=2 C=3")
    symbol("BH1750FVI",[(1,"VCC","power_in",0,12.7,270),(3,"GND","power_in",0,-12.7,90),
           (2,"ADDR","input",-12.7,-5.08,0),(5,"DVI","input",-12.7,5.08,0),
           (6,"SCL","input",12.7,5.08,180),(4,"SDA","bidirectional",12.7,0,180)],
           rect(-10.16,10.16,10.16,-10.16),datasheet="${KIPRJMOD}/../../datasheets/bh1750fvi.pdf",
           desc="Ambient light sensor; 0x23 with ADDR low; WSOF6I exposed center must NOT be soldered")
    symbol("TLV809EA29DBZ",[(3,"VDD","power_in",0,7.62,270),(1,"GND","power_in",0,-7.62,90),
           (2,"~{RESET}","output",12.7,0,180)],rect(-10.16,5.08,10.16,-5.08),
           footprint="Package_TO_SOT_SMD:SOT-23",datasheet="${KIPRJMOD}/../../datasheets/tlv809e.pdf",
           desc="2.93 V supervisor, 200 ms nominal release; normal DBZ pinout (NOT R/V variant)")
    pins=[]
    for i in range(8):
        pins += [(2*i+1,str(2*i+1),"passive",-7.62,8.89-2.54*i,0),
                 (2*i+2,str(2*i+2),"passive",7.62,8.89-2.54*i,180)]
    symbol("IDC_2x08",pins,rect(-5.08,11.43,5.08,-11.43),"J",
           "Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical","${KIPRJMOD}/../../datasheets/idc-header.pdf",
           "Wurth 61201621621; 2.54 mm PCB pin grid for 1.27 mm pitch ribbon")
    pins=[(2,"VCC","power_in",0,25.4,270),(3,"SER_IN","input",-17.78,17.78,0),
          (13,"SRCK","input",-17.78,10.16,0),(12,"RCK","input",-17.78,5.08,0),
          (9,"~{G}","input",-17.78,0,0),(8,"~{SRCLR}","input",-17.78,-5.08,0),
          (1,"NC","no_connect",-17.78,-12.7,0),(20,"NC","no_connect",-17.78,-17.78,0),
          (18,"SER_OUT","output",17.78,-12.7,180)]
    for i,p in enumerate([4,5,6,7,14,15,16,17]): pins.append((p,f"DRAIN{i}","open_collector",17.78,17.78-i*2.54,180))
    for p,x in [(10,-5.08),(11,0),(19,5.08)]: pins.append((p,"GND","power_in",x,-25.4,90))
    symbol("TPIC6B595DW",pins,rect(-15.24,22.86,15.24,-22.86),
           footprint="Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",datasheet="${KIPRJMOD}/../../datasheets/tpic6b595.pdf",
           desc="SRCK is pin 13: verified against pin diagram and application, Rev D table contains typo")

class Sheet:
    def __init__(self,name,title,page,size="A3",child_id=None):
        self.name,self.title,self.page,self.size=name,title,page,size
        self.id=uid("sheetfile:"+name)
        self.path="/"+uid("sheetfile:NumitronTop")+("/"+child_id if child_id else "")
        self.items=[]; self.used=set(); self.count=0; self.components=[]
    def uuid(self):
        self.count+=1
        return uid(self.name+":"+str(self.count))
    def wire(self,a,b):
        if a==b: return
        self.items.append(f'(wire (pts (xy {xy(*a)}) (xy {xy(*b)})) (stroke (width 0.1524) (type default)) (uuid {self.uuid()}))')
    def junction(self,p): self.items.append(f'(junction (at {xy(*p)}) (diameter 0.762) (color 0 0 0 0) (uuid {self.uuid()}))')
    def label(self,text,p,glob=False,left=False):
        kind="global_label" if glob else "label"
        extra="(shape input)" if glob else ""
        align=("right" if left else "left")+("" if glob else " bottom")
        self.items.append(f'({kind} {q(text)} {extra} (at {xy(*p)} 0) {fx(1.016,align)} (uuid {self.uuid()}))')
    def text(self,text,x,y,size=1.27):
        self.items.append(f'(text {q(text)} (at {xy(x,y)} 0) {fx(size,"left top")} (uuid {self.uuid()}))')
    def nc(self,p): self.items.append(f'(no_connect (at {xy(*p)}) (uuid {self.uuid()}))')
    def add(self,typ,ref,x,y,value=None,angle=0,fields=None,fp=None,dnp=False):
        d=LIB[typ]; self.used.add(typ); value=value or typ
        fields=dict(fields or {})
        if typ=="R":
            code={"46.4k":"46K4","10k":"10K","33R":"33R","100k":"100K","4.7k":"4K7","2.2k":"2K2","47k":"47K","1k":"1K"}[value.split()[0]]
            fields.setdefault("MPN","RC0603FR-07"+code+"L"); fields.setdefault("Manufacturer","Yageo")
        ds=("${KIPRJMOD}/../../datasheets/"+fields["MPN"]+".pdf") if typ=="R" else d["ds"]
        ident=uid("component:"+ref)
        is_flag=ref.startswith("#")
        if typ in ("R","C","MMBT3904","TestPoint","PWR_FLAG"):
            rx,ry,vx,vy=x+3.81,y-1.27,x+3.81,y+1.27
            if angle==90: rx,ry,vx,vy=x-5.08,y-3.175,x+2.54,y-3.175
        else:
            top={"AP7361C_Y5":7.62,"74AHCT125":17.78,"BH1750FVI":10.16,"TLV809EA29DBZ":5.08,"IDC_2x08":11.43,"TPIC6B595DW":22.86,"DR2000_FamilySocket":22.86}[typ]
            rx,ry,vx,vy=x+3.81,y-top-5.08,x+3.81,y-top-2.54
        ps=[prop("Reference",ref,rx,ry,is_flag,"left",angle),prop("Value",value,vx,vy,is_flag,"left",angle),
            prop("Footprint",d["fp"] if fp is None else fp),prop("Datasheet",ds),prop("Description",d["desc"])]
        for k,v in (fields or {}).items(): ps.append(prop(k,v))
        pintxt=" ".join(f'(pin {q(p[0])} (uuid {uid(ref+":"+str(p[0]))}))' for p in d["pins"])
        self.items.append(f'''(symbol (lib_id "Numitron:{typ}") (at {xy(x,y)} {angle}) (unit 1)
          (in_bom {"no" if is_flag or ref.startswith("TP") else "yes"}) (on_board {"no" if is_flag else "yes"}) (dnp {"yes" if dnp else "no"})
          (uuid {ident}) {''.join(ps)} {pintxt}
          (instances (project "NumitronTop" (path {q(self.path)} (reference {q(ref)}) (unit 1)))))''')
        a=math.radians(angle)
        result={str(p[0]): (round(x+p[3]*math.cos(a)-p[4]*math.sin(a),5),round(y-p[3]*math.sin(a)-p[4]*math.cos(a),5)) for p in d["pins"]}
        self.components.append({"ref":ref,"type":typ,"value":value,"footprint":d["fp"] if fp is None else fp,"fields":fields,"dnp":dnp,"datasheet":ds})
        return result
    def stub(self,p,net,direction="left",length=5.08,glob=False):
        dx,dy={"left":(-length,0),"right":(length,0),"up":(0,-length),"down":(0,length)}[direction]
        end=(round(p[0]+dx,5),round(p[1]+dy,5)); self.wire(p,end)
        self.label(net,end,glob,left=direction=="left")
        return end
    def rail(self,p,net,direction="up",length=5.08): return self.stub(p,net,direction,length,True)
    def passive(self,typ,ref,value,x,y,top,bottom,fp=None,fields=None,dnp=False):
        p=self.add(typ,ref,x,y,value,fp=fp,fields=fields,dnp=dnp)
        self.rail(p["1"],top,"up",2.54)
        self.rail(p["2"],bottom,"down",2.54)
        return p
    def child(self,name,title,x,y,page):
        sid=uid("child:"+name)
        self.items.append(f'''(sheet (at {xy(x,y)}) (size 76.2 25.4) (fields_autoplaced yes)
         (stroke (width 0.254) (type default)) (fill (color 0 0 0 0)) (uuid {sid})
         {prop("Sheetname",title,x,y-1.27,False,"left bottom")}
         {prop("Sheetfile",name+".kicad_sch",x,y+26.67,False,"left top")}
         (instances (project "NumitronTop" (path {q(self.path)} (page {q(page)})))))''')
        return sid
    def write(self):
        lib="\n".join(f'(symbol "Numitron:{t}" {LIB[t]["body"]})' for t in sorted(self.used))
        body=f'''(kicad_sch (version 20250114) (generator "eeschema")
          (uuid {self.id}) (paper {q(self.size)})
          (title_block (title {q(self.title)}) (date "2026-09-18") (rev "0.1 review")
            (company "Numitron Clock") (comment 1 "V1 USB power | No fabrication release"))
          (lib_symbols {lib})
          {''.join(self.items)}
          (sheet_instances (path "/" (page {q(self.page)}))) (embedded_fonts no))'''
        (OUT/(self.name+".kicad_sch")).write_text(body+"\n")

def build_control(child_id):
    s=Sheet("ControlAndSensor","Top board: control and light sensor",2,child_id=child_id)
    s.text("CONTROL / 3.3 V TO 5 V",17.78,15.24,2.54)
    s.text("Four non-inverting channels. BLANK high disables every drain output.",17.78,22.86)
    u=s.add("74AHCT125","U2",93.98,86.36,"SN74AHCT125DR",fields={"MPN":"SN74AHCT125DR","Manufacturer":"Texas Instruments"})
    s.rail(u["14"],"+5V"); s.rail(u["7"],"GND","down")
    for i,(pin,out,oe,name) in enumerate([(2,3,1,"SER"),(5,6,4,"SRCK"),(9,8,10,"RCK"),(12,11,13,"BLANK")]):
        s.stub(u[str(pin)],name+"_3V3","left",17.78,True)
        s.stub(u[str(oe)],"BUF_OE_N","left",5.08)
        r=s.add("R",f"R{i+3}",132.08,u[str(out)][1],"33R",angle=90)
        s.wire(u[str(out)],r["1"]); s.stub(r["2"],name+"_5V","right",7.62,True)
    s.passive("C","C4","100n 50V X7R",177.8,48.26,"+5V","GND")
    s.text("FIRMWARE ARM / DEFAULT OFF",205.74,35.56,1.524)
    qt=s.add("MMBT3904","Q1",241.3,83.82,"MMBT3904-7-F",fields={"MPN":"MMBT3904-7-F","Manufacturer":"Diodes Incorporated"})
    s.rail(qt["2"],"GND","down")
    rp=s.add("R","R15",243.84,59.69,"1k")
    s.rail(rp["1"],"+5V"); s.wire(rp["2"],qt["3"])
    s.junction((243.84,71.12))
    # Split the collector wire at the labeled junction for explicit connectivity.
    s.wire((243.84,71.12),(261.62,71.12)); s.label("BUF_OE_N",(261.62,71.12))
    rb=s.add("R","R16",215.9,83.82,"2.2k",angle=90)
    s.wire(rb["2"],qt["1"]); s.stub(rb["1"],"DISPLAY_ARM","left",7.62,True)
    s.passive("R","R17","4.7k",215.9,113.03,"DISPLAY_ARM","GND")
    s.text("ARM = 0 / disconnected: buffers high impedance.\nR10 holds BLANK_5V high; tubes stay off.\nARM = 1: Q1 enables all four buffers.\nKeep BLANK high while arming and loading data.\nNo 5 V pull-up connects directly to an MCU pin.",279.4,55.88)
    s.text("5 V BUS DEFAULTS",17.78,128.27,1.524)
    for i,(x,net) in enumerate([(40.64,"SER_5V"),(81.28,"SRCK_5V"),(121.92,"RCK_5V")],7):
        s.passive("R",f"R{i}","100k",x,147.32,net,"GND")
    s.passive("R","R10","2.2k",162.56,147.32,"+5V","BLANK_5V")
    s.text("3.3 V INPUT DEFAULTS",17.78,175.26,1.524)
    for i,(x,net) in enumerate([(40.64,"SER_3V3"),(81.28,"SRCK_3V3"),(121.92,"RCK_3V3")],11):
        s.passive("R",f"R{i}","4.7k",x,194.31,net,"GND")
    s.passive("R","R14","4.7k",162.56,194.31,"+3V3","BLANK_3V3")
    s.text("STARTUP CONTRACT",17.78,224.79,1.524)
    s.text("1. ARM low; configure SER/SRCK/RCK low and BLANK high.\n2. ARM high; clock 32 zero bits, pulse RCK with SRCK low.\n3. Load the desired frame; only then enable BLANK PWM.\n4. BLANK low = lit. A logic one in a drain bit lights a filament.\nStart with 100 kHz SPI mode 0; verify signals before raising speed.",17.78,232.41)
    s.text("AMBIENT LIGHT / 3.3 V I2C",228.6,135.89,1.524)
    sensor=s.add("BH1750FVI","U3",350.52,177.8,"BH1750FVI-TR",fields={"MPN":"BH1750FVI-TR","Manufacturer":"ROHM","FootprintStatus":"HOLD: verify WSOF6I land pattern; no center-pad solder"})
    s.rail(sensor["1"],"+3V3"); s.rail(sensor["3"],"GND","down")
    s.stub(sensor["6"],"SCL","right",7.62,True); s.stub(sensor["4"],"SDA","right",7.62,True)
    sup=s.add("TLV809EA29DBZ","U4",261.62,172.72,"TLV809EA29DBZR",fields={"MPN":"TLV809EA29DBZR","Manufacturer":"Texas Instruments"})
    s.rail(sup["3"],"+3V3"); s.rail(sup["1"],"GND","down")
    rd=s.add("R","R18",299.72,172.72,"1k",angle=90)
    s.wire(sup["2"],rd["1"]); s.wire(rd["2"],sensor["5"])
    s.label("ALS_DVI",(312.42,172.72))
    cd=s.add("C","C6",320.04,195.58,"100n 50V X7R")
    s.wire(cd["1"],(320.04,172.72)); s.junction((320.04,172.72)); s.rail(cd["2"],"GND","down")
    s.stub(sensor["2"],"ALS_ADDR","left",5.08)
    addr=s.add("R","R19",355.6,218.44,"10k")
    s.stub(addr["1"],"ALS_ADDR","up",2.54); s.rail(addr["2"],"GND","down",2.54)
    s.passive("C","C5","100n 50V X7R",383.54,147.32,"+3V3","GND")
    s.passive("C","C7","100n 50V X7R",238.76,208.28,"+3V3","GND")
    for ref,x,net in [("R20",281.94,"SDA"),("R21",320.04,"SCL")]:
        s.passive("R",ref,"4.7k",x,231.14,"+3V3",net,dnp=True,fields={"Assembly":"DNP - bottom board owns I2C pull-ups"})
    s.text("U4 gives DVI a defined reset after 3.3 V rises.\nADDR low selects 0x23. U4 delay is 200 ms nominal.\nR20/R21 DNP: fit only if bottom-board pull-ups are absent.\nKeep U3 optical aperture clear; do not solder center metal.",228.6,252.73)
    return s

def build_drivers(child_id):
    mapping=[("A",7),("B",8),("C",5),("D",4),("E",3),("F",9),("G",6),("DP*",1)]
    pins=[(2,"COM","passive",0,25.4,270)]
    for i,(seg,pin) in enumerate(mapping): pins.append((pin,seg,"passive",-15.24,17.78-i*2.54,0))
    graphic=rect(-12.7,22.86,12.7,-10.16)
    # A recognizable seven-segment diagram, with the optional decimal explicitly labeled at the pin.
    for a,b in [((1.27,17.78),(7.62,17.78)),((8.89,16.51),(8.89,10.16)),((8.89,7.62),(8.89,1.27)),
                ((1.27,0),(7.62,0)),((0,1.27),(0,7.62)),((0,10.16),(0,16.51)),((1.27,8.89),(7.62,8.89))]: graphic+=line(a,b,.508)
    symbol("DR2000_FamilySocket",pins,graphic,"V",datasheet="${KIPRJMOD}/../../datasheets/dr2000.pdf",
           desc="GZC9-A socket; owner reports DR2000-marked tubes with prefix decimal. Pin 1 DP provisional: RCA table assigns DP to DR2010, NC to DR2000. Verify on actual tubes.")
    s=Sheet("TubeDrivers","Top board: tube drivers",3,child_id=child_id)
    s.text("FOUR STATIC DIGITS / NO MULTIPLEXING",17.78,15.24,2.54)
    s.text("A-G mapping: RCA datasheet pp. 3-4. Owner confirms DR2000-marked tubes with prefix DP; verify DP pin 1 on actual tubes.",17.78,22.86)
    for i,(x,y,digit) in enumerate([(78.74,76.2,"H10"),(281.94,76.2,"H1"),(78.74,187.96,"M10"),(281.94,187.96,"M1")]):
        s.text(digit+" / "+["HOURS TENS","HOURS UNITS","MINUTES TENS","MINUTES UNITS"][i],x-55.88,y-41.91,1.524)
        drv=s.add("TPIC6B595DW",f"U{i+5}",x,y,"TPIC6B595DWR",fields={"MPN":"TPIC6B595DWR","Manufacturer":"Texas Instruments"})
        tube=s.add("DR2000_FamilySocket",f"V{i+1}",x+71.12,y,"DR2000 / GZC9-A",fields={"MPN":"DR2000","Socket":"GZC9-A","Manufacturer":"RCA / socket seller TBD","FootprintStatus":"HOLD: socket-tail measurements","TubeVariant":"Owner confirms DR2000 marking and prefix DP; verify pin 1 before use"})
        s.rail(drv["2"],"+5V"); s.rail(tube["2"],"V_TUBE")
        for pn in [10,11,19]:
            p=drv[str(pn)]; s.wire(p,(p[0],y+30.48))
        s.wire((x-5.08,y+30.48),(x+5.08,y+30.48)); s.junction((x,y+30.48)); s.rail((x,y+30.48),"GND","down",2.54)
        for pn,net in [(13,"SRCK_5V"),(12,"RCK_5V"),(9,"BLANK_5V"),(8,"+5V")]: s.stub(drv[str(pn)],net,"left",5.08,True)
        s.nc(drv["1"]); s.nc(drv["20"])
        s.stub(drv["3"],"SER_5V" if i==0 else f"CHAIN_{i}{i+1}","left",5.08,i==0)
        for bit,((seg,tp),dp) in enumerate(zip(mapping,[4,5,6,7,14,15,16,17])):
            s.wire(drv[str(dp)],tube[str(tp)])
            s.label(digit+"_"+("DP" if bit==7 else seg),(x+25.4,drv[str(dp)][1]))
        if i<3: s.stub(drv["18"],f"CHAIN_{i+1}{i+2}","right",5.08)
        else:
            t=s.add("TestPoint","TP5",x+33.02,y+12.7,"SER_OUT 5V")
            s.wire(drv["18"],t["1"])
        s.passive("C",f"C{8+2*i}","100n 50V X7R",x+27.94,y+38.1,"+5V","GND")
        s.passive("C",f"C{9+2*i}","1u 25V X7R",x+76.2,y+38.1,"V_TUBE","GND",fp="Capacitor_SMD:C_0805_2012Metric")
    s.text("Bytes, MSB first: [M1, M10, H1, H10]. Bits 0..6 = A..G; bit 7 = socket pin 1 (DP*).\nUse V3's prefix DP for HH.MM after verifying pin 1. Archived DR2000 table lists pin 1 as NC.\nSRCLR is tied high locally; startup clears both shift and storage state by shifting/latching zeros.",17.78,254)
    return s

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write",action="store_true",required=True)
    parser.parse_args()
    setup_library()
    root=Sheet("NumitronTop","Top board: power and interface",1)
    root.text("NUMITRON CLOCK / TOP BOARD",17.78,15.24,2.54)
    root.text("V1 schematic review - USB powered - four RCA DR2000 tubes",17.78,22.86,1.524)
    root.text("J1 / CONTROLLER CONNECTION",17.78,35.56,1.524)
    j=root.add("IDC_2x08","J1",55.88,62.23,"61201621621",fields={"Manufacturer":"Wurth Elektronik","MPN":"61201621621"})
    connector={1:"GND",2:"SER_3V3",3:"GND",4:"SRCK_3V3",5:"GND",6:"RCK_3V3",7:"GND",8:"BLANK_3V3",
               9:"+3V3",10:"SDA",11:"GND",12:"SCL",13:"DISPLAY_ARM",14:"+5V",15:"GND",16:"+5V"}
    for pin,net in connector.items(): root.stub(j[str(pin)],net,"left" if pin%2 else "right",7.62,True)
    root.text("Keyed 2 x 8 header; 2.54 mm pin grid.\n16-way, 1.27 mm pitch, 28 AWG ribbon.\nStraight-through cable: pin n to pin n.\nPin 1 = marked corner / red ribbon edge.\nSee docs/interface.md for mating-face view.",17.78,90.17)
    root.text("4.5 V FILAMENT SUPPLY",134.62,35.56,1.524)
    u=root.add("AP7361C_Y5","U1",190.5,63.5,"AP7361C-Y5-13",fields={"Manufacturer":"Diodes Incorporated","MPN":"AP7361C-Y5-13","LCSC":"C507885"})
    root.wire(u["4"],(165.1,58.42)); root.rail((165.1,58.42),"+5V")
    root.wire(u["1"],(165.1,63.5)); root.wire((165.1,63.5),(165.1,58.42)); root.junction((165.1,58.42))
    root.rail(u["2"],"GND","down")
    root.wire(u["5"],(254,58.42)); root.label("V_TUBE",(254,58.42),True)
    rt=root.add("R","R1",231.14,73.66,"46.4k 1%",fields={"MPN":"RC0603FR-0746K4L","Manufacturer":"Yageo"})
    rb=root.add("R","R2",231.14,96.52,"10k 1%",fields={"MPN":"RC0603FR-0710KL","Manufacturer":"Yageo"})
    root.wire(rt["1"],(231.14,58.42)); root.junction((231.14,58.42))
    root.wire(rt["2"],(231.14,83.82)); root.wire((231.14,83.82),rb["1"])
    root.wire(u["3"],(215.9,63.5)); root.wire((215.9,63.5),(215.9,83.82)); root.wire((215.9,83.82),(231.14,83.82))
    root.junction((231.14,83.82)); root.label("LDO_FB",(215.9,83.82)); root.rail(rb["2"],"GND","down")
    for ref,x,net in [("C1",144.78,"+5V"),("C2",281.94,"V_TUBE"),("C3",325.12,"V_TUBE")]:
        root.passive("C",ref,"10u 25V X7R",x,78.74,net,"GND",fp="Capacitor_SMD:C_1206_3216Metric",fields={"Manufacturer":"KYOCERA AVX","Selection":"X7R family; exact order code / DC bias pending"})
    root.text("0.8 x (1 + 46.4k / 10k) = 4.512 V nominal.\nDo not increase voltage to compensate driver loss.\nC2+C3: verify >= 2.2 uF effective total at bias.\nGND tab needs copper for heat spreading.",266.7,109.22)
    root.text("POWER ENTRY / TEST",17.78,128.27,1.524)
    for i,(x,net) in enumerate([(35.56,"+5V"),(86.36,"+3V3"),(137.16,"V_TUBE"),(187.96,"GND")],1):
        p=root.add("TestPoint",f"TP{i}",x,153.67,net)
        root.rail(p["1"],net,"down")
        if net!="V_TUBE":
            f=root.add("PWR_FLAG",f"#FLG0{i:02d}",x+22.86,153.67)
            root.rail(f["1"],net,"down")
    root.text("Bottom board supplies regulated 3.3 V and protected 5 V.\nBudget up to 0.77 A nominal filament load plus logic.\nVerify cold-filament surge, USB current authorization,\nribbon loss, LDO dropout and enclosure temperature.\nNo battery, charging, USB-C or telemetry circuitry here.",17.78,171.45)
    root.text("MECHANICAL HOLD POINTS",266.7,145.415,1.524)
    root.text("Target: 110 x 30 mm, 2 layers.\nTube grouping: [HH] gap [MM].\nBoard separation: 25-30 mm.\nGZC9-A socket PCB-tail dimensions unmeasured.\nTube/socket and BH1750 footprints intentionally\nunassigned until the relevant land patterns are verified.\nNo PCB routing or manufacturing outputs in this revision.",266.7,153.035)
    control_id=root.child("ControlAndSensor","Logic / ambient light",35.56,223.52,2)
    driver_id=root.child("TubeDrivers","Four tube drivers",165.1,223.52,3)
    root.text("Global nets join the sheets.\nSER_5V -> U5 -> U6 -> U7 -> U8.\nBLANK_5V high = all filaments off.",266.7,223.52)
    control=build_control(control_id)
    drivers=build_drivers(driver_id)
    for sheet in (root,control,drivers): sheet.write()
    symbols="\n".join(f'(symbol {q(name)} {d["body"]})' for name,d in LIB.items())
    (OUT/"libraries/Numitron.kicad_sym").write_text(f'(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")\n{symbols}\n)\n')
    (OUT/"sym-lib-table").write_text('(sym_lib_table (version 7)\n (lib (name "Numitron") (type "KiCad") (uri "${KIPRJMOD}/libraries/Numitron.kicad_sym") (options "") (descr "Project-local, datasheet-checked symbols"))\n)\n')
    (OUT/"NumitronTop.kicad_pro").write_text(json.dumps({"meta":{"filename":"NumitronTop.kicad_pro","version":1},"net_settings":{"classes":[{"name":"Default","clearance":0.2,"track_width":0.25,"via_diameter":0.6,"via_drill":0.3}],"meta":{"version":3}},"erc":{"erc_exclusions":[],"meta":{"version":0}},"text_variables":{"DESIGN_STATUS":"SCHEMATIC REVIEW - NOT FOR FABRICATION"}},indent=2)+"\n")
    (ROOT/"review/components.json").write_text(json.dumps([c for s in (root,control,drivers) for c in s.components if not c["ref"].startswith("#")],indent=2)+"\n")
    print("Wrote three schematic sheets and the project-local symbol library.")

if __name__ == "__main__": main()
