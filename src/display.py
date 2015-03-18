'''
Ian Tibbetts
Colby College CS251 Spring '15
Professors Stephanie Taylor and Bruce Maxwell
'''

# standard with python
from collections import OrderedDict
from optparse import OptionParser
import random
import types
import sys
import os
import numpy as np
from scipy import stats
from matplotlib import pyplot as plt

# defined by me for this project
import analysis
from data import Data
import dialog
from view import View

try: # astronomy research stuff, optional
	from astropy.io import fits
except ImportError:
	try:
		import pyfits as fits
	except:
		fits = None

# use tkinter for GUI elements
#try:
#	import tkinter as tk # python 3
#	tkf = tk.filedialog
#	from tk.colorchooser import askcolor
#except ImportError:
import Tkinter as tk # python 2
import tkFileDialog as tkf
from tkColorChooser import askcolor
import tkMessageBox as tkm
	
class DisplayApp:
	'''
	class to build and manage the display
	'''
	
	def __init__(self, width, height, filename=None, verbose=True):
		'''
		Constructor for the display application
		'''
		# make initial fields
		self.verbose = verbose
		self.filename = filename
		self.data = None
		self.headers = None
		self.filteredData = None
		self.normalizedData = None
		self.width = None
		self.height = None
		self.filename2data = {}
		self.preDefineColors()
		self.preDefineDistributions()
		self.objects = {} # shapes drawn on canvas and their row in the data

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
		self.canvasBG = self.canvas.create_rectangle(0, 0, 10000, 10000,
													fill="white")
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
		
		if filename:
			try: # handle error caused by exiting application with dialog open
				self.setData()
				self.update()
			except tk.TclError:
				exit()

	def buildAxes(self, axes=[[0,0,0],[1,0,0],
							  [0,0,0],[0,1,0],
							  [0,0,0],[0,0,1]],
				  axeslabels=[[1.05,-0.05,-0.05],
							  [-0.05,1.05,-0.05],
							  [-0.05,-0.05,1.05]]):
		'''
		builds the view transformation matrix [VTM], 
		multiplies the axis endpoints by the VTM, 
		then creates three new line objects, one for each axis
		Note: only called once by __init__, then updateAxes used
		'''
		if self.verbose: print("building the axes")
		for axis in axes:
			if len(axis) < 4: 
				axis.append(1) # homogeneous coordinate
		for axis in axeslabels:
			if len(axis) < 4:axis.append(1) # homogeneous coordinate
		self.view = View(offset=[self.width*0.15, self.height*0.15],
							screen=[self.width*0.7, self.height*0.7])
		self.baseView = self.view.clone()
		VTM = self.view.build()
		self.axes = np.asmatrix(axes)
		self.axesLabels = np.asmatrix(axeslabels)
		axesPts = (VTM * self.axes.T).T
		labelPts = (VTM * self.axesLabels.T).T
		self.xLabel.set("X")
		self.yLabel.set("Y")
		self.zLabel.set("Z")
		labelVars = [self.xLabel, self.yLabel, self.zLabel]
		self.lines = []
		self.labels = []
		for i in range(3):
			self.lines.append(self.canvas.create_line(axesPts[2*i, 0], axesPts[2*i, 1], 
												axesPts[2*i+1, 0], axesPts[2*i+1, 1]))
			self.labels.append(self.canvas.create_text(labelPts[i, 0], labelPts[i, 1], 
													font=("Purina", 12), 
													text=labelVars[i].get()))

	def buildControlsFrame(self):
		'''
		build the frame and controls for application
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
				  ).grid( row=row, columnspan=3 )
		row+=1

		
		# make an open button in the frame
		tk.Button( self.rightcntlframe, text="Open", 
				   command=self.openData, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1
		
		self.openFilenames = tk.Listbox(self.rightcntlframe, selectmode=tk.SINGLE, 
										exportselection=0, height=3)
		self.openFilenames.bind("<Double-Button-1>", self.plotData)
		self.openFilenames.grid( row=row, columnspan=3 )
		row+=1

		# make a plot button in the frame
		tk.Button( self.rightcntlframe, text="Plot Selected", 
				   command=self.plotData, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1

		# make a plot button in the frame
		tk.Button( self.rightcntlframe, text="Change Axes", 
				   command=self.changeDataAxes, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1
		
		# make a filter button in the frame
		tk.Button( self.rightcntlframe, text="Filter", 
				   command=self.filterData, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1

		# make a save button in the frame
		tk.Button( self.rightcntlframe, text="Save Data", 
				   command=self.saveData, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1

		# make a save button in the frame
		tk.Button( self.rightcntlframe, text="Save Canvas", 
				   command=self.saveCanvas, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1

		# make a clear button in the frame
		tk.Button( self.rightcntlframe, text="Clear", 
				   command=self.clearData, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1

		# make a clear button in the frame
		tk.Button( self.rightcntlframe, text="Reset", 
				   command=self.resetView, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1
		
		self.presetView = tk.StringVar( self.root )
		self.presetView.set("xy")
		tk.OptionMenu( self.rightcntlframe, self.presetView, 
					   "xy", "xz", "yz", command=self.resetViewOrientation
					   ).grid( row=row, columnspan=3 )
		row+=1

		# make a plot button in the frame
		tk.Button( self.rightcntlframe, text="Multiple Linear Regression", 
				   command=self.multiLinearRegression,
				   ).grid( row=row, columnspan=3 )
		row+=1
		
		# linear regression control
		self.fitPoints = None
		self.linearRegressionEnabled = tk.IntVar()
		tk.Checkbutton( self.rightcntlframe, text="2D Linear Regression",
					variable=self.linearRegressionEnabled,
					command=self.toggleLinearRegression,
					   ).grid( row=row, columnspan=3 )
		row+=1
		
		# connecting lines control
		self.dataLines = []
		self.linePlot = tk.IntVar()
		tk.Checkbutton( self.rightcntlframe, text="Line Plot",
					variable=self.linePlot, command=self.update
					   ).grid( row=row, columnspan=3 )
		row+=1
		
		# size selector
		tk.Label( self.rightcntlframe, text="\nSize"
					   ).grid( row=row, columnspan=3 )
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
			b.grid( row=row, columnspan=3 )
			row+=1
			
		# User selected size
		self.sizeOption = tk.StringVar( self.root )
		self.sizeOption.set("6")
		tk.OptionMenu( self.rightcntlframe, self.sizeOption, command=self.update,
					   *range(1,31)).grid( row=row, columnspan=3 )
		row+=1
		
		# shape selector
		tk.Label( self.rightcntlframe, text="\nShape"
					   ).grid( row=row, columnspan=3 )
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
			b.grid( row=row, columnspan=3 )
			row+=1
		
		# User selected shape
		self.shapeOption = tk.StringVar( self.root )
		self.shapeOption.set(self.shapeFunctions.keys()[0].capitalize())
		tk.OptionMenu( self.rightcntlframe, self.shapeOption, 
					   *[shape.capitalize() for shape in self.shapeFunctions],
					   command=self.update
					   ).grid( row=row, columnspan=3 )
		row+=1

		# color selector
		tk.Label( self.rightcntlframe, text="\nColor"
					   ).grid( row=row, columnspan=3 )
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
			b.grid( row=row, columnspan=3 )
			row+=1

		# make a button for selecting predefined colors
		self.colorRow = row
		self.colorOption = tk.StringVar( self.root )
		self.colorOption.set("Select Color")
		self.colorMenu = tk.OptionMenu( self.rightcntlframe, self.colorOption, 
					   *self.colors.keys(), command=self.update
					   ).grid( row=row, columnspan=3 )
		row+=1
		
		# use a label to set the size of the right panel
		tk.Label( self.rightcntlframe, text="OR"
				  ).grid( row=row, columnspan=3 )
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
		self.numPointsLabel.grid( row=row, columnspan=3 )
		row+=1
		self.numPoints = tk.Entry(self.rightcntlframe, width=10)
		self.numPoints.grid( row=row, columnspan=3 )
		row+=1
		
		tk.Button( self.rightcntlframe, text="Create Points", 
				   command=self.createRandomDataPoints, width=10 
				   ).grid( row=row, columnspan=3 )
		row+=1
		
		
	def buildData(self): 
		'''
		build the data on the screen based on the data and filename fields
		Note: this method is the only one that transforms and draws data
		'''
		# if the data is not set, set according to filename
		if not self.data:
			return
		
		# clean the data on the canvas
		self.clearObjects()
		
		# prepare to transform the active data to the current view
		VTM = self.view.build()
		viewData = self.normalizedData.copy()
		
		# transform into view
		viewData = (VTM * viewData.T).T

		# order so that closer objects draw last
		zIndicesSorted = np.argsort(viewData[:, 2].T.tolist()[0])
		
		# transform sorted data to view and draw on canvas
		for row in zIndicesSorted:
			x, y = [viewData[row, col] for col in range(2)]
			self.drawObject(x, y, row=row)
			
			# TODO: line plotting, currently ordered according to csv
			nextRow = row + 1
			if self.linePlot.get() and nextRow < len(zIndicesSorted):
				xh, yh = [viewData[nextRow, col] for col in range(2)]
				line = self.canvas.create_line(x, y, xh, yh)
				self.dataLines.append(line)

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
						 ['Save, Ctrl-S', self.saveData],  
						 ['Quit, Ctrl-Q OR Esc', self.handleQuit]
						 ]])

		# create another menu for color
		datamenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Data", menu = datamenu )
		menulist.append([datamenu,
						[['Plot Selected, Ctrl-P', self.plotData],
						 ['Filter, Ctrl-F', self.filterData],
						 ['Save Filtered Data', self.saveFilteredData],
						 ['Change Axes', self.changeDataAxes],
						 ['Clear, Ctrl-N', self.clearData]
						 ]])

		# create another menu for color
		canvasmenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "View", menu = canvasmenu )
		menulist.append([canvasmenu,
						[['Zoom In', self.zoomIn],
						 ['Zoom Out', self.zoomOut],
						 ['Reset Orientation', self.resetViewOrientation],
						 ['Reset Zoom', self.resetViewZoom],
						 ['Reset All', self.resetView]
						 ]])
		
		# create another menu for color
		colormenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Color", menu = colormenu )
		menulist.append([colormenu,
						[['Random Color', self.getRandomColor],
						 ['Pick Color', self.getUserColor],
						 ['Canvas Color', self.setCanvasColor]
						 ]])

		# create another menu for color
		distrmenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Create", menu = distrmenu )
		menulist.append([distrmenu,
						[['Set Distribution', self.setDistribution],
						 ['Create Points', self.createRandomDataPoints],
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
						 ['Key Bindings', self.displayBindings],
						 ['', None]
						 ]])	

		# create another menu for research		# for astronomy research
		self.imageFilePath = "/home/imtibbet/Pictures/astro/results/VELA28/results"# "."
		astromenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Astro", menu = astromenu )
		menulist.append([astromenu,
						[['Set Path to Images', self.setImageFilePath],
						 ['', None],
						 ['', None]
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
		tk.Label(bottomstatusframe, text="Status", 
				 ).grid(row=0, column=cols, rowspan=3)
		cols+=1
		
		# display the number of objects on the canvas
		tk.Label(bottomstatusframe, text="num objects"
				 ).grid(row=0, column=cols, padx=50)
		tk.Label(bottomstatusframe, text="on canvas:"
				 ).grid(row=1, column=cols)
		self.numObjStrVar = tk.StringVar( self.root )
		self.numObjStrVar.set("0")
		tk.Label(bottomstatusframe, textvariable=self.numObjStrVar
				 ).grid(row=2, column=cols)
		cols+=1

		# display the current color fields
		tk.Label(bottomstatusframe, text="size field:"
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, text="color field:"
				 ).grid(row=1, column=cols)
		tk.Label(bottomstatusframe, text="shape field:"
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
		self.curserxLocation = tk.StringVar( self.root )
		self.curseryLocation = tk.StringVar( self.root )
		'''
		tk.Label(bottomstatusframe, text="\tx:"
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, text="\ty:"
				 ).grid(row=1, column=cols)
		cols+=1
		tk.Label(bottomstatusframe, textvariable=self.curserxLocation
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, textvariable=self.curseryLocation
				 ).grid(row=1, column=cols)
		cols+=1		
		'''
		
		# display the location of the object the curser is over
		tk.Label(bottomstatusframe, text="\tdata "
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, text="\tdata "
				 ).grid(row=1, column=cols)
		tk.Label(bottomstatusframe, text="\tdata "
				 ).grid(row=2, column=cols)
		cols+=1
		self.xLabel = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.xLabel
				 ).grid(row=0, column=cols)
		self.yLabel = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.yLabel
				 ).grid(row=1, column=cols)
		self.zLabel = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.zLabel
				 ).grid(row=2, column=cols)
		cols+=1
		tk.Label(bottomstatusframe, text=":"
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, text=":"
				 ).grid(row=1, column=cols)
		tk.Label(bottomstatusframe, text=":"
				 ).grid(row=2, column=cols)
		cols+=1
		self.xLocation = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.xLocation
				 ).grid(row=0, column=cols)
		self.yLocation = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.yLocation
				 ).grid(row=1, column=cols)
		self.zLocation = tk.StringVar( self.root )
		tk.Label(bottomstatusframe, textvariable=self.zLocation
				 ).grid(row=2, column=cols)
		cols+=1
	
	def captureState(self):
		'''
		return the current state of the application's data as a dictionary
		'''
		return {"normalized":self.normalizedData,
				"filtered":self.filteredData,
				"filename":self.filename,
				"headers":self.headers,
				"data":self.data}
	
	def changeDataAxes(self, event=None):
		'''
		prompts the user to change the displayed data axes if any
		'''
		if self.data:
			state = self.captureState()
			self.pickDataAxes()
			if not self.data:
				self.restoreState(state)
			else:
				self.update()
		else:
			tkm.showerror("No Data Plotted", "No data to change axes")
		
	def clearData(self, event=None):
		'''
		clear the data from the canvas
		'''
		if self.verbose: print("clearing data from canvas")
		self.clearObjects()
		self.filename = None
		self.data = None
		self.updateNumObjStrVar()
		self.xLocation.set("----")
		self.yLocation.set("----")
		self.zLocation.set("----")
		self.xLabel.set("x")
		self.yLabel.set("y")
		self.zLabel.set("z")
		self.colorField.set("")
		self.sizeField.set("")
		self.shapeField.set("")
		self.updateAxes()
	
	def clearObjects(self):
		'''
		clear the objects from the canvas
		'''
		for obj in self.objects:
			self.canvas.delete(obj)
		self.objects = {}
		for line in self.dataLines:
			self.canvas.delete(line)
		self.dataLines = []
		
	def createRandomDataPoints( self, event=None ):
		'''
		create a number of random points on the canvas according to the current
		distributions, storing as data and rendering with view.
		Data can be filtered and saved like any other data
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
		self.filename = [["x", "y", "z"], ["numeric", "numeric", "numeric"]]
		self.filename += [[randFuncX(*randArgsX), 
						   randFuncY(*randArgsY),
						   randFuncZ(*randArgsZ)]
						for _ in range(points)]
		self.setData()
		self.update()
		
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
		add the control selected shape to the canvas at x, y with cur color
		row is used to get data determined shape, color, and size if enabled
		'''
		dx = int(self.sizeOption.get()) # self.view.extent[0,0]
		dy = int(self.sizeOption.get()) # self.view.extent[0,1]
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
			self.dataDepth = self.colorData[row, 0] # used for coloring
			shape = shapeFunc(coords, fill=self.colorMode(), outline='')
			self.objects[shape] = row
			self.updateNumObjStrVar()
		else:
			if self.verbose: print("No shape function for %s" % self.shapeOption.get())
		
	def excludeData(self, exclude):
		'''
		this limits the current data by row(int) or rows(list) given
		while tracking deletions in the filtered data field
		leaves the original data instance unchanged by cloning first
		'''
		rows = self.data.matrix_data.shape[0]
		mask = np.ones(rows, dtype=bool)
		try: # exclude a single row
			mask[int(exclude)] = False
			if self.verbose: print("deleted element")
		except: # exclude a list of rows
			for [col, [newMin, newMax]] in enumerate(exclude):
				for row in range(rows):
					if (self.data.matrix_data[row, col] < newMin or
						self.data.matrix_data[row, col] > newMax):
						mask[row] = False
			if self.verbose: print("applied filter")
			
		unmask = np.negative(mask)
		if not self.filteredData:
			self.filteredData = self.data.clone()
			self.filteredData.raw_data = self.data.raw_data[unmask]
		else:
			self.filteredData.raw_data = np.vstack((self.filteredData.raw_data, 
												self.data.raw_data[unmask]))
		self.data = self.data.clone() # prevent base data from being altered
		self.data.matrix_data = self.data.matrix_data[mask]
		self.data.raw_data = self.data.raw_data[mask]
		
	def filterData(self, event=None):
		'''
		filter the data by getting user bounds
		'''
		if not self.data:
			tkm.showerror("No Data", "No data to filter")
			return
		newRanges = dialog.FilterDataDialog(self.root, self.data, 
										title="Filter Data").result
		if self.verbose: print("filtering: %s" % newRanges)
		if not newRanges:
			tkm.showerror("Filter Failed", "Data will not be filtered")
		else:
			self.excludeData(newRanges)
			self.processData()
		self.update()
	
	def getColorByDepth(self):
		'''
		return the color according the given normalized z as hex string
		'''
		z = max(min(self.dataDepth, 1.0), 0.0) # in case depth is not normalized
		
		rb = int(z * 255.0)
		gb = 0
		bb = 255 - int(z * 255.0)
		return "#%02x%02x%02x" % (rb, gb, bb)
		
	def getCurrentColor(self):
		'''
		get the current color selected by the controls as hex string
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
		set the color channel pickers to three random integers between 0 and 255
		returns the random rgb band values as hex string
		'''
		if self.verbose: print("setting random color")
		rb = random.randint(0,255)
		gb = random.randint(0,255)
		bb = random.randint(0,255)
		self.redBand.set(str(rb))
		self.greenBand.set(str(gb))
		self.blueBand.set(str(bb))
		rgb = "#%02x%02x%02x" % (rb, gb, bb)
		if rgb in ["black", "#000000"]: rgb = "#000001" # FIXME black causes bad damage rectangle
		return rgb
	
	def getShapeFunction(self, shape, x, y, dx, dy):
		'''
		returns the shape function and arguments as a list [func, args]
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
		prompt the user for a color and use selection as the current color
		returns user selected color as hex string of band values
		'''
		if self.verbose: print("creating a new color")
		#d = dialog.ColorMakerDialog(self.root, title="Create New Color")
		result = askcolor()
		if result[0]:
			(rb, gb, bb) = result[0]
			self.redBand.set(str(rb))
			self.greenBand.set(str(gb))
			self.blueBand.set(str(bb))
			rgb = result[1]
			if rgb in ["black", "#000000"]: rgb = "#000001" # FIXME black causes bad damage rectangle
			return rgb
		return None
			
	def handleQuit(self, event=None):
		'''
		quit the display application
		'''
		if self.verbose: print('Terminating')
		self.root.destroy()

	def handleButton1(self, event):
		'''
		prepare to pan the view by storing the base click
		'''
		if self.verbose: print('handle button 1: %d %d' % (event.x, event.y))
		self.baseClick = [event.x, event.y]

	def handleButton2(self, event):
		'''
		prepare to rotate the view by storing original click and view
		'''
		if self.verbose: print('handle button 2: %d %d' % (event.x, event.y))
		self.baseClick = [event.x, event.y]
		self.baseView = self.view.clone()

	def handleButton3(self, event):
		'''
		prepare to zoom the view by storing original click and extent
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
		# rotate the view
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

		# update the extent
		zoomSpeed = 0.01
		self.view.extent = self.baseExtent*min(max(1.0+zoomSpeed*dy, 0.1), 3.0)
		self.update()
		
	def handleDelete(self, event):
		'''
		delete the top point under the event location
		'''
		if self.verbose: print('handle ctrl shift button 1: %d %d' % (event.x, event.y))
		self.baseClick = [event.x, event.y]
		for obj in self.objects:
			[xlow, ylow, xhigh, yhigh] = self.canvas.bbox(obj)
			if ( (event.x > xlow) and (event.x < xhigh) and
				 (event.y > ylow) and (event.y < yhigh) ):
				row = self.objects[obj]
				self.excludeData(row)
				self.processData()
				self.update()
				return

	def handleDoubleButton1(self, event):
		'''
		show all the raw data for the point double clicked
		'''
		for obj in self.objects:
			if not self.canvas.bbox(obj): continue
			[xlow, ylow, xhigh, yhigh] = self.canvas.bbox(obj)
			if ( (event.x > xlow) and (event.x < xhigh) and
				 (event.y > ylow) and (event.y < yhigh) ):
				row = self.objects[obj]
				msg = []
				for i in range(self.data.raw_data.shape[1]):
					msg.append(" | ".join([self.data.raw_headers[i],
										self.data.raw_types[i],
										self.data.raw_data[row, i]]))
				msg = "\n".join(msg)
				tkm.showinfo("Data Info", msg, parent=self.root)
				return

	def handleShowData(self, event):
		'''
		update the status if the event is over an object on the canvas
		'''
		self.curserxLocation.set(event.x)
		self.curseryLocation.set(event.y)
		self.xLocation.set("-"*4)
		self.yLocation.set("-"*4)
		self.zLocation.set("-"*4)
		for obj in self.objects:
			if not self.canvas.bbox(obj): continue
			[xlow, ylow, xhigh, yhigh] = self.canvas.bbox(obj)
			if ( (event.x > xlow) and (event.x < xhigh) and
				 (event.y > ylow) and (event.y < yhigh) ):
				row = self.objects[obj]
				xcol = self.data.header2matrix[self.headers[0]]
				ycol = self.data.header2matrix[self.headers[1]]
				if len(self.headers) > 5:
					zcol = self.data.header2matrix[self.headers[2]]
					self.zLocation.set("%5.2f" % self.data.matrix_data[row, zcol])
				self.xLocation.set("%5.2f" % self.data.matrix_data[row, xcol])
				self.yLocation.set("%5.2f" % self.data.matrix_data[row, ycol])
				return
			
	def handleShowImage(self, event):
		'''
		show the image of the data point, if any
		'''
		# find the object under the mouse click, if any
		row=None
		for obj in self.objects:
			if not self.canvas.bbox(obj): continue
			[xlow, ylow, xhigh, yhigh] = self.canvas.bbox(obj)
			if ( (event.x > xlow) and (event.x < xhigh) and
				 (event.y > ylow) and (event.y < yhigh) ):
				row = self.objects[obj]
				break
		if row == None:
			return
		
		try:
			col = self.data.get_raw_headers().index("FILENAME")
			filename = "/".join([self.imageFilePath.rstrip("/"), 
								self.data.raw_data[row, col]])
			hdu = fits.open(filename)
			#fileList = filename.split("_")
			#filename = "_".join(fileList[:-2]) + "." + fileList[-1].split(".")[-1]
			#filename = tkf.askopenfilename(initialdir=self.imageFilePath.get())
			#data = np.log10(fits.open(filename)[1].data)
		except:
			if self.verbose: print(sys.exc_info())
			print("cant open the astronomy image (verbose to see error)")
			return
		
		fig = plt.figure(1)
		plt.clf()
		titles = ["Original", "Model", "Residual"]
		scale = 6 # how much to stretch the data for contrast using log
		for i, title in enumerate(titles, start=1):
			a = fig.add_subplot(1,len(titles),i)
			a.set_title(title)
			data = hdu[i].data
			if i == 3: # residual
				data[data < 0] = 0
			data *= 10**scale
			data += 1
			data = np.log10(data)
			implot = plt.imshow(data)
			implot.set_cmap("cubehelix")
			implot.set_clim(0.0, scale)
			cb = plt.colorbar(ticks=range(scale+1), orientation='horizontal')
			cb.set_label("log10(pixel*$10^%d$+1)" % scale)
		
		dialog.MatPlotLibDialog(self.root, fig, filename.split("/")[-1])
		
	def main(self):
		'''
		start the application
		'''
		if self.verbose: print('Entering main loop')
		self.root.mainloop()
		
	def multiLinearRegression(self, event=None):
		'''
		Run a multiple linear regression
		'''
		if self.verbose: print("running multiple linear regression")
		headers = dialog.MultiLinearRegression(self.root, self.data,
										title="Pick Regression Axes").result
		if not headers:
			return
		results = analysis.linear_regression(self.data, headers[:-1], headers[-1])
		for header, slope in zip(headers[:-1], results[0][:-1]):
			print("m%s %.3f" % (header, slope))
		print("b %.3f" % results[0][-1])
		print("sse: %.3f" % results[1])
		print("R2: %.3f" % results[2])
		print("t: %s" % results[3])
		print("p: %s" % results[4])	
		
	def openData(self, event=None):
		'''
		open a dialog for picking data file and read into field
		'''
		initDir = "../csv"
		if not os.path.isdir(initDir):
			initDir = "."
		filename = tkf.askopenfilename(parent=self.root, title='Choose a data file', 
											initialdir=initDir )
		if filename:
			nodirfilename = filename.split("/")[-1]
			try:
				self.filename2data[nodirfilename] = Data(filename, self.verbose)
				if self.verbose: print("successfully read data")
			except:
				tkm.showerror("Failed File Read", "Failed to read %s" % filename)
				return
			self.openFilenames.delete(0, tk.END)
			selIndex = tk.END
			for i, fname in enumerate(self.filename2data):
				if fname == nodirfilename:
					selIndex = i
				self.openFilenames.insert(tk.END, fname)
			self.openFilenames.select_set(selIndex)
			self.openFilenames.bind("<Double-Button-1>", self.plotData)
		
	def pickDataAxes(self, event=None):
		'''
		pick the data axes and update the displayed data
		'''
		self.headers = dialog.PickAxesDialog(self.root, self.data, self.headers,
											title="Pick Data Axes").result
		if not self.headers: # if the user cancels the dialog, abort
			self.filename = None
			self.data = None
		else: # sets the active data and normalize it
			self.processData()
			
	def plotData(self, event=None):
		'''
		plot the data associated with the currently selected filename
		'''
		state = self.captureState()
		try:
			self.filename = self.openFilenames.get(self.openFilenames.curselection())
		except:
			tkm.showerror("No Selected Data", "Select opened data to plot")
			return
		self.setData()
		if self.data:
			self.update()
		else:
			self.restoreState(state)
			
	def preDefineColors(self):
		'''
		define the colors for the color selector control, keys are displayed
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
		define the distributions (see builtin random) for creating points
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
		define the shapes and canvas functions for representing points
		'''
		if self.verbose: print("defining initial shapes")
		self.shapeFunctions = OrderedDict()
		self.shapeFunctions["OVAL"] = [self.canvas.create_oval, []]
		self.shapeFunctions["RECTANGLE"] = [self.canvas.create_rectangle, []]
		self.shapeFunctions["DOWN TRIANGLE"] = [self.canvas.create_polygon, []]
		self.shapeFunctions["UP TRIANGLE"] = [self.canvas.create_polygon, []]
		self.shapeFunctions["X"] = [self.canvas.create_polygon, []]
		self.shapeFunctions["STAR"] = [self.canvas.create_polygon, []]
			
	def processData(self, event=None):
		'''
		use the data instance field to set active data fields
		'''
		# normalize the data and set the fields
		self.normalizedData = analysis.normalize_columns_separately(self.data, self.headers)
		self.shapeData = self.normalizedData[:, -1]
		self.shapeField.set(self.headers[-1])
		self.colorData = self.normalizedData[:, -2]
		self.colorField.set(self.headers[-2])
		self.sizeData = self.normalizedData[:, -3]
		self.sizeField.set(self.headers[-3])
		self.xLabel.set(self.headers[0].capitalize())
		self.yLabel.set(self.headers[1].capitalize())
		[rows, cols] = self.normalizedData.shape
		if cols < 6: # pad missing z data
			self.normalizedData = np.column_stack((self.normalizedData[:, :2], [0]*rows, [1]*rows))
			self.zLabel.set("")
		else: # pad the homogeneous coordinate
			self.normalizedData = np.column_stack((self.normalizedData[:, :3], [1]*rows))
			self.zLabel.set(self.headers[2].capitalize())
		
	def resetViewOrientation(self, event=None):
		'''
		set the view to the specified preset, maintaining current zoom
		'''
		presetStr = self.presetView.get().upper()
		curView = self.view.clone()
		self.view.reset() # return to default view
		self.view.offset = curView.offset.copy()
		self.view.screen = curView.screen.copy()
		self.view.extent = curView.extent.copy()
		if presetStr == "XZ":
			self.view.rotateVRC(0, 90)
		elif presetStr == "YZ":
			self.view.rotateVRC(90, 90)
		self.update()
		
	def resetViewZoom(self, event=None):
		'''
		set the view to the default zoom
		'''
		curView = self.view.clone()
		self.view.reset() # return to default view
		self.view.offset = curView.offset.copy()
		self.view.screen = curView.screen.copy()
		self.view.u = curView.u.copy()
		self.view.vpn = curView.vpn.copy()
		self.view.vup = curView.vup.copy()
		self.view.vrp = curView.vrp.copy()
		self.update()

	def resetView(self, event=None):
		'''
		set the view to the specified preset, including zoom reset
		'''
		curView = self.view.clone()
		self.view.reset() # return to default view
		self.view.offset = curView.offset.copy()
		self.view.screen = curView.screen.copy()
		self.update()
		
	def restoreState(self, state):
		'''
		using the given state, restore the fields
		'''
		self.data = state["data"]
		self.headers = state["headers"]
		self.filename = state["filename"]
		self.filteredData = state["filtered"]
		self.normalizedData = state["normalized"]
	
	def saveCanvas(self, event=None):
		'''
		saves the canvas to a postscript file
		'''
		filename = tkf.asksaveasfilename(defaultextension=".ps",
										parent=self.root,
										initialdir="..",
										title="Save Displayed Data")
		if not filename:
			return
		self.canvas.postscript(file=filename, colormode='color')
		
	def saveData(self, event=None):
		'''
		save the displayed data, prompting for a filename
		'''
		if not self.data:
			tkm.showerror("No Data", "No data to save")
			return
		initDir = "../csv"
		if not os.path.isdir(initDir):
			initDir = "."
		wfile = tkf.asksaveasfile(defaultextension=".csv",
								parent=self.root,
								initialdir=initDir,
								title="Save Displayed Data")
		if not wfile:
			return
		self.data.save(wfile)
		if self.verbose: print("saved successfully")
	
	def saveFilteredData(self, event=None):
		'''
		save the filtered data, prompting for a filename
		'''
		if not self.filteredData:
			tkm.showerror("No Data", "No data has been filtered")
			return
		initDir = "../csv"
		if not os.path.isdir(initDir):
			initDir = "."
		wfile = tkf.asksaveasfile(defaultextension=".csv",
								parent=self.root,
								initialdir=initDir,
								title="Save Filtered Data")
		if not wfile:
			return
		
		self.filteredData.save(wfile)
		if self.verbose: print("saved successfully")

	def setBindings(self):
		'''
		set the key bindings for the application
		'''
		if self.verbose: print("setting the key bindings")
		# bind mouse motions to the canvas
		self.canvas.bind( '<Button-1>', self.handleButton1 )
		self.canvas.bind( '<Double-Button-1>', self.handleDoubleButton1 )
		self.canvas.bind( '<Double-Button-2>', self.handleShowImage )
		self.canvas.bind( '<Double-Button-3>', self.handleShowImage )
		self.canvas.bind( '<Control-Button-1>', self.handleButton2 ) # same as B2
		self.canvas.bind( '<Button-2>', self.handleButton2 )
		self.canvas.bind( '<Button-3>', self.handleButton3 )
		self.canvas.bind( '<B1-Motion>', self.handleButton1Motion )
		self.canvas.bind( '<Control-B1-Motion>', self.handleButton2Motion ) # same as B2-Motion
		self.canvas.bind( '<B2-Motion>', self.handleButton2Motion )
		self.canvas.bind( '<B3-Motion>', self.handleButton3Motion )
		self.canvas.bind( '<Control-Shift-Button-1>', self.handleDelete )
		self.canvas.bind( '<Motion>', self.handleShowData )
		self.canvas.bind( '<Configure>', self.updateScreen ) # resizing canvas

		# bind command sequences to the root window
		self.root.bind( '<Control-f>', self.filterData)
		self.root.bind( '<Control-n>', self.clearData)
		self.root.bind( '<Control-o>', self.openData)
		self.root.bind( '<Control-p>', self.plotData)
		self.root.bind( '<Control-q>', self.handleQuit)
		self.root.bind( '<Control-s>', self.saveData)
		self.root.bind( '<Escape>', self.handleQuit)
	
	def setCanvasColor(self, event=None):
		'''
		sets the canvas color according to a user selected color
		'''
		if self.verbose: print("setting canvas color")
		#d = dialog.ColorMakerDialog(self.root, title="Create New Color")
		result = askcolor()
		if result[0]:
			self.canvas.itemconfig(self.canvasBG, fill=result[1])
	
	def setColorMode(self, event=None):
		'''
		callback for radio button, used to change color function for drawing
		'''
		cmstr = self.colorModeStr.get()
		if cmstr == "s":
			self.colorMode = self.getCurrentColor
		else:# cmstr == "d":
			self.colorMode = self.getColorByDepth
		self.update()
			
	def setData(self):
		'''
		sets the data field using the filename field, return if filename is None
		'''
		try:
			self.data = self.filename2data[self.filename] # opened data
		except:
			self.data = Data(self.filename, self.verbose) # creating points
		
		# check for missiing data
		if not self.data.get_headers():
			tkm.showerror("Insufficient Data", "Not enough columns of data to plot")
			self.filename = None
			self.data = None
			return
		
		# for only one column of data, make histogram
		if len(self.data.get_headers()) < 2:
			xvalues = self.data.matrix_data
			xlabel = self.data.get_headers()[0]
			try:
				ylabel = self.data.raw_types.index("STRING")
				ylabel = self.data.raw_headers[ylabel]
			except ValueError:
				print("no string type data found")
				ylabel = None
			title = self.filename
			# self.clearData()
			self.filename = None
			self.data = None
			fig = plt.figure(1)
			plt.clf()
			if ylabel == None:
				plt.hist(xvalues)
			else:
				plt.hist(xvalues)
				plt.ylabel(ylabel)
			plt.xlabel(xlabel)
			dialog.MatPlotLibDialog(self.root, fig, title)
			return

		# for more than one column, get headers from the user
		if not self.data:
			tkm.showerror("No Data", "No data to plot")
		else:
			self.filteredData = None
			self.headers = ["AGE(GYR)", "PX(PIXELS)", "PY(PIXELS)", 
						"RAD(PIXELS)","REDSHIFT(Z)","CAMERA"]
			for header in self.headers:
				if header not in [h.upper() for h in self.data.get_headers()]:
					if self.verbose: print("not astro data")
					self.headers = None
					break
			self.pickDataAxes()
		
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

	def setImageFilePath(self):
		'''
		setup the path to the image files for astro research
		'''
		if self.verbose: print(self.imageFilePath)
		path = tkf.askdirectory(parent=self.root, title='Choose a data file', 
							initialdir=self.imageFilePath )
		if path:
			self.imageFilePath = path
			
	def toggleLinearRegression(self, event=None):
		'''
		allows the user to toggle on/off a linear regression of displayed data
		'''
		if not self.data and self.linearRegressionEnabled.get():
			tkm.showerror("No Data", "No data to apply linear regression")
			self.linearRegressionEnabled.set(0)
			return
		if not self.linearRegressionEnabled.get():
			if self.verbose: print("removing linear regression")
			self.canvas.delete(self.fitLine)
			self.fitPoints = None
		else:
			
			# do the regression on the current view if data has 3 dimensions
			curView = self.presetView.get()
			if curView == "xy" or not self.zLabel.get():
				indHeader = self.xLabel.get().upper()
				depHeader = self.yLabel.get().upper()
			elif curView == "yz":
				indHeader = self.yLabel.get().upper()
				depHeader = self.zLabel.get().upper()
			else: # curView == "xz":
				indHeader = self.xLabel.get().upper()
				depHeader = self.zLabel.get().upper()
			if self.verbose: print("applying linear regression of %s and %s" %
								(indHeader, depHeader))
				
			# perform linear regression in data space
			slope, intercept, r, p, stderr = stats.linregress(
				self.data.get_data([indHeader, depHeader]))
			
			# use resulting intercept and slope to get normalized endpoints
			ranges = analysis.data_range(self.data, [indHeader, depHeader])
			indMin, indMax = ranges[0]
			indRange = indMax - indMin
			depMin, depMax = ranges[1]
			indlow = 0
			indhigh = 1
			deplow = (intercept-depMin)/(depMax-depMin)
			dephigh = ((intercept+slope*indRange)-depMin)/(depMax-depMin)
			
			# the normalized endpoints are interpreted based on current view
			if curView == "xy" or not self.zLabel.get():
				self.fitPoints = np.matrix([[indlow, deplow, 0, 1],
											[indhigh, dephigh, 0, 1]])
			elif curView == "yz":
				self.fitPoints = np.matrix([[0, indlow, deplow, 1],
											[0, indhigh, dephigh, 1]])
			else: #  curView == "xz":
				self.fitPoints = np.matrix([[indlow, 0, deplow, 1],
											[indhigh, 0, dephigh, 1]])
				
			# use the view to tranform from normalized to screen
			VTM = self.view.build()
			fitPts = (VTM * self.fitPoints.T).T
			self.fitLine = self.canvas.create_line(	fitPts[0, 0], fitPts[0, 1], 
													fitPts[1, 0], fitPts[1, 1],
													fill="red")
			#print("slope %.2f intercept %.2f r %.2f p %.2f stderr %.2f" %
			print("slope %f intercept %f r^2 %f p %f stderr %f" %
				(slope, intercept, r*r, p, stderr))
		
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
		VTM = self.view.build()
		axesPts = (VTM * self.axes.T).T
		labelPts = (VTM * self.axesLabels.T).T
		labelVars = [self.xLabel, self.yLabel, self.zLabel]
		if self.fitPoints != None:
			fitPts = (VTM * self.fitPoints.T).T
			self.canvas.coords(self.fitLine, 	fitPts[0, 0], fitPts[0, 1], 
												fitPts[1, 0], fitPts[1, 1])
		if self.data:
			ranges = analysis.data_range(self.data, self.headers)
		else:
			ranges = None
		for i, line in enumerate(self.lines):
			self.canvas.coords(line, 
								axesPts[2*i, 0], axesPts[2*i, 1], 
								axesPts[2*i+1, 0], axesPts[2*i+1, 1])
			self.canvas.coords(self.labels[i], labelPts[i, 0], labelPts[i, 1])
			axesLabel = labelVars[i].get()
			if ranges and (i < 2 or len(self.headers) > 5):
				axesLabel += "\n(%.2f, %.2f)" % tuple(ranges[i])
			self.canvas.itemconfigure(self.labels[i], text=axesLabel)

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
		self.view.offset[0, 0] = self.width*0.15
		self.view.offset[0, 1] = self.height*0.15
		self.view.screen[0, 0] = self.width*0.7
		self.view.screen[0, 1] = self.height*0.7
		self.update()
		
	def zoomIn(self):
		'''
		contract the extent of the view by a constant factor
		'''
		self.view.extent *= 0.9
		self.update()
		
	def zoomOut(self):
		'''
		expand the extent of the view by a constant factor
		'''
		self.view.extent *= 1.1
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
	DisplayApp(1200, 900, options.filename, options.verbose).main()
