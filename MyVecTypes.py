#Andrew Grace
#Nov 2021

#Quick vector containers for testing

# x, y, z
# i, j, k

ALMOST_ZERO=0.000001

import math

class MyVec3:
    def __init__(self, x=None, y=None, z=None):
        self._data = [x, y, z]
        self._normal = None

    def __repr__(self):
        return str("MyVec3: [{}, {}, {}]".format(*self._data))

    def __str__(self):
        return str("MyVec3: [{}, {}, {}]".format(*self._data))

#    @property
#    def array(self):
#        return self._data
    
#    @property
#    def normal(self):
#        return self._normal
#    
#    @normal.setter
#    def normal(self,value):
#        self._normal = value

    @property
    def x(self):
        return self._data[0]

    @x.setter
    def x(self, value):
        self._data[0] = value

    @property
    def y(self):
        return self._data[1]

    @y.setter
    def y(self, value):
        self._data[1] = value    

    @property
    def z(self):
        return self._data[2]

    @z.setter
    def z(self, value):
        self._data[2] = value    

#---------------------------------

    @property
    def i(self):
        return self._data[0]

    @i.setter
    def i(self, value):
        self._data[0] = value

    @property
    def j(self):
        return self._data[1]

    @j.setter
    def j(self, value):
        self._data[1] = value    

    @property
    def k(self):
        return self._data[2]

    @k.setter
    def k(self, value):
        self._data[2] = value   

#------------------------------
#Opeators
    def __add__(self, other_val):
        result = MyVec3()
        result.x = self.x + other_val.x
        result.y = self.y + other_val.y
        result.z = self.z + other_val.z
        return result
        
    def __sub__(self,other_val):
        result = MyVec3()
        result.x = self.x - other_val.x
        result.y = self.y - other_val.y
        result.z = self.z - other_val.z
        return result
        
    def __mul__(self,other_val):
        if type(other_val) is MyVec3:        
            result = MyVec3()
            result.x = self.x * other_val.x
            result.y = self.y * other_val.y
            result.z = self.z * other_val.z
            return result
        else:
            result = MyVec3(self.x, self.y, self.z)
            result.x *= other_val
            result.y *= other_val
            result.z *= other_val
            return result
        
#------------------------------
    def tolist(self):
        return self._data

    def normalize(self):
        v = self
        magnitude = math.sqrt((v.x * v.x) + (v.y * v.y) + (v.z * v.z))
        
        if magnitude < ALMOST_ZERO:
            return MyVec3(0.0, 0.0, 0.0)
        
        self.x = v.x/magnitude
        self.y = v.y/magnitude
        self.z = v.z/magnitude

# x, y, z, w
# i, j, k, l


class MyVec4(MyVec3):
    def __init__(self, x=None, y=None, z=None, w=None):
        self._data = [x, y, z, w]

    def __repr__(self):
        return str("MyVec4: [{}, {}, {}, {}]".format(*self._data))

    def __str__(self):
        return str("MyVec4: [{}, {}, {}, {}]".format(*self._data))

    #----------------------

    @property
    def w(self):
        return self._data[3]

    @w.setter
    def w(self, value):
        self._data[3] = value

    @property
    def l(self):
        return self._data[3]

    @l.setter
    def l(self, value):
        self._data[3] = value
        

