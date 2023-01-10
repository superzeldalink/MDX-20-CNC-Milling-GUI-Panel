import trimesh
from scipy.spatial import Delaunay

def PointsOnMesh(mesh_points, origin, points):
    """Project points on mesh bed

    Args:
        mesh_points: Mesh bed points
        origin ([x0, y0, z0]): XY Origin and Z-offset
        points: Path points

    Returns:
        points: Projected path points
    """
    point_2d = []
    for i in mesh_points:
        point_2d.append([i[0], i[1]])
        
    offset_points = []
    for i in points:
        offset_points.append([i[0] + origin[0], i[1] + origin[1], i[2] + origin[2]])

    tri = Delaunay(point_2d)
    mesh = trimesh.Trimesh(mesh_points, tri.simplices)
    distance = mesh.nearest.signed_distance(offset_points).tolist()
    
    projected_points = offset_points
    for i in range(len(offset_points)):
        projected_points[i][2] += offset_points[i][2] + distance[i]
    
    return projected_points