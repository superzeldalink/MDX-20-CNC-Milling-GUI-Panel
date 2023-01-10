import pathlib
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import serial.tools.list_ports

class SelectSerialDialog(QDialog):
    def __init__(self, _mdx_port, _arduino_port):
        super().__init__()
        uic.loadUi(f"{pathlib.Path(__file__).parent.resolve()}/SelectSerialDialog.ui", self)
        
        self.mdx_port, self.arduino_port = None, None
        self.mdx_comboBox.addItem("None")
        self.arduino_comboBox.addItem("None")
        
        comports = serial.tools.list_ports.comports()
        self.ports, descs = [], []
        for port, desc, _ in comports:
            self.ports.append(port)
            descs.append(desc)
            
            label = "{}: {}".format(port,desc)
            self.mdx_comboBox.addItem(label)
            self.arduino_comboBox.addItem(label)
            
            if port == _mdx_port:
                self.mdx_port = port
                self.mdx_comboBox.setCurrentText(label)
            if port == _arduino_port:
                self.arduino_port = port
                self.arduino_comboBox.setCurrentText(label)
                
        self.mdx_comboBox.currentIndexChanged.connect(self.mdx_port_changed)
        self.arduino_comboBox.currentIndexChanged.connect(self.arduino_port_changed)
        
    def mdx_port_changed(self, index):
        if index == 0:
            self.mdx_port = None
        else:
            self.mdx_port = self.ports[index - 1]
    def arduino_port_changed(self, index):
        if index == 0:
            self.arduino_port = None
        else:
            self.arduino_port = self.ports[index - 1]
            