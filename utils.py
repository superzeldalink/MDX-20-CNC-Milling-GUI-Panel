"""Utilities"""

MAX_X = 200
MAX_Y = 150
MIN_Z = -60

def clip(value, lower, upper):
    return lower if value < lower else upper if value > upper else value

def mm2inch(mm):
    return mm/0.0254

def inch2mm(inch):
    return inch*0.0254