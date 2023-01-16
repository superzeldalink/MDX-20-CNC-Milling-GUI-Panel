from utils import *

def nc2rol(nc):
    """Convert NC/Gcode into RML-1 language
        - M5/M05 -> !M0;
        - M3/M03 -> !M1;
        - G0/G00 -> V15;Zx,y,z;
        - G1/G01 -> V02;Zx,y,z;

    Args:
        nc (file): NC/Gcode file

    Returns:
        str: Converted RML-1
    """
    rol = []
    x, y, z = 0, 0, 0
    for line in nc.read().splitlines():
        if line != "":
            line = line.split(" ")
            op = line[0]
            arg = line[1:]
            # pass
            if op == "M05" or op == "M5":
                rol.append("!M0;")
            elif op == "M03" or op == "M3":
                rol.append("!M1;")
            elif op == "G00" or op == "G0":
                for pos in arg:
                    if pos != "":
                        if pos[0] == "X":
                            x = float(pos[1:])
                            x = mm2inch(x)
                        elif pos[0] == "Y":
                            y = float(pos[1:])
                            y = mm2inch(y)
                        elif pos[0] == "Z":
                            z = float(pos[1:])
                            z = mm2inch(z)
                rol.append("V15.0;")
                rol.append("Z{:.1f},{:.1f},{:.1f};".format(x,y,z))
            elif op == "G01" or op == "G1":
                for pos in arg:
                    if pos != "":
                        if pos[0] == "X":
                            x = float(pos[1:])
                            x = mm2inch(x)
                        elif pos[0] == "Y":
                            y = float(pos[1:])
                            y = mm2inch(y)
                        elif pos[0] == "Z":
                            z = float(pos[1:])
                            z = mm2inch(z)
                rol.append("V2.0;")
                rol.append("Z{:.1f},{:.1f},{:.1f};".format(x,y,z))
    
    rol_file = "\n"
    for line in rol:
        rol_file += line + "\n"
    rol_file += "\n"
    return rol_file