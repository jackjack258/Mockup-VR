import viz
import vizshape

from MyVecTypes import *

#v is a normalized directional vector 
# based on formula
# new_pos = old_pos + (distance/vec_magnitude * vec), magnitude is 1 if normalized.
def pointAlongVector(start_pos, direction_vec, distance):
    if type(direction_vec) is MyVec3:
        return start_pos + (direction_vec * distance)

def dot(v1, v2):    
    if type(v1) is MyVec3 and type(v2) is MyVec3:
        return (v1.x * v2.x) + (v1.y * v2.y) + (v1.z * v2.z)
    else:
        raise Exception("Need to use MyVec3 types")
		
#https://www.statology.org/cross-product-python/
#Cross Product = [(A2*B3) - (A3*B2), 
#   (A3*B1) - (A1*B3), 
#   (A1*B2) - (A2*B1)]
def cross(self, v1, v2):
	if type(v1) is MyVec3 and type(v2) is MyVec3:
		result = MyVec3()
		result.x = (v1.y * v2.z) - (v1.z * v2.y)
		result.y = (v1.z * v2.x) - (v1.x * v2.z)
		result.z = (v1.x * v2.y) - (v1.y * v2.x)
		return result
	else:
		raise Exception("Need to use MyVec3 types")

#The points are just plain python Arrays
def drawLine(p1, p2, lineWidth=2, color=viz.WHITE):
	viz.startLayer(viz.LINES)
	viz.lineWidth(lineWidth)
	viz.vertexColor(color)
	viz.vertex(p1)
	viz.vertex(p2)
	return viz.endLayer()
	
#The points are just plain python Arrays
def drawPoint(p1, pointSize=10, color=viz.WHITE):
	viz.startLayer(viz.POINTS)
	viz.pointSize(pointSize)
	viz.vertexColor(color)
	viz.vertex(p1)
	layer = viz.endLayer()
	layer.setCenter(p1)
	return layer
	
def show_X_Axis():
	xplane = vizshape.addGrid(size=[100.0, 100.0], step=10,  axis=vizshape.AXIS_Y)
	xplane.color(viz.RED)
	xplane.alpha(0.7)
	return xplane
	
def show_Y_Axis():
	yplane = vizshape.addGrid(size=[100.0, 100.0], step=10, axis=vizshape.AXIS_Z)
	yplane.color(viz.GREEN)
	yplane.alpha(0.7)
	return yplane

