#!/usr/bin/env python3
"""Frame KiCad's native routing/assembly SVGs; no invented geometry.

Ground fills are hidden in these overview copies only. Native filled-copper
plots and the editable PCB are preserved separately for detailed review.
"""
from pathlib import Path
import re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
for side in ['top','bottom']:
    source=ET.parse(ROOT/f'tmp/{side}-routing.svg').getroot()
    view=source.get('viewBox')
    # Keep the CAD geometry; use a paper-friendly palette for the preview.
    palette={'#C83434':'#b86529','#4D7FC4':'#3567a4','#F2EDA1':'#194a39','#D6D6D6':'#546c63','#AFAFAF':'#546c63','#D0D2CD':'#546c63','#848400':'#194a39','#C2C200':'#263d34','#585D84':'#546c63','#E8B2A7':'#194a39','#FFFFFF':'#dce6de','#000000':'#253d34'}
    for el in source.iter():
        for k,v in list(el.attrib.items()):
            for old,new in palette.items():v=v.replace(old,new)
            el.set(k,v)
    root=ET.Element(f'{{{NS}}}svg',{'width':'1800','height':'860','viewBox':'0 0 1800 860'})
    ET.SubElement(root,'rect',{'width':'1800','height':'860','fill':'#f2f5f1'})
    def label(x,y,value,size=24,color='#183f32',weight='400'):
        item=ET.SubElement(root,'text',{'x':str(x),'y':str(y),'font-family':'Arial, Helvetica, sans-serif','font-size':str(size),'fill':color,'font-weight':weight});item.text=value
    label(80,55,'NUMITRON / TOP BOARD',30,weight='700')
    label(80,91,('Tube side' if side=='top' else 'Underside · mirrored to show the assembled face')+'   /   REV 0.2',22)
    label(1440,55,'110 × 40 mm',25)
    label(1440,91,'2 copper layers',20)
    ET.SubElement(root,'rect',{'x':'80','y':'120','width':'1640','height':'596.36','rx':'1','fill':'#ffffff','stroke':'#aec1b6','stroke-width':'1.5'})
    drawing=ET.SubElement(root,'svg',{'x':'80','y':'120','width':'1640','height':'596.36','viewBox':view})
    for child in list(source):drawing.append(child)
    label(80,762,'Routing and component outlines from the saved KiCad board. Ground fills hidden for clarity.',22)
    label(80,801,'PROTOTYPE REVIEW  /  Verify socket fit, pin-1 decimal and enclosure clearance before ordering.',20,'#6e5425')
    ET.ElementTree(root).write(ROOT/f'review/NumitronTop-{side}.svg',encoding='unicode',xml_declaration=True)
