import numpy as np

def GetCenter(corner):
    x1, y1 = corner[0]
    x2, y2 = corner[3]
    x3, y3 = corner[1]
    x4, y4 = corner[2]

    x  = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    y  = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    return [x, y]

def avgRotation(original, measured):
    original_x1, original_y1 = original[0]
    original_x2, original_y2 = original[3]
    original_x3, original_y3 = original[1]
    original_x4, original_y4 = original[2]
    origCenter_x, origCenter_y = GetCenter(original)
    original_r1 = np.arctan2(original_y1 - origCenter_y, original_x1 - origCenter_x)
    original_r2 = np.arctan2(original_y2 - origCenter_y, original_x2 - origCenter_x)
    original_r3 = np.arctan2(original_y3 - origCenter_y, original_x3 - origCenter_x)
    original_r4 = np.arctan2(original_y4 - origCenter_y, original_x4 - origCenter_x)
    
    measured_x1, measured_y1 = measured[0]
    measured_x2, measured_y2 = measured[3]
    measured_x3, measured_y3 = measured[1]
    measured_x4, measured_y4 = measured[2]
    measuredCenter_x, measuredCenter_y = GetCenter(measured)
    measured_r1 = np.arctan2(measured_y1 - measuredCenter_y, measured_x1 - measuredCenter_x)
    measured_r2 = np.arctan2(measured_y2 - measuredCenter_y, measured_x2 - measuredCenter_x)
    measured_r3 = np.arctan2(measured_y3 - measuredCenter_y, measured_x3 - measuredCenter_x)
    measured_r4 = np.arctan2(measured_y4 - measuredCenter_y, measured_x4 - measuredCenter_x)
    measures = [
        [measured_r1 - original_r1],
        [measured_r2 - original_r2],
        [measured_r3 - original_r3],
        [measured_r4 - original_r4]
    ]

    return np.mean(measures), np.std(measures)

def rotate(point, center=[0,0], angle=0):
    x, y = point
    center_x, center_y = center
    newX = center_x + (x - center_x) * np.cos(angle) - (y - center_y) * np.sin(angle)
    newY = center_y + (x - center_x) * np.sin(angle) + (y - center_y) * np.cos(angle)
    return [newX, newY]

def translate(point, trans):
    x, y = point
    _x, _y = trans
    return x + _x, y + _y

def Calculate(points, original, measured):
    o_center = GetCenter(original)
    r_center = GetCenter(measured)
    deg, std = avgRotation(original, measured)

    dx = r_center[0] - o_center[0]
    dy = r_center[1] - o_center[1]
    
    offset = [dx,dy]
        
    return offset, deg, std

def GetAlignedPoints(points, offset, deg):
    dx, dy = offset
    new_points = []
    for point in points:
        point_2d = [point[0],point[1]]
        new_point = translate(rotate(point_2d, [dx,dy], deg), [dx,dy])
        new_points.append([new_point[0],new_point[1],point[2]])
        
    return new_points