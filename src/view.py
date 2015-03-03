'''
Ian Tibbetts
Colby College CS251 Spring '15
Professors Stephanie Taylor and Bruce Maxwell
'''
import numpy as np
import numpy.matlib as npm
from math import cos, sin, pi

def normalize(v):
	'''
	return the given vector with unit length
	'''
	return v/np.linalg.norm(v)

class View:
		
	def __init__(self, vrp=[0.5,0.5,1], vpn=[0,0,-1], vup=[0,1,0], u=[1,0,0],
				extent=[1,1,1], screen=[400,400], offset=[20,20], 
				verbose=False):
		'''
		Constructor for the view class, with defaults for all parameters
		'''
		self.vrp = np.matrix(vrp, np.float)
		self.vpn = np.matrix(vpn, np.float)
		self.vup = np.matrix(vup, np.float)
		self.u = np.matrix(u, np.float)
		self.extent = np.matrix(extent, np.float)
		self.screen = np.matrix(screen, np.float)
		self.offset = np.matrix(offset, np.float)
		self.verbose = verbose
	
	def reset(self):
		'''
		resets all parameters of this view to their defaults
		'''
		self.__init__()
		
	def clone(self):
		'''
		returns a deep clone of this view
		'''
		return View(self.vrp, self.vpn, self.vup, self.u, self.extent, 
					self.screen, self.offset, self.verbose)
	
	def getTranslate(self, dx, dy, dz=0):
		'''
		returns a 4x4 translation matrix
		'''
		return np.asmatrix([[1,0,0,dx],
							[0,1,0,dy],
							[0,0,1,dz],
							[0,0,0,1]],
							np.float)
		
	def getScale(self, sx, sy, sz=1):
		'''
		returns a 4x4 scale matrix
		'''
		return np.asmatrix([[sx,0,0,0],
							[0,sy,0,0],
							[0,0,sz,0],
							[0,0,0,1]],
							np.float)
		
	def rotateVRC(self, angUp, angU):
		'''
		rotate the view about the up and u axes by the given angles (in degrees)
		'''
		centerVV = self.vrp + self.vpn * self.extent[0,2] * 0.5
		t1 = self.getTranslate(-centerVV[0,0], -centerVV[0,1], -centerVV[0,2])
		Rxyz = self.getRotateXYZ(self.u, self.vup, self.vpn)
		r1 = self.getRotateY(angUp)
		r2 = self.getRotateX(angU)
		t2 = self.getTranslate(centerVV[0,0], centerVV[0,1], centerVV[0,2])
		tvrc = np.zeros((4,4), np.float)
		tvrc[:,:3] = np.vstack((self.vrp, self.u, self.vup, self.vpn))
		tvrc[0,3] = 1 # vrp is a point so homogeneous of 1
		tvrc = (t2*Rxyz.T*r2*r1*Rxyz*t1*tvrc.T).T
		self.vrp = 	tvrc[0,:3].copy()
		self.u = 	normalize(tvrc[1,:3]).copy()
		self.vup = 	normalize(tvrc[2,:3]).copy()
		self.vpn = 	normalize(tvrc[3,:3]).copy()
		
	def getRotateXYZ(self, u, v, w):
		'''
		returns a 4x4 rotation matrix to align to the given axes
		'''
		m = npm.identity(4, np.float)
		rot = np.vstack((u, v, w))
		m[0:3,0:3] = rot
		return m
	
	def getRotateX(self, a):
		'''
		given an angle (in degrees) return the 4x4 rotation matrix about x
		'''
		a *= pi/180.0 # convert to radians
		return np.asmatrix([[1,0,0,0],
							[0,cos(a),sin(a),0],
							[0,-sin(a),cos(a),0],
							[0,0,0,1]],
							np.float)
		
	def getRotateY(self, a):
		'''
		given an angle (in degrees) return the 4x4 rotation matrix about y
		'''
		a *= pi/180.0 # convert to radians
		return np.asmatrix([[cos(a),0,-sin(a),0],
							[0,1,0,0],
							[sin(a),0,cos(a),0],
							[0,0,0,1]],
							np.float)
		
	def getRotateZ(self, a):
		'''
		given an angle (in degrees) return the 4x4 rotation matrix about z
		'''
		a *= pi/180.0 # convert to radians
		return np.asmatrix([[cos(a),sin(a),0,0],
							[-sin(a),cos(a),0,0],
							[0,0,1,0],
							[0,0,0,1]],
							np.float)
		
	def build(self):
		'''
		returns the view transformation matrix for this view instance
		'''
		# compute orthonormal axes
		tu = npm.cross(self.vup, self.vpn)
		tvup = npm.cross(self.vpn, tu)
		tvpn = self.vpn.copy()
		if self.verbose:
			print("not normalized vup:")
			print(tvup)
			print("not normalized vpn:")
			print(tvpn)
			print("not normalized u:")
			print(tu)
		tvup = normalize(tvup)
		tvpn = normalize(tvpn)
		tu = normalize(tu)
		if self.verbose:
			print("normalized vup:")
			print(tvup)
			print("normalized vpn:")
			print(tvpn)
			print("normalized u:")
			print(tu)
		self.vup = tvup.copy()
		self.vpn = tvpn.copy()
		self.u = tu.copy()
		
		# initialize tho vtm matrix that will be returned
		vtm = npm.identity(4, np.float)
		if self.verbose: print("after vtm init:\n%s" % vtm)
		
		# translate vrp to origin
		vtm = self.getTranslate(-self.vrp[0,0], -self.vrp[0,1], 
								-self.vrp[0,2]) * vtm
		if self.verbose: print("after vtm translate to origin:\n%s" % vtm)
		
		# align the vtm ref coords
		vtm = self.getRotateXYZ(tu, tvup, tvpn) * vtm
		if self.verbose: print("after vtm align axes:\n%s" % vtm)
		
		# translate to get lower left corner to zero
		vtm = self.getTranslate(self.extent[0,0]*0.5, 
								self.extent[0,1]*0.5) * vtm
		if self.verbose: print("after vtm translate to zero:\n%s" % vtm)
		
		# scale to normalize
		vtm = self.getScale(1.0/self.extent[0,0], 1.0/self.extent[0,1], 
							1.0/self.extent[0,2]) * vtm
		if self.verbose: print("after vtm normalize:\n%s" % vtm)
		
		# scale to screen
		vtm = self.getScale(-self.screen[0,0], -self.screen[0,1]) * vtm
		if self.verbose: print("after vtm scale to screen:\n%s" % vtm)
		
		# translate to screen
		vtm = self.getTranslate(self.screen[0,0] + self.offset[0,0], 
								self.screen[0,1] + self.offset[0,1]) * vtm
		if self.verbose: print("after vtm translate to screen:\n%s" % vtm)
		
		# return the complete vtm matrix
		return vtm

if __name__ == "__main__":
	
	print("testing view")
	verbose = True
	view = View(verbose=verbose)
	print(view.build())
		