import serial, time
import serial.tools.list_ports
from utils import *

BAUDRATE = 9600

ser = None

def OpenSerial(port):
    """Open Serial RS232 connection

    Returns:
        bool: True for success, False of failed
    """
    
    global ser
    try:
        ser = serial.Serial(port, BAUDRATE, rtscts=True, dsrdtr=True)
        ser.bytesize = serial.EIGHTBITS #number of bits per bytes
        ser.parity = serial.PARITY_NONE #set parity check: no parity
        ser.stopbits = serial.STOPBITS_ONE #number of stop bits
        ser.open()
    except serial.SerialException as e:
        if e.errno == None:
            return True
        return False
    return True

def Send_Data(data):
    """Send data to MDX-20 over serial

    Returns:
        str/int: Return data when success, 2 for failed communication, e.errno for other errors
    """
    try:
        if ser != None:
            if ser.is_open:
                ser.setRTS(True)
                ser.setDTR(True)
                if not ser.getCTS() or not ser.getDSR():
                    # print("Waiting...")
                    while not ser.getCTS() or not ser.getDSR():
                        time.sleep(0.25)
                    
                ser.write((data + "\n\r").encode())
                time.sleep(0.02)
                return data
        else:
            return 2
    except serial.SerialException as e:
        return e.errno
    
def Move(x,y,z):
    """Move to XYZ. 
        Attention: XYZ in thou or inch/1000

    Args:
        x (float): X position
        y (float): Y position
        z (float): Z position

    Returns:
        int: Response
    """
    xi = mm2inch(x)
    yi = mm2inch(y)
    zi = mm2inch(z)
    data = "V15;Z{:.1f},{:.1f},{:.1f};".format(xi, yi, zi)
    return Send_Data(data)