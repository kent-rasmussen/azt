#!/usr/bin/env python3
# coding=UTF-8
import ast
def stringtoobject(x):
    try:
        return ast.literal_eval(x)
    except (SyntaxError,ValueError): #if the literal eval doesn't work, it's a string
        return x #in case string is just string
def indent(elem, level=0):
    indentspaces=4
    """from http://effbot.org/zone/element-lib.htm#prettyprint"""
    i = "\n" + level*" "*indentspaces
    if len(elem):
        # print("elem: {}".format(elem))
        # print("elem.text: {}".format(elem.text))
        if not elem.text or not elem.text.strip():
            elem.text = i + " "*indentspaces
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
if __name__ == '__main__':
    import xml.etree.ElementTree as ET
    x='<a><b><c>d</c></b></a>'
    y=ET.fromstring(x)
    print(ET.tostring(y).decode('utf-8'))
    indent(y)
    print(ET.tostring(y).decode('utf-8'))