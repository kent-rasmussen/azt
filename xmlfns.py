#!/usr/bin/env python3
# coding=UTF-8
def indent(elem, level=0):
    indentspaces=4
    """from http://effbot.org/zone/element-lib.htm#prettyprint"""
    i = "\n" + level*" "*indentspaces
    if len(elem):
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
