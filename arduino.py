import serial
import serial.tools.list_ports

BAUDRATE = 1152000

ser = None

def OpenSerial(port):
    """Open Arduino serial connection

    Returns:
        bool: True for success, False of failed
    """
    
    global ser
    try:
        ser = serial.Serial(port, BAUDRATE)
        ser.open()
    except serial.SerialException as e:
        if e.errno == None:
            return True
        return False
    return True

def Read_Data():
    """Read data from Arduino serial

    Returns:
        str/int: Return data when success, 2 for failed communication, e.errno for other errors
    """
    try:
        if ser != None:
            ser.flushInput()
            ser.flushOutput()
            read  = ser.readline()
            if read != b'0\r\n' and read != b'1\r\n':
                return 1
            else:
                return int(read)
        else:
            return 2
    except serial.SerialException as e:
        return e.errno
    