'''
Ian Tibbetts
Colby College CS251 Spring '15
Professors Stephanie Taylor and Bruce Maxwell
'''
import types
import random
import numpy as np
import analysis
from data import Data
from view import View
import dialog
from optparse import OptionParser
from collections import OrderedDict

# use tkinter for GUI elements
try:
	import tkinter as tk # python 3
	tkf = tk.filedialog
	from tk.colorchooser import askcolor
except ImportError:
	import Tkinter as tk # python 2
	import tkFileDialog as tkf
	from tkColorChooser import askcolor
	
# create a class to build and manage the display
class DisplayApp:

	def __init__(self, width, height, filename=None, verbose=True):
		'''
		Constructor for the display application
		'''
		# make initial fields
		self.verbose = verbose
		self.filename = filename
		self.data = None
		self.activeData = None
		self.width = None
		self.height = None
		self.filename2data = {}
		self.preDefineColors()
		self.preDefineDistributions()
		self.objects = [] # shapes drawn on canvas
		self.objectsResize = [] # shapes being resized, w/ original sizes

		# create a tk object, which is the root window
		self.root = tk.Tk()

		# set up the geometry for the window
		self.root.geometry( "%dx%d+50+30" % (width, height) )
		
		# set the title of the window
		self.root.title("Tibbetts GUI")
		# set the maximum size of the window for resizing
		self.root.maxsize( 1600, 900 )
		
		# set the canvas field to grant access to shape functions
		self.canvas = tk.Canvas( self.root, width=width, height=height )
		self.preDefineShapes()

		# setup the menus
		self.buildMenus()

		# build the controls
		self.buildControlsFrame()

		# build the status bar
		self.buildStatusFrame()

		# pack the Canvas
		self.canvas.pack( expand=tk.YES, fill=tk.BOTH )

		# bring the window to the front
		self.root.lift()

		# - do idle events here to get actual canvas size
		self.root.update_idletasks()

		# set up the key bindings
		self.setBindings()
		
		# set the width and height for updating the screen
		self.width = self.canvas.winfo_width()
		self.height = self.canvas.winfo_height()
		
		# build the axes
		self.buildAxes()
		
		# build the data
		self.buildData()

	def buildAxes(self, axes=[[0,0,0],[1,0,0],
							  [0,0,0],[0,1,0],
							  [0,0,0],[0,0,1]],
				  axeslabels=[[1.05,0,0],
							  [0,1.05,0],
							  [0,0,1.05]]):
		'''
		builds the view transformation matrix [VTM], 
		multiplies the axis endpoints by the VTM, 
		then creates three new line objects, one for each axis
		'''
		if self.verbose: print("building the axes")
		for axis in axes:
			if len(axis) < 4: 
				axis.append(1) # homogeneous coordinate
		for axis in axeslabels:
			if len(axis) < 4:axis.append(1) # homogeneous coordinate
		self.view = View(offset=[self.width*0.1, self.height*0.1],
							screen=[self.width*0.8, self.height*0.8])
		self.baseView = self.view.clone()
		VTM = self.view.build()
		self.axes = np.asmatrix(axes)
		self.axesLabels = np.asmatrix(axeslabels)
		axesPts = (VTM * self.axes.T).T
		labelPts = (VTM * self.axesLabels.T).T
		self.labelStrings = ["x", "y", "z"]
		self.lines = []
		self.labels = []
		for i in range(3):
			self.lines.append(self.canvas.create_line(axesPts[2*i, 0], axesPts[2*i, 1], 
												axesPts[2*i+1, 0], axesPts[2*i+1, 1]))
			self.labels.append(self.canvas.create_text(labelPts[i, 0], labelPts[i, 1], 
												font=("Purina", 20), text=self.labelStrings[i]))

	def buildControlsFrame(self):
		'''
		build the frame and controls
		'''
		if self.verbose: print("building the control frame")
		# make a control frame on the right
		self.rightcntlframe = tk.Frame(self.root)
		self.rightcntlframe.pack(side=tk.RIGHT, padx=2, pady=2, fill=tk.Y)

		# make a separator frame
		tk.Frame( self.root, width=2, bd=1, relief=tk.SUNKEN
				  ).pack( side=tk.RIGHT, padx = 2, pady = 2, fill=tk.Y)

		row=0
		# use a label to set the size of the right panel
		tk.Label( self.rightcntlframe, text="Data"
				  ).grid( row=row, column=1 )
		row+=1

		# make an open button in the frame
		tk.Button( self.rightcntlframe, text="Open", 
				   command=self.openData, width=10
				   ).grid( row=row, column=1 )
		row+=1
		
		self.openFilenames = tk.Listbox(self.rightcntlframe, selectmode=tk.SINGLE, 
										exportselection=0, height=3)
		self.openFilenames.grid( row=row, column=1 )
		row+=1

		# make a clear button in the frame
		tk.Button( self.rightcntlframe, text="Plot Selected", 
				   command=self.plotData, width=10
				   ).grid( row=row, column=1 )
		row+=1

		# make a clear button in the frame
		tk.Button( self.rightcntlframe, text="Clear", 
				   command=self.clearData, width=10
				   ).grid( row=row, column=1 )
		row+=1
		
		self.presetView = tk.StringVar( self.root )
		self.presetView.set("xy")
		tk.OptionMenu( self.rightcntlframe, self.presetView, 
					   "xy", "xz", "yz", command=self.viewPreset
					   ).grid( row=row, column=1 )
		row+=1

		# make a reset button in the frame
		tk.Button( self.rightcntlframe, text="Reset", 
				   command=self.viewPreset, width=10
				   ).grid( row=row, column=1 )
		row+=1

		# size selector
		tk.Label( self.rightcntlframe, text="\nSize"
					   ).grid( row=row, column=1 )
		row+=1

		# make a size mode selector in the frame
		colorModes = [
			("Size By Data", "d"),
			("Selected Size", "s")
		]
		self.sizeModeStr = tk.StringVar()
		self.sizeModeStr.set("d") # initialize
		for text, mode in colorModes:
			b = tk.Radiobutton(self.rightcntlframe, text=text,
							variable=self.sizeModeStr, value=mode, command=self.update)
			b.grid( row=row, column=1 )
			row+=1
			
		# User selected size
		self.sizeOption = tk.StringVar( self.root )
		self.sizeOption.set("7")
		tk.OptionMenu( self.rightcntlframe, self.sizeOption, command=self.update,
					   *range(1,31)).grid( row=row, column=1 )
		row+=1
		
		# shape selector
		tk.Label( self.rightcntlframe, text="\nShape"
					   ).grid( row=row, column=1 )
		row+=1

		# make a shape mode selector in the frame
		colorModes = [
			("Shape By Data", "d"),
			("Selected Shape", "s")
		]
		self.shapeModeStr = tk.StringVar()
		self.shapeModeStr.set("d") # initialize
		for text, mode in colorModes:
			b = tk.Radiobutton(self.rightcntlframe, text=text,
							variable=self.shapeModeStr, value=mode, command=self.update)
			b.grid( row=row, column=1 )
			row+=1
		
		# User selected shape
		self.shapeOption = tk.StringVar( self.root )
		self.shapeOption.set(self.shapeFunctions.keys()[0].capitalize())
		tk.OptionMenu( self.rightcntlframe, self.shapeOption, 
					   *[shape.capitalize() for shape in self.shapeFunctions],
					   command=self.update
					   ).grid( row=row, column=1 )
		row+=1

		# color selector
		tk.Label( self.rightcntlframe, text="\nColor"
					   ).grid( row=row, column=1 )
		row+=1

		# make a color mode selector in the frame
		colorModes = [
			("Color By Data", "d"),
			("Selected Color", "s")
		]
		self.colorModeStr = tk.StringVar()
		self.colorModeStr.set("d") # initialize
		self.colorMode = self.getColorByDepth
		for text, mode in colorModes:
			b = tk.Radiobutton(self.rightcntlframe, text=text,
							variable=self.colorModeStr, value=mode, 
							command=self.setColorMode)
			b.grid( row=row, column=1 )
			row+=1

		# make a button for selecting predefined colors
		self.colorRow = row
		self.colorOption = tk.StringVar( self.root )
		self.colorOption.set("Select Color")
		self.colorMenu = tk.OptionMenu( self.rightcntlframe, self.colorOption, 
					   *self.colors.keys()).grid( row=row, column=1 )
		row+=1
		
		# use a label to set the size of the right panel
		tk.Label( self.rightcntlframe, text="OR"
				  ).grid( row=row, column=1 )
		row+=1
		
		# make a an integer selector for each color band
		tk.Label( self.rightcntlframe, text="Red").grid( row=row, column=0 )
		tk.Label( self.rightcntlframe, text="Green").grid( row=row, column=1 )
		tk.Label( self.rightcntlframe, text="Blue").grid( row=row, column=2 )
		row+=1
		self.redBand = tk.StringVar( self.root )
		self.redBand.set("0")
		tk.OptionMenu( self.rightcntlframe, self.redBand, 
					   *range(256)).grid( row=row, column=0 )
		self.greenBand = tk.StringVar( self.root )
		self.greenBand.set("0")
		tk.OptionMenu( self.rightcntlframe, self.greenBand, 
					   *range(256)).grid( row=row, column=1 )
		self.blueBand = tk.StringVar( self.root )
		self.blueBand.set("0")
		tk.OptionMenu( self.rightcntlframe, self.blueBand, 
					   *range(256)).grid( row=row, column=2 )
		row+=1
		
		# make a create points button in the frame
		self.numPointsDesc = tk.StringVar( self.root )
		self.numPointsDesc.set("\nNumber of Points")
		self.numPointsLabel = tk.Label(self.rightcntlframe, 
									   textvariable=self.numPointsDesc)
		self.numPointsLabel.grid( row=row, column=1 )
		row+=1
		self.numPoints = tk.Entry(self.rightcntlframe, width=10)
		self.numPoints.grid( row=row, column=1 )
		row+=1
		tk.Button( self.rightcntlframe, text="Create Points", 
				   command=self.createRandomDataPoints, width=10 
				   ).grid( row=row, column=1 )
		row+=1
		
	def buildData(self): 
		'''
		build the data on the screen based on the data and filename fields
		Note: this method is the only one that transforms and draws data
		'''
		
		# clean the data on the canvas
		for obj in self.objects:
			self.canvas.delete(obj)
		self.objects = []
		
		# if the data is not set, set according to filename
		if not self.data:
			self.setActiveData()
			if not self.data: 
				return
		
		# prepare to transform the active data to the current view
		VTM = self.view.build()
		viewData = self.activeData.copy()
		
		# transform into view
		viewData = (VTM * viewData.T).T

		# order so that closer objects draw last
		zIndicesSorted = np.argsort(viewData[:, 2].T.tolist()[0])
		
		# transform sorted data to view and draw on canvas
		#dx = 6.0/self.view.extent[0,0] # size of data points
		#dy = 6.0/self.view.extent[0,1]
		for i in zIndicesSorted:
			self.drawObject(viewData[i,0], viewData[i,1], row=i)

	def buildMenus(self):
		'''
		builds the menu bar and contents
		'''
		if self.verbose: print("building the menus")
		# create a new menu
		self.menu = tk.Menu(self.root)

		# set the root menu to our new menu
		self.root.config(menu = self.menu)

		# create a variable to hold the top level menus
		menulist = []

		# create a file menu
		filemenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "File", menu = filemenu )
		menulist.append([filemenu,
						[['Open, Ctrl-O', self.openData], 
						 ['Clear  Ctrl-N', self.clearData], 
						 ['Quit		Ctrl-Q', self.handleQuit]
						 ]])

		# create another menu for color
		colormenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Color", menu = colormenu )
		menulist.append([colormenu,
						[['Random Color', self.getRandomColor],
						 ['Create Color', self.getUserColor],
						 ['', None]
						 ]])

		# create another menu for color
		distrmenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Distribution", menu = distrmenu )
		menulist.append([distrmenu,
						[['Set Distribution', self.setDistribution],
						 ['', None],
						 ['', None]
						 ]])		

		# create another menu for help
		helpmenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Help", menu = helpmenu )
		menulist.append([helpmenu,
						[["About", [['Application', self.displayAboutApp],
									['Me', self.displayAboutMe],
									['Stephanie', self.displayAboutSteph],
									['Bruce', self.displayAboutBruce]
									]],
						 ['Key Bindings', self.displayBindings]
						 ]])
		
		# build the menu elements and callbacks
		for menu, items in menulist:
			for item in items:
				
				# blank menu item
				if not item[0]:
					menu.add_separator()
				
				# sub cascade (TODO: could be recursive, only depth 1 now)
				elif isinstance(item[1], types.ListType):
					submenu = tk.Menu(self.menu)
					for subitem in item[1]:
						submenu.add_command(label=subitem[0], command=subitem[1])
					menu.add_cascade( label=item[0], menu=submenu )
				
				# menu command
				else:
					menu.add_command( label=item[0], command=item[1] )
		
	def buildStatusFrame(self):
		'''
		build the frame and the status labels
		'''
		if self.verbose: print("building the status frame")
		# make a status frame on the bottom
		bottomstatusframe = tk.Frame(self.root)
		bottomstatusframe.pack(side=tk.BOTTOM, padx=2, pady=2, fill=tk.X)
		
		# make a separator frame
		tk.Frame( self.root, height=2, bd=1, relief=tk.SUNKEN
				  ).pack( side=tk.BOTTOM, padx = 2, pady = 2, fill=tk.X)
		
		cols = 0;
		tk.Label(bottomstatusframe, text="Status", padx=20, 
				 ).grid(row=0, column=cols, rowspan=2)
		cols+=1
		
		# display the number of objects on the canvas
		tk.Label(bottomstatusframe, text="num objects on canvas:"
				 ).grid(row=0, column=cols)
		self.numObjStrVar = tk.StringVar( self.root )
		self.numObjStrVar.set("0")
		tk.Label(bottomstatusframe, textvariable=self.numObjStrVar
				 ).grid(row=1, column=cols)
		cols+=1

		# display the current color fields
		tk.Label(bottomstatusframe, text="\tsize field:"
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, text="\tcolor field:"
				 ).grid(row=1, column=cols)
		tk.Label(bottomstatusframe, text="\tshape field:"
				 ).grid(row=2, column=cols)
		cols+=1
		self.sizeField = tk.StringVar( self.root, value="" )
		tk.Label(bottomstatusframe, textvariable=self.sizeField
				 ).grid(row=0, column=cols)
		self.colorField = tk.StringVar( self.root, value="" )
		tk.Label(bottomstatusframe, textvariable=self.colorField
				 ).grid(row=1, column=cols)
		self.shapeField = tk.StringVar( self.root, value="" )
		tk.Label(bottomstatusframe, textvariable=self.shapeField
				 ).grid(row=2, column=cols)
		cols+=1		

		# display the current distributions
		tk.Label(bottomstatusframe, text="\tx distribution:"
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, text="\ty distribution:"
				 ).grid(row=1, column=cols)
		tk.Label(bottomstatusframe, text="\tz distribution:"
				 ).grid(row=2, column=cols)
		cols+=1
		self.xDistribution = tk.StringVar( self.root, value="UNIFORM" )
		tk.Label(bottomstatusframe, textvariable=self.xDistribution
				 ).grid(row=0, column=cols)
		self.yDistribution = tk.StringVar( self.root, value="UNIFORM" )
		tk.Label(bottomstatusframe, textvariable=self.yDistribution
				 ).grid(row=1, column=cols)
		self.zDistribution = tk.StringVar( self.root, value="UNIFORM" )
		tk.Label(bottomstatusframe, textvariable=self.zDistribution
				 ).grid(row=2, column=cols)
		cols+=1			   
		
		# display the location of the curser
		tk.Label(bottomstatusframe, text="\tx:"
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, text="\ty:"
				 ).grid(row=1, column=cols)
		cols+=1
		self.curserxLocation = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.curserxLocation
				 ).grid(row=0, column=cols)
		self.curseryLocation = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.curseryLocation
				 ).grid(row=1, column=cols)
		cols+=1		
		
		# display the location of the object the curser is over
		tk.Label(bottomstatusframe, text="\tobject x:"
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, text="\tobject y:"
				 ).grid(row=1, column=cols)
		cols+=1
		self.xLocation = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.xLocation
				 ).grid(row=0, column=cols)
		self.yLocation = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.yLocation
				 ).grid(row=1, column=cols)
		cols+=1
	
	def clearData(self, event=None):
		'''
		clear the data from the canvas
		'''
		if self.verbose: print("clearing data from canvas")
		for obj in self.objects:
			self.canvas.delete(obj)
		self.objects = []
		self.filename = None
		self.data = None
		self.activeData = None
		self.updateNumObjStrVar()
		self.xLocation.set("")
		self.yLocation.set("")
		self.colorField.set("")
		self.sizeField.set("")
		self.shapeField.set("")
		self.labelStrings = ["x", "y", "z"]
		self.updateAxes()
	
	def createRandomDataPoints( self, event=None ):
		'''
		draw a number of random points on the canvas
		'''
		if self.verbose: print("creating points on canvas")
		# parse the number of points from the entry control
		pointsStr = self.numPoints.get()
		points = 100
		if pointsStr.isdigit():
			self.numPointsDesc.set("\nNumber of Points")
			self.numPointsLabel.config(fg="black")
			points = int(pointsStr)
		elif pointsStr:
			self.numPointsDesc.set("\nNAN, default 100")
			self.numPointsLabel.config(fg="red")
			
		# position the points randomly according to current distribution
		[randFuncX, randArgsX] = self.randomFunctions[self.xDistribution.get().upper()]
		[randFuncY, randArgsY] = self.randomFunctions[self.yDistribution.get().upper()]
		[randFuncZ, randArgsZ] = self.randomFunctions[self.zDistribution.get().upper()]
		
		# make points on the canvas
		self.data = None
		self.activeData = None
		self.filename = [["x", "y", "z"], ["numeric", "numeric", "numeric"]]
		self.filename += [[randFuncX(*randArgsX), 
						   randFuncY(*randArgsY),
						   randFuncZ(*randArgsZ)]
						for _ in range(points)]
		self.update()
		
	def deletePoint(self, event):
		'''
		delete the top point under the event location
		'''
		if self.verbose: print('handle ctrl shift button 1: %d %d' % (event.x, event.y))
		self.baseClick = [event.x, event.y]
		for obj in reversed(self.objects): # reversed gets front object first
			[xlow, ylow, xhigh, yhigh] = self.canvas.bbox(obj)
			if ( (event.x > xlow) and (event.x < xhigh) and
				 (event.y > ylow) and (event.y < yhigh) ):
				self.canvas.delete(obj)
				self.objects.remove(obj)
				self.updateNumObjStrVar()
				self.objectsMove = []
				self.objectsResize = []
				return
		
	def displayAboutApp(self, event=None):
		'''
		display the application about dialog
		'''
		dialog.AboutAppDialog(self.root, title="About Application")

	def displayAboutMe(self, event=None):
		'''
		display the author about dialog
		'''
		dialog.AboutMeDialog(self.root, title="About Me")

	def displayAboutSteph(self, event=None):
		'''
		display the Stephanie about dialog
		'''
		dialog.AboutStephDialog(self.root, title="About Stephanie Taylor")

	def displayAboutBruce(self, event=None):
		'''
		display the Bruce about dialog
		'''
		dialog.AboutBruceDialog(self.root, title="About Bruce Maxwell")

	def displayBindings(self, event=None):
		'''
		display the Key Bindings about dialog
		'''
		dialog.BindingsDialog(self.root, title="Key Bindings")
	
	def drawObject(self, x, y, row=0):
		'''
		add the control selected shape to the canvas at x, y with size dx, dy
		'''
		dx = int(self.sizeOption.get())
		dy = int(self.sizeOption.get())
		if self.sizeModeStr.get() == "d":
			dx *= self.sizeData[row, 0] + 0.5
			dy *= self.sizeData[row, 0] + 0.5
			
		if self.shapeModeStr.get() == "s":
			[shapeFunc, coords] = self.getShapeFunction(self.shapeOption.get(), 
														x, y, dx, dy)
		else: # if self.shapeModeStr.get() == "d"
			shapeDataVal = min(self.shapeData[row, 0], 0.99)
			numShapes = len(self.shapeFunctions)
			shapeIndex = int(shapeDataVal*numShapes)
			shapes = self.shapeFunctions.keys()
			[shapeFunc, coords] = self.getShapeFunction(shapes[shapeIndex], 
														x, y, dx, dy)
			
		if shapeFunc:
			self.dataDepth = self.colorData[row, 0] # used for color depending on mode
			shape = shapeFunc(coords, fill=self.colorMode(), outline='')
			self.objects.append(shape)
			self.updateNumObjStrVar()
		else:
			if self.verbose: print("No shape function for %s" % 
								   self.shapeOption.get())
		
	def getColorByDepth(self):
		'''
		get the color according the given normalized z
		'''
		z = max(min(self.dataDepth, 1.0), 0.0) # in case depth is not normalized
		
		rb = int(z * 255.0)
		gb = 0
		bb = 255 - int(z * 255.0)
		return "#%02x%02x%02x" % (rb, gb, bb)
		
	def getCurrentColor(self):
		'''
		get the current color selected by the controls
		'''
		rgb = self.colors[self.colorOption.get()]
		if not rgb: rgb = ("#%02x%02x%02x" % 
							 (int(self.redBand.get()), 
							  int(self.greenBand.get()), 
							  int(self.blueBand.get())))
		if rgb in ["black", "#000000"]: rgb = "#000001" # FIXME black causes bad damage rectangle
		return rgb
		
	def getRandomColor(self, event=None):
		'''
		set the color channel pickers to three random integers between 0 and 250
		and return the random rgb band values as hex string
		'''
		if self.verbose: print("setting random color")
		rb = random.randint(0,255)
		gb = random.randint(0,255)
		bb = random.randint(0,255)
		self.redBand.set(str(rb))
		self.greenBand.set(str(gb))
		self.blueBand.set(str(bb))
		return "#%02x%02x%02x" % (rb, gb, bb)
	
	def getShapeFunction(self, shape, x, y, dx, dy):
		'''
		returns the function and arguments as a tuple for the arguments
		'''
		shape = shape.upper()
		if shape not in self.shapeFunctions:
			return [None, None]
			
		if shape == "STAR":
			self.shapeFunctions[shape][1] = [x-dx, y+dy, 
											 x, y+dy/2.0,
											 x+dx, y+dy, 
											 x+dx/2.0, y, 
											 x+dx, y-dy/2.0, 
											 x+dx/3.0, y-dy/2.0,
											 x, y-dy, 
											 x-dx/3.0, y-dy/2.0,
											 x-dx, y-dy/2.0, 
											 x-dx/2.0, y]
		elif shape == "UP TRIANGLE":
			self.shapeFunctions[shape][1] = [x-dx, y+dy, 
											 x+dx, y+dy, 
											 x, y-dy]
		elif shape == "DOWN TRIANGLE":
			self.shapeFunctions[shape][1] = [x-dx, y-dy, 
											 x+dx, y-dy, 
											 x, y+dy]
		elif shape == "X":
			self.shapeFunctions[shape][1] = [x-dx, y+dy, 
											 x, y+dy/2.0,
											 x+dx, y+dy, 
											 x+dx/2.0, y, 
											 x+dx, y-dy, 
											 x, y-dy/2.0, 
											 x-dx, y-dy, 
											 x-dx/2.0, y]
		else:
			self.shapeFunctions[shape][1] = [x-dx, y-dy, 
											 x+dx, y+dy]
		return self.shapeFunctions[shape]

	def getUserColor(self, event=None):
		'''
		define a new color for the color selector control
		'''
		if self.verbose: print("creating a new color")
		#d = dialog.ColorMakerDialog(self.root, title="Create New Color")
		result = askcolor()
		if result[0]:
			(rb, gb, bb) = result[0]
			self.redBand.set(str(rb))
			self.greenBand.set(str(gb))
			self.blueBand.set(str(bb))
			return result[1]
		return None
			
	def handleQuit(self, event=None):
		'''
		quit the display application
		'''
		if self.verbose: print('Terminating')
		self.root.destroy()

	def handleButton1(self, event):
		'''
		prepare for moving objects on canvas, the first object under the event
		or all the objects if the event is not over any objects
		'''
		if self.verbose: print('handle button 1: %d %d' % (event.x, event.y))
		self.baseClick = [event.x, event.y]

	def handleButton2(self, event):
		'''
		prepare to rotate the view by storing click and original view
		'''
		if self.verbose: print('handle button 2: %d %d' % (event.x, event.y))
		self.baseClick = [event.x, event.y]
		self.baseView = self.view.clone()

	def handleButton3(self, event):
		'''
		prepare for scaling by storing a base click point and the value of the	
		extent in the view space that does not change while the user moves
		'''
		if self.verbose: print('handle button 3: %d %d' % (event.x, event.y))
		self.baseClick = [event.x, event.y]
		self.baseExtent = self.view.extent.copy()

	def handleButton1Motion(self, event):
		'''
		pan the view
		'''
		# calculate the differential motion
		[dx, dy] = [ event.x - self.baseClick[0], event.y - self.baseClick[1] ]
		if self.verbose: print('handle button 1 motion %d %d' % (dx, dy))
		self.baseClick = [event.x, event.y] # update click location
		
		# Divide the differential motion by the screen size
		dx /= self.view.screen[0, 0]
		dy /= self.view.screen[0, 1]
		
		# Multiply the motion by the view extents.
		dx *= self.view.extent[0, 0]
		dy *= self.view.extent[0, 1]
		
		# The VRP should be updated
		panSpeed = 1.0
		self.view.vrp += panSpeed*dx*self.view.u + panSpeed*dy*self.view.vup
		self.update()

	def handleButton2Motion(self, event):
		'''
		rotate the view about the center of the view volume
		'''
		# calculate the differential motion
		[dx, dy] = [ event.x - self.baseClick[0], event.y - self.baseClick[1] ]
		if self.verbose: print('handle button 2 motion %d %d' % (dx, dy))
		
		# update the view
		rotSpeed = 0.5
		self.view = self.baseView.clone()
		self.view.rotateVRC(-rotSpeed*dx, rotSpeed*dy)
		self.update()

	def handleButton3Motion(self, event):
		'''
		zoom the view
		'''
		# calculate the difference
		dy = event.y - self.baseClick[1] # only zoom with vertical motion
		if self.verbose: print('handle button 3 motion %d' % dy)

		# update the extent
		zoomSpeed = 0.01
		self.view.extent = self.baseExtent*min(max(1.0+zoomSpeed*dy, 0.1), 3.0)
		self.update()
		
	def main(self):
		'''
		start the application
		'''
		if self.verbose: print('Entering main loop')
		self.root.mainloop()
		
	def openData(self, event=None):
		'''
		open a dialog for picking data file and read into field
		'''
		filename = tkf.askopenfilename(parent=self.root, title='Choose a data file', 
											initialdir='.' )
		if filename:
			nodirfilename = filename.split("/")[-1]
			try:
				self.filename2data[nodirfilename] = Data(filename, self.verbose)
				print("successfully read data")
			except:
				print("failed to read data")
				return
			self.openFilenames.insert(tk.END, nodirfilename)
			self.openFilenames.select_clear(first=0, last=tk.END)
			self.openFilenames.select_set(tk.END)
			
	def plotData(self, event=None):
		'''
		plot the data associated with the currently selected filename
		'''
		try:
			self.filename = self.openFilenames.get(self.openFilenames.curselection())
			self.data = None
			self.activeData = None
			self.update()
		except:
			print("no selected filename")

	def preDefineColors(self):
		'''
		define the initial colors for the color selector control
		'''
		if self.verbose: print("defining initial colors")
		self.colors = OrderedDict()
		self.colors["Select Color"] = ""
		self.colors["black"] = "black"
		self.colors["blue"] = "blue"
		self.colors["red"] = "red"
		self.colors["green"] = "green"
		self.colors["purple"] = "purple"
		
	def preDefineDistributions(self):
		'''
		define the distributions for creating points
		'''
		if self.verbose: print("defining initial distributions")
		self.randomFunctions = OrderedDict()
		self.randomFunctions["UNIFORM"] = [random.random,[]]
		self.randomFunctions["GAUSSIAN"] = [random.gauss,[0.5, 0.1]] # mean, sigma
		self.randomFunctions["TRIANGULAR"] = [random.triangular,[0.0, 0.5, 0.1]] # low, high, mode
		self.randomFunctions["BETA"] = [random.betavariate,[0.5, 0.1]] # alpha, beta
		self.randomFunctions["EXPONENTIAL"] = [random.expovariate,[2]] # lambd
		self.randomFunctions["GAMMA"] = [random.gammavariate,[0.5, 0.1]] # alpha, beta
		self.randomFunctions["WEIBULL"] = [random.weibullvariate,[0.5, 0.5]] #alpha, beta
		
	def preDefineShapes(self):
		'''
		define the shapes for representing points
		'''
		self.shapeFunctions = {"RECTANGLE":[self.canvas.create_rectangle, []],
							  "OVAL":[self.canvas.create_oval, []],
							  "DOWN TRIANGLE":[self.canvas.create_polygon, []],
							  "UP TRIANGLE":[self.canvas.create_polygon, []],
							  "X":[self.canvas.create_polygon, []],
							  "STAR":[self.canvas.create_polygon, []]}
		
	def setActiveData(self, event=None):
		'''
		set the active data, selected by the user
		'''
		if not self.filename:
			return
		try:
			self.data = self.filename2data[self.filename] # opened data
		except:
			self.data = Data(self.filename, self.verbose) # creating points
			
		headers = dialog.PickAxesDialog(self.root, self.data, title="Pick Data Axes").result
		if not headers:
			self.filename = None
			self.data = None
			self.activeData = None
			return
			
		self.activeData = analysis.normalize_columns_separately(self.data, headers)
		self.shapeData = self.activeData[:, -1]
		self.shapeField.set(headers[-1])
		self.colorData = self.activeData[:, -2]
		self.colorField.set(headers[-2])
		self.sizeData = self.activeData[:, -3]
		self.sizeField.set(headers[-3])
		[rows, cols] = self.activeData.shape
		self.labelStrings[0] = headers[0]
		self.labelStrings[1] = headers[1]
		if cols == 2: # pad missing z data
			self.activeData = np.column_stack((self.activeData[:, :2], [0]*rows, [1]*rows))
		else: # pad the homogeneous coordinate
			self.activeData = np.column_stack((self.activeData[:, :3], [1]*rows))
			self.labelStrings[2] = headers[2]
			
	def setBindings(self):
		'''
		set the key bindings for the application
		'''
		if self.verbose: print("setting the key bindings")
		# bind mouse motions to the canvas
		self.canvas.bind( '<Button-1>', self.handleButton1 )
		self.canvas.bind( '<Control-Button-1>', self.handleButton2 ) # same as B2
		self.canvas.bind( '<Button-2>', self.handleButton2 )
		self.canvas.bind( '<Button-3>', self.handleButton3 )
		self.canvas.bind( '<B1-Motion>', self.handleButton1Motion )
		self.canvas.bind( '<Control-B1-Motion>', self.handleButton2Motion ) # same as B2-Motion
		self.canvas.bind( '<B2-Motion>', self.handleButton2Motion )
		self.canvas.bind( '<B3-Motion>', self.handleButton3Motion )
		self.canvas.bind( '<Control-Shift-Button-1>', self.deletePoint )
		self.canvas.bind( '<Motion>', self.showObjectPosition )

		# bind command sequences to the root window
		self.root.bind( '<Control-n>', self.clearData)
		self.root.bind( '<Control-o>', self.openData)
		self.root.bind( '<Control-q>', self.handleQuit )
		
		# resizing canvas
		self.root.bind( '<Configure>', self.updateScreen )
	
	def setColorMode(self, event=None):
		'''
		callback for radio button
		'''
		cmstr = self.colorModeStr.get()
		if cmstr == "s":
			self.colorMode = self.getCurrentColor
		else:# cmstr == "d":
			self.colorMode = self.getColorByDepth
		self.update()
			
	def setDistribution(self, event=None):
		'''
		select the distribution using the dialog and update status
		'''
		if self.verbose: print("setting a new distribution")
		[xDistribution, yDistribution, zDistribution] = \
			dialog.DistributionDialog(self.root, 
							   self.xDistribution.get(), 
							   self.yDistribution.get(), 
							   self.zDistribution.get(), 
							   list(self.randomFunctions.keys()),
							   title="Set Distribution").result
		self.xDistribution.set(xDistribution)
		self.yDistribution.set(yDistribution)
		self.zDistribution.set(zDistribution)

	def showObjectPosition(self, event):
		'''
		update the status if the event is over an object on the canvas
		'''
		self.curserxLocation.set(event.x)
		self.curseryLocation.set(event.y)
		self.xLocation.set("-"*4)
		self.yLocation.set("-"*4)
		for obj in self.objects:
			if not self.canvas.bbox(obj): break
			[xlow, ylow, xhigh, yhigh] = self.canvas.bbox(obj)
			if ( (event.x > xlow) and (event.x < xhigh) and
				 (event.y > ylow) and (event.y < yhigh) ):
				self.xLocation.set("%4d" % int((xhigh+xlow)/2.0))
				self.yLocation.set("%4d" % int((yhigh+ylow)/2.0))
				return

	def update(self, event=None):
		'''
		update the objects on the canvas with the current vtm 
		'''
		self.buildData()
		self.updateAxes()

	def updateAxes(self):
		'''
		updates the axes line objects with the current vtm
		'''
		if self.verbose: print("updating axes")
		VTM = self.view.build()
		axesPts = (VTM * self.axes.T).T
		labelPts = (VTM * self.axesLabels.T).T
		for i, line in enumerate(self.lines):
			self.canvas.coords(line, 
								axesPts[2*i, 0], axesPts[2*i, 1], 
								axesPts[2*i+1, 0], axesPts[2*i+1, 1])
			self.canvas.coords(self.labels[i], labelPts[i, 0], labelPts[i, 1])
			self.canvas.itemconfigure(self.labels[i], text=self.labelStrings[i])
		
	def updateNumObjStrVar(self):
		'''
		update the status bar to reflect the current number of objects
		'''
		#if self.verbose: print("updating the number of objects status")
		self.numObjStrVar.set("%d" % len(self.objects))

	def updateScreen(self, event=None):
		'''
		updates the view to the current screen dimensions
		'''
		if (not (self.width and self.height) or
			(self.width == self.canvas.winfo_width() and 
			self.height == self.canvas.winfo_height())):
			return
		if self.verbose: print("screen resizing")
		self.width = self.canvas.winfo_width() 
		self.height = self.canvas.winfo_height()
		self.view.offset[0, 0] = self.width*0.1
		self.view.offset[0, 1] = self.height*0.1
		self.view.screen[0, 0] = self.width*0.8
		self.view.screen[0, 1] = self.height*0.8
		self.update()
		
	def viewPreset(self, event=None):
		'''
		set the view to the specified preset
		'''
		presetStr = self.presetView.get().upper()
		self.view.reset() # return to xy plane view
		self.view.offset[0, 0] = self.width*0.1
		self.view.offset[0, 1] = self.height*0.1
		self.view.screen[0, 0] = self.width*0.8
		self.view.screen[0, 1] = self.height*0.8
		if presetStr == "XZ":
			self.view.rotateVRC(0, 90)
		elif presetStr == "YZ":
			self.view.rotateVRC(90, 90)
		self.update()

if __name__ == "__main__":
	
	#define the command line interface usage message
	usage = "python %prog [-h help] [options (with '-'|'--' prefix)]"

	# used to parse command line arguments, -h will print options by default
	parser = OptionParser(usage)
	
	# indicate that the program should print actions to console
	parser.add_option("-v","--verbose", 
				help="to enable command line printouts of state",
				action="store_true")
	
	# indicate that the program should print actions to console
	parser.add_option("-f","--filename", 
				help="to specify a csv file of data to read into a Data field",
				default="")
	
	[options, args] = parser.parse_args()
	
	# run the application
	DisplayApp(1200, 675, options.filename, options.verbose).main()