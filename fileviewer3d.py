from PyQt5.QtWidgets import*
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import numpy as np

"""Toolhead 3D"""
theta = np.linspace(0,2*np.pi,5)
r = np.linspace(0,3,2)
T, R = np.meshgrid(theta, r)

x_toolhead = R * np.cos(T)
y_toolhead = R * np.sin(T)
z_toolhead = np.sqrt(20*x_toolhead**2 + 20*y_toolhead**2)

"""XY Origin and Z-offset 3D"""
r2 = 2.5
u, v = np.mgrid[0:2*np.pi:5j, 0:np.pi:5j]
x_origin = r2*np.cos(u)*np.sin(v)
y_origin = r2*np.sin(u)*np.sin(v)
z_origin = r2*np.cos(v)

class FileViewer3D(QWidget):
    """3D Viewer"""
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
        
        self.toolhead = self.canvas.axes.plot_surface(x_toolhead, y_toolhead, z_toolhead, color='red')
        self.origin = self.canvas.axes.plot_surface(x_origin, y_origin, z_origin, color='blue')
        self.mesh = self.canvas.axes.plot_trisurf([0,1,2],[0,4,2],[1,2,7], color=(0,0,0,0))
    
    def Set_Toolhead_Pos(self, x0, y0, z0):
        """Set 3D toolhead position

        Args:
            x0 (float): Toolhead X position
            y0 (float): Toolhead Y position
            z0 (float): Toolhead Z position
        """
        self.toolhead.remove()
        
        x, y, z = x_toolhead.copy(), y_toolhead.copy(), z_toolhead.copy()
        for i in range(len(x)):
            for j in range(len(x[i])):
                x[i][j] += x0
                
        for i in range(len(y)):
            for j in range(len(y[i])):
                y[i][j] += y0
                
        for i in range(len(z)):
            for j in range(len(z[i])):
                z[i][j] += z0
                
        self.toolhead = self.canvas.axes.plot_surface(x, y, z, color='red')
        self.canvas.draw()
        
    def Set_Origin_Pos(self, x0, y0, z0):
        """Set 3D origin position

        Args:
            x0 (float): X0
            y0 (float): Y0
            z0 (float): Z-offset
        """
        self.origin.remove()
        
        x, y, z = x_origin.copy(), y_origin.copy(), z_origin.copy()
        for i in range(len(x)):
            for j in range(len(x[i])):
                x[i][j] += x0
                
        for i in range(len(y)):
            for j in range(len(y[i])):
                y[i][j] += y0
                
        for i in range(len(z)):
            for j in range(len(z[i])):
                z[i][j] += z0
                
        self.origin = self.canvas.axes.plot_surface(x, y, z, color='blue')
        self.canvas.draw()
        
    def Plot_Mesh(self, mesh): 
        """Plot mesh bed

        Args:
            mesh: Mesh points
        """
        self.mesh.remove()
        
        x, y, z = [], [], []
        for i in mesh:
            x.append(i[0])
            y.append(i[1])
            z.append(i[2])
        
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)

        self.mesh = self.canvas.axes.plot_trisurf(x, y, z, color='lightgray', alpha=0.5)
        self.canvas.draw()
        
    def Remove_Mesh(self):
        """Remove mesh bed"""
        self.mesh.remove()
        self.mesh = self.canvas.axes.plot_trisurf([0,1,2],[0,4,2],[1,2,7], color=(0,0,0,0))