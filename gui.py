import sys, mdx20, nc2rol, pathlib, time, arduino, PointsOnMesh, configparser
from utils import *
from SelectSerialDialog import SelectSerialDialog
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtCore import QThread, pyqtSignal, QLineF
from PyQt5.QtCore import QFile, QTextStream
import breeze_resources

path = str(pathlib.Path(__file__).parent.resolve())

# Initial variales
x, y, z = 0, 0, 0
x0, y0 ,z0 = 0, 0, 0
delta_xy, delta_z = 10, 1
speed = 15
spindle = False

graphview_scale = 1

speed_override = False
instructionsList = []
points = []
points_data = []
currentInstruction = 0
started = False

prev_time = 0

mesh_bed = []
mesh_bl_x, mesh_bl_y, mesh_tr_x ,mesh_tr_y = 0, 0, MAX_X, MAX_Y
h_grid, v_grid = 3, 3
use_mesh = False

mdx_port, arduino_port = None, None

config = configparser.ConfigParser()
config.read(path + "/config/config.ini")

x0 = float(config['Origin']['x'])
y0 = float(config['Origin']['y'])
z0 = float(config['Origin']['z'])

class WorkerThread(QThread):
    """Job milling worker"""
    update = pyqtSignal(int)
    def run(self):
        for i in range(currentInstruction, len(instructionsList)):
            if started == False:
                break
            
            instruction = instructionsList[i]
            if instruction != "":
                if instruction[0] == 'Z':
                    xt, yt, zt = instruction[1:-1].split(",")
                    new_x = float(xt)
                    new_y = float(yt)
                    new_z = float(zt)
                    newInstruction = "Z{:.1f},{:.1f},{:.1f};".format(new_x, new_y, new_z)
                elif (instruction[0] == 'V' and speed_override != False and float(instruction[1:-1]) != 15):
                    newInstruction = "V{:.1f}".format(speed)
                else: 
                    newInstruction = instruction
                
                mdx20.Send_Data(newInstruction)
                self.update.emit(i)
                
        self.finished.emit()
        
class MeshBedWorker(QThread):
    """Mesh bed worker"""
    update_meshviewer = pyqtSignal()
    update_table_value = pyqtSignal()
    
    def AutoZ_Down(self,_x ,_y, _z):
        while True:
            read_data = arduino.Read_Data()
            if read_data == 0:
                return _z
            elif read_data == 2:
                return "error"
            mdx20.Move(_x,_y,_z)
            _z = _z - 0.0127
    
    def run(self):
        save_z = z
        x_step = (mesh_tr_x - mesh_bl_x) / h_grid
        y_step = (mesh_tr_y - mesh_bl_y) / v_grid
        
        for i in np.arange(mesh_bl_y, mesh_tr_y+0.01, y_step):
            for j in (np.arange(mesh_bl_x, mesh_tr_x+0.01, x_step) if (i - mesh_bl_y)%(2*y_step) == 0 else np.arange(mesh_tr_x, mesh_bl_x-0.01, -x_step)):
                mdx20.Move(j, i, save_z+2)
                mdx20.Move(j, i, save_z)
                time.sleep(1.5)
                _z = self.AutoZ_Down(j, i, save_z)
                if _z == "error":
                    return
                mesh_bed.append([j,i,_z])
                self.update_table_value.emit()
                if i >= y_step:
                    self.update_meshviewer.emit()
        
