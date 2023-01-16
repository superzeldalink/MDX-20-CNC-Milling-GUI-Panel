from PyQt5.QtWidgets import*
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class AlignmentViewer(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)

        self.canvas = FigureCanvas(Figure(figsize=(20,10)))
        
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        
        self.canvas.axes = self.canvas.figure.add_subplot()
        self.canvas.axes.set_aspect('equal')
        self.setLayout(vertical_layout)
        