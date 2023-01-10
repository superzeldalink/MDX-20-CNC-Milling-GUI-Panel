from PyQt5.QtWidgets import*
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class MeshBedViewer(QWidget):
    """Mesh bed viewer"""
    def Create_Trans_Box(self):
        max_range = np.array([200, 150, 65]).max()
        Xb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][0].flatten() + 0.5*(200)
        Yb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][1].flatten() + 0.5*(150)
        Zb = 0.5*max_range*np.mgrid[-1:2:2,-1:2:2,-1:2:2][2].flatten() + 0.5*(-55)

        for xb, yb, zb in zip(Xb, Yb, Zb):
            self.canvas.axes.plot([xb], [yb], [zb], 'w')
            
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)

        self.canvas = FigureCanvas(Figure(figsize=(20,10)))
        
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        
        self.canvas.axes = self.canvas.figure.add_subplot(projection="3d")
        self.setLayout(vertical_layout)
        
        self.canvas.axes.view_init(25, -100)
        
        self.Create_Trans_Box()
        
        self.mesh = self.canvas.axes.plot_trisurf([0,1,2],[0,4,2],[1,2,7], color=(0,0,0,0))
        
    def Plot_Mesh(self, mesh):
        """Plot mesh bed

        Args:
            mesh: Mesh points after probing
        """
        self.canvas.axes.clear()
        
        x, y, z = [], [], []
        for i in mesh:
            x.append(i[0])
            y.append(i[1])
            z.append(i[2])

        x = np.array(x)
        y = np.array(y)
        z = np.array(z)

        self.mesh = self.canvas.axes.plot_trisurf(x, y, z, color='blue')
        self.canvas.draw()