class MainWindow(QMainWindow):
    """Main GUI"""
    def init_machine(self):
        self.Main_Control.setEnabled(False)
        mdx20.Send_Data("IN;")
        mdx20.Send_Data("V{:.1f};".format(speed))
        mdx20.Send_Data("!MC0;")
        mdx20.Send_Data("!ZM400.0;")
        self.Move(0,0,0)
        self.Main_Control.setEnabled(True)
        
    def keyPressEvent(self, event):
        """Keyboard shortcut for moving bed and toolhead.

        Args:
            event (QtEvent): Event signal from Qt
        """
        if event.key() == QtCore.Qt.Key_Left:
            self.Move(x-delta_xy, y, z)
        elif event.key() == QtCore.Qt.Key_Right:
            self.Move(x+delta_xy, y, z)
            
        elif event.modifiers() == QtCore.Qt.ControlModifier:
            if event.key() == QtCore.Qt.Key_Up:
                self.Move(x, y, z+delta_z)
            elif event.key() == QtCore.Qt.Key_Down:
                self.Move(x, y, z-delta_z)
                
        elif event.key() == QtCore.Qt.Key_Up:
            self.Move(x, y+delta_xy, z)
        elif event.key() == QtCore.Qt.Key_Down:
            self.Move(x, y-delta_xy, z)
            
    def __init__(self):
        """Initialization"""
        super().__init__()
        uic.loadUi(path + "/gui.ui", self)
        self.xm_btn.clicked.connect(lambda: self.Move(x-delta_xy, y, z))
        self.xp_btn.clicked.connect(lambda: self.Move(x+delta_xy, y, z))
        self.ym_btn.clicked.connect(lambda: self.Move(x, y-delta_xy, z))
        self.yp_btn.clicked.connect(lambda: self.Move(x, y+delta_xy, z))
        self.zm_btn.clicked.connect(lambda: self.Move(x, y, z-delta_z))
        self.zp_btn.clicked.connect(lambda: self.Move(x, y, z+delta_z))
        self.home_xy_btn.clicked.connect(lambda: self.Move(x0, y0, 0))
        self.home_z_btn.clicked.connect(lambda: self.Move(x, y, 0))
        self.go_btn.clicked.connect(self.Go)
        self.set_origin_btn.clicked.connect(self.Set_Origin)
        self.set_z_btn.clicked.connect(self.Set_Z)
        self.spindle_checkbox.stateChanged.connect(self.Spindle)
        self.speed_override_checkbox.stateChanged.connect(self.Speed_override_changed)
        
        self.delta_xy_spinbox.valueChanged.connect(self.Delta_XY_changed)
        self.delta_z_spinbox.valueChanged.connect(self.Delta_Z_changed)
        self.speed_spinbox.valueChanged.connect(self.Speed_changed)
        
        self.x0_spinbox.valueChanged.connect(self.x0_changed)
        self.y0_spinbox.valueChanged.connect(self.y0_changed)
        self.z0_spinbox.valueChanged.connect(self.z0_changed)
        
        self.x_pos_spinbox.setValue(x)
        self.y_pos_spinbox.setValue(y)
        self.z_pos_spinbox.setValue(z)
        self.delta_xy_spinbox.setValue(delta_xy)
        self.delta_z_spinbox.setValue(delta_z)
        self.speed_spinbox.setValue(speed)
        
        self.actionOpen.triggered.connect(self.openFile)
        self.actionOpenSerial.triggered.connect(self.Start_serial)
        self.actionExit.triggered.connect(lambda: QtCore.QCoreApplication.quit())
        
        self.instructions_list.currentRowChanged.connect(self.Instruction_row_changed)
        
        self.start_btn.clicked.connect(self.Start_Job)
        
        self.zoom_in_btn.clicked.connect(self.Zoom_In_Graph)
        self.zoom_out_btn.clicked.connect(self.Zoom_Out_Graph)
        self.one_to_one_btn.clicked.connect(self.One_To_One_Graph)
        
        self.autoZ_btn.clicked.connect(self.AutoZ)
        self.mesh_bed_btn.clicked.connect(self.Mesh_Bed)
        
        self.x_bl_spinbox.valueChanged.connect(self.x_bl_changed)
        self.y_bl_spinbox.valueChanged.connect(self.y_bl_changed)
        self.x_tr_spinbox.valueChanged.connect(self.x_tr_changed)
        self.y_tr_spinbox.valueChanged.connect(self.y_tr_changed)
        
        self.set_bl_btn.clicked.connect(self.Set_bl)
        self.set_tr_btn.clicked.connect(self.Set_tr)
        self.h_grid_spinbox.valueChanged.connect(self.h_grid_changed)
        self.v_grid_spinbox.valueChanged.connect(self.v_grid_changed)
        
        self.save_mesh_btn.clicked.connect(self.Save_Mesh)
        self.load_mesh_btn.clicked.connect(self.Load_Mesh)
        self.clear_mesh_btn.clicked.connect(self.Clear_Mesh)
        self.relevel_btn.clicked.connect(self.Relevel)
        self.use_mesh_checkbox.stateChanged.connect(self.Use_Mesh)
        
        self.update_table_size()
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        """Init 2D viewport"""
        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)
        pen = QPen(QtCore.Qt.white)
        pen.setCosmetic(True)
        
        self.lines = []
        
        # Draw Grid
        side = 10

        for i in range(20):
            for j in range(15):
                r = QtCore.QRectF(QtCore.QPointF(i*side, j*side), QtCore.QSizeF(side, side))
                self.scene.addRect(r, pen)
        
        self.origin = self.scene.addEllipse(-1.5, -1.5, 3, 3, QPen(QtCore.Qt.blue), QBrush(QtCore.Qt.blue))
        self.tool_head = self.scene.addEllipse(-1.5, -1.5, 3, 3, QPen(QtCore.Qt.red), QBrush(QtCore.Qt.red))
        
        """Init 3D viewport"""
        self.fileviewer3d.Set_Toolhead_Pos(x, y, z)
        self.fileviewer3d.Set_Origin_Pos(x0, y0, z0)

        self.graphicsView.scale(5, -5)
        self.graphicsView.viewport().installEventFilter(self)
        
        self.Main_Control.setEnabled(False)
        
        """Set spinboxes values from config file"""
        self.x0_spinbox.setValue(x0)
        self.y0_spinbox.setValue(y0)
        self.z0_spinbox.setValue(z0)

    """2D viewport related functions"""
    def eventFilter(self, source, event):
        """EventFilter for 2D graphicsview
            Ctrl+Scroll for zooming
            Ctrl+Click for setting x,y
        """
        global graphview_scale
                    
        if (source == self.graphicsView.viewport()):
            if event.type() == QtCore.QEvent.Wheel and event.modifiers() == QtCore.Qt.ControlModifier:
                if event.angleDelta().y() > 0:
                    scale = 1.25
                else:
                    scale = .8
                
                graphview_scale *= scale
                self.graphicsView.scale(scale, scale)
            
            if event.type() == QtCore.QEvent.MouseMove:
                mousePos = self.graphicsView.mapToScene(event.pos())
                self.mousepos_label.setText("({:.1f}, {:.1f})".format(mousePos.x(), mousePos.y()))
                
            if event.type() == QtCore.QEvent.MouseButtonPress and event.modifiers() == QtCore.Qt.ControlModifier and started == False:
                mousePos = self.graphicsView.mapToScene(event.pos())
                self.Update_Position(mousePos.x(), mousePos.y(), z)
            
        return super().eventFilter(source,event)
    
    def Zoom_In_Graph(self):
        global graphview_scale
        scale = 1.25
        graphview_scale *= scale
        self.graphicsView.scale(scale, scale)
        
    def Zoom_Out_Graph(self):
        global graphview_scale
        scale = 0.8
        graphview_scale *= scale
        self.graphicsView.scale(scale, scale)
        
    def One_To_One_Graph(self):
        global graphview_scale
        scale = 1/graphview_scale
        graphview_scale = 1
        self.graphicsView.scale(scale, scale)
    """"""
    
    def Update_Position(self, _x, _y, _z):
        """Update Position to 2D, 3D viewports and spinboxes. The viewports will update in 10fps maximum

        Args:
            _x (float): X position
            _y (float): Y position
            _z (float): Z position
        """
        global x, y, z, MAX_X, MAX_Y, MIN_Z, prev_time
        x = clip(_x, 0, MAX_X)
        y = clip(_y, 0, MAX_Y)
        z = clip(_z, MIN_Z, 0)
        self.x_pos_spinbox.setValue(x)
        self.y_pos_spinbox.setValue(y)
        self.z_pos_spinbox.setValue(z)
        
        now_time = time.time()
        if now_time - prev_time > 1/10:
            self.scene.removeItem(self.tool_head)
            self.tool_head = self.scene.addEllipse(x-1.5, y-1.5, 3, 3, QPen(QtCore.Qt.red), QBrush(QtCore.Qt.red))
            
            self.fileviewer3d.Set_Toolhead_Pos(x, y, z)
        
        prev_time = now_time
        
    def Draw_Lines(self):
        """Draw toolpath on 2D, 3D viewports"""
        if len(points) != 0:
            new_points = []
            _x, _y, _z = [], [], []
            for point in points:
                x = clip(point[0], 0, MAX_X)
                y = clip(point[1], 0, MAX_Y)
                z = clip(point[2], MIN_Z, 0)
                        
                _x.append(x)
                _y.append(y)
                _z.append(z)
                new_points.append([x, y, z])
            
            for line in self.lines:
                self.scene.removeItem(line)
            
            self.lines.clear()
            pen = QPen(QtCore.Qt.green)
            pen.setCosmetic(True)
            for i in range(len(new_points) - 1):
                self.lines.append(self.scene.addLine(QLineF(new_points[i][0],new_points[i][1], new_points[i+1][0], new_points[i+1][1]), pen))
                
            # 3D
            try:
                self.lines_3d.pop(0).remove()
            except:
                pass
            self.lines_3d = self.fileviewer3d.canvas.axes.plot(_x,_y,_z, color='green')
            self.fileviewer3d.canvas.draw()
    
    def Add_To_Log(self, log):
        """Add to log

        Args:
            log (str): Log
        """
        if log == 2:
            QMessageBox.critical(self, "Error", "Error! Can not communicate!")
            log = "Error! Can not communicate!"
        #self.log_textbox.setText(f"{#self.log_textbox.toPlainText()}\n{log}")
    
    def Start_serial(self):
        """Start MDX-20 and Arduino Serial"""
        global mdx_port, arduino_port
        mdx_port = config['Serial']['mdx_port']
        arduino_port = config['Serial']['arduino_port']
        
        dlg = SelectSerialDialog(mdx_port, arduino_port)
        if dlg.exec_():
            mdx_port = dlg.mdx_port
            arduino_port = dlg.arduino_port
            
            if mdx_port == None:
                return
            else: 
                serial_started = mdx20.OpenSerial(mdx_port)
                if serial_started == False:
                    QMessageBox.critical(self, "Error", "Error! Can not start serial!")
                    self.Main_Control.setEnabled(False)
                else:
                    self.init_machine()
            
            if arduino_port == None:
                self.tabWidget_2.setTabEnabled(1, False)
                return
            else:
                self.tabWidget_2.setTabEnabled(1, True)
                arduino.OpenSerial(arduino_port)
                self.Load_Mesh()
        
    def Move(self, _x, _y, _z):
        """Move bed and/or toolhead

        Args:
            _x (float): X position
            _y (float): Y position
            _z (float): Z position
        """
        self.Update_Position(_x, _y, _z)
        log = mdx20.Move(x,y,z)
        self.Add_To_Log(log)
        
    def Go(self):
        """Go button. Move using spinboxes values."""
        x = self.x_pos_spinbox.value()
        y = self.y_pos_spinbox.value()
        z = self.z_pos_spinbox.value()
        self.Move(x, y, z)
        
    def Set_Origin(self):
        """Set origin (X, Y) at current position"""
        global x0, y0
        x0, y0 = x, y
        self.x0_spinbox.setValue(x)
        self.y0_spinbox.setValue(y)
        
        self.scene.removeItem(self.origin)
        self.origin = self.scene.addEllipse(x0-1.5, y0-1.5, 3, 3, QPen(QtCore.Qt.blue), QBrush(QtCore.Qt.blue))
        
        self.fileviewer3d.Set_Origin_Pos(x0, y0, z0)
        self.Check_Use_Mesh()
        self.Draw_Lines()
    
    def Set_Z(self):
        """Set Z-offset for toolpath"""
        global z0
        z0 = z
        self.z0_spinbox.setValue(z)
        self.fileviewer3d.Set_Origin_Pos(x0, y0, z0)
        self.Draw_Lines()
        
    def Spindle(self,state):
        """Set spindle on/off

        Args:
            state (int): QtCore.Qt.Checked, QtCore.Qt.Unchecked
        """
        if state == QtCore.Qt.Checked:
            log = mdx20.Send_Data("!MC1;")
        else:
            log = mdx20.Send_Data("!MC0;")
        
        self.Add_To_Log(log)
        
    """Update delta_xyz when spinboxes change"""
    def Delta_XY_changed(self, value):
        global delta_xy
        delta_xy = value
        
    def Delta_Z_changed(self, value):
        global delta_z
        delta_z = value
    """"""
    
    """Update X0, Y0, Z0 when spinboxes change"""    
    def x0_changed(self, value):
        global x0
        x0 = value
        
        self.scene.removeItem(self.origin)
        self.origin = self.scene.addEllipse(x0-1.5, y0-1.5, 3, 3, QPen(QtCore.Qt.blue), QBrush(QtCore.Qt.blue))
        self.fileviewer3d.Set_Origin_Pos(x0, y0, z0)
        self.Check_Use_Mesh()
        self.Draw_Lines()
        
    def y0_changed(self, value):
        global y0
        y0 = value
        self.scene.removeItem(self.origin)
        self.origin = self.scene.addEllipse(x0-1.5, y0-1.5, 3, 3, QPen(QtCore.Qt.blue), QBrush(QtCore.Qt.blue))
        self.fileviewer3d.Set_Origin_Pos(x0, y0, z0)
        self.Check_Use_Mesh()
        self.Draw_Lines()
        
    def z0_changed(self, value):
        global z0
        z0 = value
        self.fileviewer3d.Set_Origin_Pos(x0, y0, z0)
        self.Check_Use_Mesh()
        self.Draw_Lines()
    """"""
        
    def Speed_changed(self, value):
        """Update speed when spinbox changes"""
        global speed
        speed = value
        log = mdx20.Send_Data("V{:.1f};".format(speed))
        self.Add_To_Log(log)
        
    def Speed_override_changed(self, state):
        """Set speed override"""
        global speed_override
        speed_override = state
        
    def openFile(self):
        """Open path file using File -> Open (Ctrl+O)
            Current supports:
                - Basic *.rol, *.prn instructions (V, Z, !MCn). Files exported from FlatCAM RML-1 post-processing.
                - Basic *.nc, *.gcode instructions (G00, G01, M3, M5). File exported from FlatCAM Mach3 post-processing.
            Opened file will be read, draw paths on 2D, 3D viewports and add to instructions list.
        """
        global instructionsList
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "",\
            "All supported files (*.rol *.prn *.nc *.gcode);;RML-1 (*.rol *.prn);;NC Gcode (*.nc *.gcode);;All Files (*)", options=options)
        if fileName == "":
            return
        file = open(fileName, 'r')
        
        if pathlib.Path(fileName).suffix.lower() == ".nc" or pathlib.Path(fileName).suffix.lower() == ".gcode":
            lines = nc2rol.nc2rol(file).splitlines()
        else:
            lines = file.read().splitlines()
            
        file.close()
        
        self.instructions_list.clear()
        self.instructions_list.addItems(lines)
        instructionsList = lines.copy()
            
        points_data.clear()
        for instruction in lines:
            if instruction != "":
                if instruction[0] == "Z":
                    x, y, z = instruction[1:-1].split(",")
                    x = inch2mm(float(x))
                    y = inch2mm(float(y))
                    z = inch2mm(float(z))
                    points_data.append([x,y,z])
                    
        self.Check_Use_Mesh()
        self.Draw_Lines()
        
        self.progress_label.setText(f"{currentInstruction}/{len(lines)}")
        self.progressBar.setValue(0)
                        
    def Instruction_row_changed(self, currentRow):
        """Instructions list row changed -> update progress"""
        global currentInstruction
        currentInstruction = currentRow
        self.progress_label.setText(f"{currentInstruction}/{len(instructionsList)}")
        self.progressBar.setValue(int(currentInstruction*100/len(instructionsList)))
    
    """Start milling job"""
    def Start_Job(self):
        global started, speed
        if started == True:
            self.start_btn.setText("Start")
            started = False
            self.spindle_checkbox.setChecked(False)
            self.Move(x, y, 0)
        else:
            self.start_btn.setText("Stop")
            self.spindle_checkbox.setChecked(True)
            started = True
            
            self.worker = WorkerThread()
            self.worker.start()
            self.worker.update.connect(self.worker_update)
            self.worker.finished.connect(self.worker_finished)
        
        log = mdx20.Send_Data("V{:.1f};".format(speed))
        self.Add_To_Log(log)    
        
    def worker_update(self, val):
        self.instructions_list.setCurrentRow(val)
        instruction = instructionsList[val]
        if instruction != "":
            if instruction[0] == "Z":
                xt, yt, zt = instruction[1:-1].split(",")
                xt = inch2mm(float(xt))
                yt = inch2mm(float(yt))
                zt = inch2mm(float(zt))
                self.Update_Position(xt, yt, zt)
            elif instruction[0] == "V" and speed_override == False:
                self.speed_spinbox.setValue(float(instruction[1:-1])) 
        
    def worker_finished(self):
        global started
        started = False
        self.start_btn.setText("Start")
        started = False
        self.spindle_checkbox.setChecked(False)
        self.Move(x, y, 0)
    """"""
        
    def AutoZ_Down(self):
        """Z-probe until Arduino senses a contact"""
        global z
        mdx20.Send_Data("V15.0")
        while True:
            read_data = arduino.Read_Data()
            if read_data == 0:
                return
            elif read_data == 2:
                return "error"
            mdx20.Move(x,y,z)
            z = z - 0.0127
            
    def AutoZ(self):
        """Z-probe and set Z-offset"""
        if self.AutoZ_Down() == "error":
            return
        self.Set_Z()
        self.Move(x, y, 0)
    
    """Mesh bed leveling"""   
    def x_bl_changed(self, value):
        global mesh_bl_x
        if value >= mesh_tr_x:
            self.x_bl_spinbox.setValue(mesh_bl_x)
            return
        mesh_bl_x = value
        self.update_table_size()
    def y_bl_changed(self, value):
        global mesh_bl_y
        if value >= mesh_tr_y:
            self.x_bl_spinbox.setValue(mesh_bl_y)
            return
        mesh_bl_y = value
        self.update_table_size()
    def x_tr_changed(self, value):
        global mesh_tr_x
        if value <= mesh_bl_x:
            self.x_tr_spinbox.setValue(mesh_tr_x)
            return
        mesh_tr_x = value
        self.update_table_size()
    def y_tr_changed(self, value):
        global mesh_tr_y
        if value <= mesh_bl_y:
            self.y_tr_spinbox.setValue(mesh_tr_y)
            return
        mesh_tr_y = value
        self.update_table_size()
    def h_grid_changed(self, value):
        global h_grid
        h_grid = value
        self.update_table_size()
    def v_grid_changed(self, value):
        global v_grid
        v_grid = value
        self.update_table_size()
        
    def Set_bl(self):
        global mesh_bl_x, mesh_bl_y
        mesh_bl_x = x; mesh_bl_y = y
        self.x_bl_spinbox.setValue(x)
        self.y_bl_spinbox.setValue(y)
        self.update_table_size()
    def Set_tr(self):
        global mesh_tr_x, mesh_tr_y
        mesh_tr_x = x; mesh_tr_y = y
        self.x_tr_spinbox.setValue(x)
        self.y_tr_spinbox.setValue(y)
        self.update_table_size()
        
    def update_table_size(self):
        x_step = (mesh_tr_x - mesh_bl_x) / h_grid
        y_step = (mesh_tr_y - mesh_bl_y) / v_grid
        x_label = [str("{:.3f}".format(x)) for x in np.arange(mesh_bl_x,mesh_tr_x+0.01,x_step)]
        y_label = [str("{:.3f}".format(y)) for y in np.arange(mesh_bl_y,mesh_tr_y+0.01,y_step)]
        self.mesh_table.setRowCount(len(y_label))
        self.mesh_table.setColumnCount(len(x_label))
        self.mesh_table.setHorizontalHeaderLabels(x_label)
        self.mesh_table.setVerticalHeaderLabels(y_label)
        
    def update_table_value(self):
        for i in range(len(mesh_bed)):
            row = int(i / (h_grid + 1))
            col = int(i % (h_grid + 1))
            
            item = QTableWidgetItem()
            item.setText(str("{:.3f}".format(mesh_bed[i][2])))
            self.mesh_table.setItem(row, col if row%2 == 0 else h_grid - col, item)
        
    def Save_Mesh(self):
        arr = [[h_grid, v_grid], mesh_bed]
        arr = np.array(arr, dtype=object)
        np.save(path + '/config/mesh.npy',arr)
        
    def Load_Mesh(self):
        global mesh_bed, h_grid, v_grid, mesh_bl_x, mesh_bl_y, mesh_tr_x, mesh_tr_y
        try:
            arr = np.load(path + "/config/mesh.npy", allow_pickle=True).tolist()
        except:
            return
        h_grid, v_grid = arr[0]
        mesh_bed = arr[1]
        if len(mesh_bed) > 0:
            mesh_bl_x, mesh_bl_y = mesh_bed[0][0], mesh_bed[0][1]
            mesh_tr_x = mesh_bed[h_grid + 1][0]
            mesh_tr_y = mesh_bed[len(mesh_bed) - 1][1]
            self.x_bl_spinbox.setValue(mesh_bl_x)
            self.y_bl_spinbox.setValue(mesh_bl_y)
            self.x_tr_spinbox.setValue(mesh_tr_x)
            self.y_tr_spinbox.setValue(mesh_tr_y)
            self.h_grid_spinbox.setValue(h_grid)
            self.v_grid_spinbox.setValue(v_grid)
            self.update_table_size()
            self.update_table_value()
            self.meshbedviewer.Plot_Mesh(mesh_bed)
        
    def Clear_Mesh(self):
        global use_mesh
        mesh_bed.clear()
        for i in range(self.mesh_table.rowCount() * self.mesh_table.columnCount()):
            item = QTableWidgetItem()
            item.setText("")
            self.mesh_table.setItem(0, i, item)
            
        self.meshbedviewer.canvas.axes.clear()
        self.meshbedviewer.canvas.draw()
        use_mesh = False
        self.use_mesh_checkbox.setChecked(False)
        self.Check_Use_Mesh()
        self.Draw_Lines()
    
    def Relevel(self):
        global mesh_bed
        selected = self.mesh_table.selectedItems()
        save_z = z
        for i in selected:
            row = i.row()
            column = i.column()
            if row % 2 != 0:
                column_m = h_grid - column
            else:
                column_m = column
                
            current = mesh_bed[(h_grid+1)*row + column_m]
            self.Move(current[0], current[1], z)
            time.sleep(1)
            if self.AutoZ_Down() == "error":
                return
            
            mesh_bed[(h_grid+1)*row + column_m] = [current[0], current[1], z]
            self.update_table_value()
            self.meshbedviewer.Plot_Mesh(mesh_bed)
            
            self.Move(x, y, save_z)
        
    def Use_Mesh(self, value):
        global use_mesh
        if len(mesh_bed) > 0:
            use_mesh = value
        else:
            self.use_mesh_checkbox.setChecked(False)
            
        self.Check_Use_Mesh()
        self.Draw_Lines()
            
    def Check_Use_Mesh(self):
        global points, instructionsList
        if use_mesh == False:
            self.fileviewer3d.Remove_Mesh()
            points.clear()
            for i in points_data:
                points.append([i[0] + x0, i[1] + y0, i[2] + z0])
        else:
            self.fileviewer3d.Plot_Mesh(mesh_bed)
            if len(points_data) > 0:
                origin = [x0, y0, z0]
                points = PointsOnMesh.PointsOnMesh(mesh_bed, origin, points_data)
                for i in range(len(points)):
                    points[i][2] += z0
                
        ZinstrucCount = 0
        for i in range(len(instructionsList)):
            if instructionsList[i] != "":
                if instructionsList[i][0] == 'Z':
                    instructionsList[i] = "Z{:.1f},{:.1f},{:.1f}".format(mm2inch(points[ZinstrucCount][0]),mm2inch(points[ZinstrucCount][1]),mm2inch(points[ZinstrucCount][2]))
                    ZinstrucCount += 1
        
        self.instructions_list.clear()
        self.instructions_list.addItems(instructionsList)
        
    
    def Mesh_Bed(self):
        self.worker = MeshBedWorker()
        self.worker.start()
        self.worker.finished.connect(lambda: self.Move(x, y, 0))
        self.worker.update_meshviewer.connect(lambda: self.meshbedviewer.Plot_Mesh(mesh_bed))
        self.worker.update_table_value.connect(lambda: self.update_table_value())
    """"""
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    """Theme"""
    file = QFile(":/dark/stylesheet.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())
    
    window = MainWindow()
    window.show()
    app.exec_()
    
    if mdx_port != None:
        config['Serial']['mdx_port'] = mdx_port
        config['Serial']['arduino_port'] = arduino_port if arduino_port != None else "None"
        
        config['Origin']['x'] = str(x0)
        config['Origin']['y'] = str(y0)
        config['Origin']['z'] = str(z0)
        with open(path + '/config/config.ini', 'w') as configfile:
            config.write(configfile)