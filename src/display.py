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
import os
import numpy as np
import math
from scipy import stats
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.image as image

# defined by me for this project
import analysis
import classifiers
from data import Data
import dialogs
from view import View
from photos import colors

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
import tkMessageBox as tkm
import tkSimpleDialog as tks
from tkColorChooser import askcolor
	
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
		self.delimiter = ","
		self.headers = None
		self.filteredData = None
		self.normalizedData = None
		self.manualDataRanges = {}
		self.width = None
		self.height = None
		self.filename2data = {}
		self.preDefineDistributions()
		self.objects = {} # shapes drawn on canvas and their row in the data
		self.root = tk.Tk()
		self.fitPoints = None
		self.linearRegressionEnabled = tk.BooleanVar()
		self.dataLines = []
		self.linePlot = tk.BooleanVar()
		self.enableTicks = tk.BooleanVar()		
		self.enableTicks.set(True)
		self.xLabel = tk.StringVar( self.root )
		self.yLabel = tk.StringVar( self.root )
		self.zLabel = tk.StringVar( self.root )
		self.xLabel.set("X")
		self.yLabel.set("Y")
		self.zLabel.set("Z")
		self.colors = ["blue","red","green","purple","yellow","orange","salmon","maroon","black","goldenrod"]

		# set up the geometry for the window
		self.root.geometry( "%dx%d+50+30" % (width, height) )
		
		# set the title of the window
		# PICKUP: Plotting by Ingenious Computer Kid in an Undergraduate Program
		# PLAD: Plotting and Analysis of Data
		# DAPPER: Data Analysis and Plotting for Producing/Portraying Exceptional Results
		self.root.title("DAPPER") # TODO: better name
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
		
		# build the axesPts
		self.buildAxes()
		
		if filename:
			try: # handle error caused by exiting application with dialogs open
				self.setData()
				self.update()
			except tk.TclError:
				exit()

	def buildAxes(self, axes=[[0,0,0],[1,0,0],
							  [0,0,0],[0,1,0],
							  [0,0,0],[0,0,1]]):
		'''
		builds the view transformation matrix [VTM], 
		multiplies the axis endpoints by the VTM, 
		then creates three new line objects, one for each axis
		Note: only called once by __init__, then updateAxes used
		'''
		if self.verbose: print("building the axesPts")
		self.view = View(offset=[self.width*0.15, self.height*0.15],
							screen=[self.width*0.7, self.height*0.7])
		self.baseView = self.view.clone() # in case b2 motion happens without click
		
		# set up the fields for holding normalized locations of axes objects
		self.axesPts = np.asmatrix(axes, dtype=np.float)
		self.axesLabelsPts = []
		self.numTicks = 5
		self.ticksMarksPts = []
		self.ticksLabelsPts = []
		for i in range(3):
			low = self.axesPts[2*i] 
			high = self.axesPts[2*i+1]
			self.axesLabelsPts.append(high.copy())
			self.axesLabelsPts[-1] -= 0.06
			self.axesLabelsPts[-1][0,i] += 0.12
			step = (high-low)/(self.numTicks-1.0)
			for j in range(self.numTicks):
				cur = low + j*step
				curLow = cur - 0.02
				curLow[0,i] += 0.02
				curHigh = cur + 0.02
				curHigh[0,i] -= 0.02
				self.ticksMarksPts.append(curLow)
				self.ticksMarksPts.append(curHigh)
				curLabel = cur - 0.04
				curLabel[0,i] += 0.04
				self.ticksLabelsPts.append(curLabel)
				
		self.axesLabelsPts = np.vstack(self.axesLabelsPts)	
		self.ticksMarksPts = np.vstack(self.ticksMarksPts)		
		self.ticksLabelsPts = np.vstack(self.ticksLabelsPts)
		self.axesPts = analysis.appendHomogeneous(self.axesPts)
		self.axesLabelsPts = analysis.appendHomogeneous(self.axesLabelsPts)
		self.ticksMarksPts = analysis.appendHomogeneous(self.ticksMarksPts)
		self.ticksLabelsPts = analysis.appendHomogeneous(self.ticksLabelsPts)
		
		VTM = self.view.build()
		axesPts = (VTM * self.axesPts.T).T
		axesLabelsPts = (VTM * self.axesLabelsPts.T).T
		ticksMarksPts = (VTM * self.ticksMarksPts.T).T
		ticksLabelsPts = (VTM * self.ticksLabelsPts.T).T
		self.axes = []
		self.axesLabels = []
		self.ticksMarks = []
		self.ticksLabels = []
		labelVars = [self.xLabel, self.yLabel, self.zLabel]
		for i in range(3):
			self.axes.append(self.canvas.create_line(
				axesPts[2*i, 0], axesPts[2*i, 1], 
				axesPts[2*i+1, 0], axesPts[2*i+1, 1]))
			self.axesLabels.append(self.canvas.create_text(
				axesLabelsPts[i, 0], axesLabelsPts[i, 1], 
				font=("Purina", 10), text=labelVars[i].get()))
			for j in range(self.numTicks):
				self.ticksMarks.append(self.canvas.create_line(
					ticksMarksPts[self.numTicks*2*i + 2*j, 0], 
					ticksMarksPts[self.numTicks*2*i + 2*j, 1], 
					ticksMarksPts[self.numTicks*2*i + 2*j+1, 0], 
					ticksMarksPts[self.numTicks*2*i + 2*j+1, 1]))
				self.ticksLabels.append(self.canvas.create_text(
					ticksLabelsPts[self.numTicks*i + j, 0], 
					ticksLabelsPts[self.numTicks*i + j, 1], 
					font=("Purina", 8), 
					text=""))#str(self.numTicks*i + j)))
			
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
		self.odatas = tk.Listbox(self.rightcntlframe, selectmode=tk.SINGLE, 
										exportselection=0, height=3)
		self.odatas.bind("<Double-Button-1>", self.plotData)
		self.odatas.grid( row=row, columnspan=3 )
		row+=1

		# make a plot button in the frame
		tk.Button( self.rightcntlframe, text="Plot", 
				   command=self.plotData, width=5
				   ).grid( row=row, column=0 )
		tk.Button( self.rightcntlframe, text="Delete", 
				   command=self.openFilesDelete, width=5
				   ).grid( row=row, column=1 )
		tk.Button( self.rightcntlframe, text="Rename", 
				   command=self.openFilesRename, width=5
				   ).grid( row=row, column=2 )
		row+=1
		tk.Frame( self.rightcntlframe, height=2, bd=1, relief=tk.SUNKEN
				  ).grid( row=row, columnspan=3, pady = 10, sticky=tk.EW)
		row+=1

		# make a get at bat button in the frame
		tk.Button( self.rightcntlframe, text="Gen At Bat Data", 
				   command=self.genAtBatData, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1

		# make a plot button in the frame
		tk.Button( self.rightcntlframe, text="Change Axes", 
				   command=self.changeDataAxes, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1

		# make a plot button in the frame
		tk.Button( self.rightcntlframe, text="Change Ranges", 
				   command=self.changeRanges, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1
		
		# make a filter button in the frame
		tk.Button( self.rightcntlframe, text="Filter", 
				   command=self.filterData, width=10
				   ).grid( row=row, columnspan=3 )
		row+=1

		# make a save button in the frame
		tk.Button( self.rightcntlframe, text="Save Displayed", 
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
		
		presets = self.getPresets()
		self.zLabel.trace("w", self.updatePresets)
		self.presetView = tk.StringVar()
		self.presetView.set(presets[0])
		self.presetControl = tk.OptionMenu( self.rightcntlframe, self.presetView, 
									*presets, command=self.resetViewOrientation)
		self.presetControlRow = row
		self.presetControl.grid( row=self.presetControlRow, columnspan=3 )
		row+=1

		# make a plot button in the frame
		tk.Button( self.rightcntlframe, text="Multiple Linear Regression", 
				   command=self.multiLinearRegression,
				   ).grid( row=row, columnspan=3 )
		row+=1
		
		# linear regression control
		tk.Checkbutton( self.rightcntlframe, text="2D Linear Regression",
					variable=self.linearRegressionEnabled,
					command=self.toggleLinearRegression,
					   ).grid( row=row, columnspan=3 )
		row+=1
		
		# connecting axes control
		tk.Checkbutton( self.rightcntlframe, text="Line Plot",
					variable=self.linePlot, command=self.update
					   ).grid( row=row, columnspan=3 )
		row+=1
		
		# disable ticks
		tk.Checkbutton( self.rightcntlframe, text="Enable Ticks",
					variable=self.enableTicks, command=self.updateAxes
					   ).grid( row=row, columnspan=3 )
		row+=1
		
		# size selector
		tk.Label( self.rightcntlframe, text="\nSize"
					   ).grid( row=row, columnspan=3 )
		row+=1

		# make a size mode selector in the frame
		sizeModes = [
			("Size By Data", "d"),
			("Selected Size", "s")
		]
		self.sizeModeStr = tk.StringVar()
		self.sizeModeStr.set("d") # initialize
		for text, mode in sizeModes:
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
		shapeModes = [
			("Shape By Data", "d"),
			("Selected Shape", "s")
		]
		self.shapeModeStr = tk.StringVar()
		self.shapeModeStr.set("d") # initialize
		for text, mode in shapeModes:
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
			("Gradient Color", "g"),
			("Discrete Color", "d"),
			("Selected Color", "s")
		]
		self.colorModeStr = tk.StringVar()
		self.colorModeStr.set("g") # initialize
		self.getColor = self.getColorGradient
		for text, mode in colorModes:
			b = tk.Radiobutton(self.rightcntlframe, text=text,
							variable=self.colorModeStr, value=mode, 
							command=self.setColorMode)
			b.grid( row=row, columnspan=3 )
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
			
			# line plotting, currently ordered according to csv
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
		canvasmenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Canvas", menu = canvasmenu )
		menulist.append([canvasmenu,
						[['Save Canvas', self.saveCanvas],
						 ['Set Canvas Color', self.setCanvasColor],
						 ['Clear, Ctrl-N', self.clearData]
						 ]])

		# create another menu for data
		datamenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Data", menu = datamenu )
		menulist.append([datamenu,
						[['Save Displayed Data', self.saveData],
						 ['Plot Selected, Ctrl-P', self.plotData],
						 ['Set Delimiter, Ctrl-D', self.setDelimiter],
						 ['Filter, Ctrl-F', self.filterData],
						 ['Save Filtered Data', self.saveFilteredData],
						 ['Change Axes', self.changeDataAxes],
						 ['Change Ranges', self.changeRanges],
						 ['Multiple Linear Regression', self.multiLinearRegression],
						 ]])
		
		# create another menu for analysis
		anamenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Analysis", menu = anamenu )
		menulist.append([anamenu,
						[['Run PCA', self.pcaRun],
						 ['Show PCA', self.pcaShow],
						 ['Save PCA', self.pcaSave],
						 ['Run Kmeans', self.kmeansRun],
						 ['Classify', self.classify]
						 ]])

		# create another menu for color
		viewmenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "View", menu = viewmenu )
		menulist.append([viewmenu,
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
						 ['', None]
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
				
				# sub cascade (could be recursive, only depth 1 now)
				elif isinstance(item[1], types.ListType):
					submenu = tk.Menu(self.menu)
					for subitem in item[1]:
						submenu.add_command(label=subitem[0], command=subitem[1])
					menu.add_cascade( label=item[0], menu=submenu )
				
				# menu command
				else:
					menu.add_command( label=item[0], command=item[1] )
		
		optionsmenu = tk.Menu( self.menu )
		self.menu.add_cascade( label = "Options", menu = optionsmenu )
		optionsmenu.add_checkbutton(label="2D Linear Regression", 
								variable=self.linearRegressionEnabled,
								command=self.toggleLinearRegression)
		optionsmenu.add_checkbutton(label="Line Plot", variable=self.linePlot)
		optionsmenu.add_checkbutton(label="Enable Tick Marks", 
								variable=self.enableTicks,
								command=self.updateAxes)
		
	def buildStatusFrame(self):
		'''
		build the frame and the status axesLabels
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
		tk.Label(bottomstatusframe, textvariable=self.xLabel
				 ).grid(row=0, column=cols)
		tk.Label(bottomstatusframe, textvariable=self.yLabel
				 ).grid(row=1, column=cols)
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
		prompts the user to change the displayed data axesPts if any
		'''
		if not self.data:
			tkm.showerror("No Data Plotted", "No data to change axesPts")
			return
		state = self.captureState()
		self.pickDataAxes()
		if not self.data:
			self.restoreState(state)
		else:
			self.update()
			
	def changeRanges(self, event=None):
		'''
		set the ranges of the axesPts
		'''
		if not self.data:
			tkm.showerror("No Data Plotted", "No data to change ranges")
			return
		if len(self.headers) == 5:
			headers = self.headers[:2]
		else:
			headers = self.headers[:3]
		newRanges = dialogs.SetDataRanges(self.root, self.data, 
										self.manualDataRanges, headers,
										"Set Data Ranges").result
		if self.verbose: print("changing ranges: %s" % newRanges)
		if not newRanges:
			tkm.showerror("Range Change Failed", "Data will not be changed")
			return
		# use new ranges to update manual data ranges dictionary
		for header, newRange in zip(headers, newRanges):
			self.manualDataRanges[header] = newRange
		# TODO: self.excludeData(newRanges) would eliminate data outside new range
		self.processData()
		self.update()
		
	def classify(self):
		'''
		present a dialog for running classification
		assumes selected filename is the open training data
		'''
		try:
			curFilename = self.odatas.get(self.odatas.curselection())
		except:
			print("No open files")
			return
		dtrain = self.filename2data[curFilename]
		result = dialogs.ClassifyDialog(self.root, dtrain, self.filename2data).result
		if not result:
			return
		dtest, classHeader, headers, knnbool, k = result
		try:
			k = int(k)
		except:
			k = None
		testNotOpened = dtest == None
		noClassHeader = classHeader.upper() == "NONE"
		initDir = "../csv"
		if not os.path.isdir(initDir):
			initDir = "."
		if noClassHeader:
			# get a filename for the test category data
			filename = tkf.askopenfilename(parent=self.root, 
										title='Choose a training categories file', 
										initialdir=initDir,
										filetypes=[("All Files","*"),
												("Data files", "*.csv")])
			if not filename:
				return
			traincats = Data(filename)
			dtrain.add_column(traincats.get_raw_headers()[0], 
							traincats.get_raw_types()[0], 
							traincats.raw_data[:, 0])
			classHeader = traincats.get_raw_headers()[0]
		if testNotOpened:
			# get a filename for the training data
			fndtest = tkf.askopenfilename(parent=self.root, 
										title='Choose a testing data file', 
										initialdir=initDir,
										filetypes=[("All Files","*"),
												("Data files", "*.csv")])
			if not fndtest:
				return
			dtest = Data(fndtest)
		if classHeader not in dtest.get_raw_headers():
			# get a filename for the test category data
			filename = tkf.askopenfilename(parent=self.root, 
										title='Choose a testing categories file', 
										initialdir=initDir,
										filetypes=[("All Files","*"),
												("Data files", "*.csv")])
			if filename:
				testcats = Data(filename)
				dtest.add_column(testcats.get_raw_headers()[0], 
								testcats.get_raw_types()[0], 
								testcats.raw_data[:, 0])

		classes = classifiers.classify(dtrain, dtest, classHeader, headers, knnbool, k)
		colName = "Classifications_"
		colName += "k="+str(k) if knnbool else "NB"
		dtest.add_column(colName, "NUMERIC", classes)
		if testNotOpened: self.openFilesAppend(fndtest.split("/")[-1], dtest)
		
	def clearData(self, event=None):
		'''
		clear the data from the canvas
		'''
		if self.verbose: print("clearing data from canvas")
		self.clearObjects()
		self.filename = None
		self.data = None
		self.manualDataRanges = {}
		self.updateNumObjStrVar()
		self.xLocation.set("----")
		self.yLocation.set("----")
		self.zLocation.set("----")
		self.xLabel.set("X")
		self.yLabel.set("Y")
		self.zLabel.set("Z")
		self.colorField.set("")
		self.sizeField.set("")
		self.shapeField.set("")
		self.removeFit()
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
		points = tks.askinteger("Number of Points", 
							"Enter the number of points to be created",
							parent=self.root, initialvalue=100,
							minvalue=1, maxvalue=9999)
		if not points:
			return
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
		display the application about dialogs
		'''
		dialogs.AboutAppDialog(self.root, title="About Application")

	def displayAboutMe(self, event=None):
		'''
		display the author about dialogs
		'''
		dialogs.AboutMeDialog(self.root, title="About Me")

	def displayAboutSteph(self, event=None):
		'''
		display the Stephanie about dialogs
		'''
		dialogs.AboutStephDialog(self.root, title="About Stephanie Taylor")

	def displayAboutBruce(self, event=None):
		'''
		display the Bruce about dialogs
		'''
		dialogs.AboutBruceDialog(self.root, title="About Bruce Maxwell")

	def displayBindings(self, event=None):
		'''
		display the Key Bindings about dialogs
		'''
		dialogs.BindingsDialog(self.root, title="Key Bindings")
	
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
			shape = shapeFunc(coords, fill=self.getColor(self.colorData[row, 0]), 
							outline='')
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
		newRanges = dialogs.FilterDataDialog(self.root, self.data, 
										title="Filter Data").result
		if self.verbose: print("filtering: %s" % newRanges)
		if not newRanges:
			tkm.showerror("Filter Failed", "Data will not be filtered")
			return
		self.excludeData(newRanges)
		self.processData()
		self.update()
	
		
	def genAtBatData(self):
		try:
			curFilename = self.odatas.get(self.odatas.curselection())
		except:
			print("No open files")
			return
		print("getting at bat data")
		data = self.filename2data[curFilename]
		result = dialogs.GetAtBatID(self.root, data).result
		if not result:
			return
		[atBatID, numFrames] = result
		try:
			numFrames = float(numFrames)
		except:
			numFrames = 20.0
		atBatIDs = np.squeeze(np.asarray(data.get_data(["AB_ID"])))
		atBatData = data.get_data(data.get_headers())[atBatIDs == atBatID]
		sx = data.header2matrix["XSTART"]
		sy = data.header2matrix["YSTART"]
		sz = data.header2matrix["ZSTART"]
		ex = data.header2matrix["XEND"]
		ey = data.header2matrix["YEND"]
		ez = data.header2matrix["ZEND"]
		vx = data.header2matrix["XVEL"]
		vy = data.header2matrix["YVEL"]
		vz = data.header2matrix["ZVEL"]
		ax = data.header2matrix["XACC"]
		ay = data.header2matrix["YACC"]
		az = data.header2matrix["ZACC"]
		newData = [["TS", "SPEED", "X", "Y", "Z"] + data.get_headers(), 
				["NUMERIC"]*5 + data.get_types()]
		for pitch in atBatData:
			frames = self.getCurve(numFrames, 
						pitch[0, sx], pitch[0, sy], pitch[0, sz], 
						pitch[0, ex], pitch[0, ey], pitch[0, ez], 
						pitch[0, vx], pitch[0, vy], pitch[0, vz], 
						pitch[0, ax], pitch[0, ay], pitch[0, az])
			for frame in frames:
				newData.append(pitch.tolist()[0] + frame)
		fn = "ab:"+str(atBatID)
		self.openFilesAppend(fn, Data(newData, verbose=self.verbose))			
	
	def getColorCurrent(self, z=None):
		'''
		get the current color selected by the controls as hex string
		'''
		rgb = ("#%02x%02x%02x" % 
			(int(self.redBand.get()), 
			int(self.greenBand.get()), 
			int(self.blueBand.get())))
		if rgb in ["black", "#000000"]: rgb = "#000001" # FIXME black causes bad damage rectangle
		return rgb
	
	def getColorDiscrete(self, z):
		'''
		get the discrete color selected by the controls as hex string
		'''
		z = max(min(z, 1.0), 0.0) # in case depth is not normalized
		if len(np.unique(np.squeeze(np.asarray(self.colorData)))) <= len(self.colors):
			rgb = self.colors[int(z*(len(self.colors)-1))]
		else:
			rgb = colors[int(z*(len(colors)-1))]
		if rgb in ["black", "#000000"]: rgb = "#000001" # FIXME black causes bad damage rectangle
		return rgb
	
	def getColorGradient(self, z):
		'''
		return the color according the given normalized z as hex string
		'''
		z = max(min(z, 1.0), 0.0) # in case depth is not normalized
		
		rb = int(z * 255.0)
		gb = 0
		bb = 255 - int(z * 255.0)
		return "#%02x%02x%02x" % (rb, gb, bb)

	def getCurrentPreset(self):
		'''
		return the upper case string of the selected preset (XY | YZ | XZ)
		'''
		presets = self.getPresets()
		if self.presetView.get() == presets[0]:
			return "XY"
		elif self.presetView.get() == presets[1]:
			return "YZ"
		else: # self.presetView.get() == presets[0]:
			return "XZ"
		
	def getCurve(self, frames, sx, sy, sz, ex, ey, ez, vx, vy, vz, ax, ay, az):
		'''
		return a list of frames with time, speed, x, y, and z for each of the frames
		'''
		# distance to plate
		dy = sy - ey
		# time to plate
		qsqrt = math.sqrt(vy*vy - 2*ay*dy)
		t = min( (-vy + qsqrt)/ay, (-vy - qsqrt)/ay )
		def _x(t):
			return sx + vx*t + 0.5*ax*(t**2)
		def _y(t):
			return sy + vy*t + 0.5*ay*(t**2)
		def _z(t):
			return sz + vz*t + 0.5*az*(t**2)
		
		#Get velocity at time t
		def _vx(t):
			return vx+t*ax
		def _vy(t):
			return vy+t*ay
		def _vz(t):
			return vz+t*az
		
		#Get speed at time t
		def _speed(t):
			return math.sqrt(_vx(t)**2 + _vy(t)**2 +_vz(t)**2)
		
		# sample the curve, making x and y coordinate lists
		results = []
		for ct in np.arange(0, t, t/frames):
			results.append([ct, _speed(ct), _x(ct), _y(ct), _z(ct)])
		return results
	
	def getPresets(self):
		'''
		return the presets for the current x, y, and z labels
		'''
		presets = [self.xLabel.get()[:min(5, len(self.xLabel.get()))]+" - "+
				   self.yLabel.get()[:min(5, len(self.yLabel.get()))], 
				   self.yLabel.get()[:min(5, len(self.yLabel.get()))]+" - "+
				   self.zLabel.get()[:min(5, len(self.zLabel.get()))],
				   self.xLabel.get()[:min(5, len(self.xLabel.get()))]+" - "+
				   self.zLabel.get()[:min(5, len(self.zLabel.get()))]
				   ]
		return presets if self.zLabel.get() else presets[:1]
		
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
		#d = dialogs.ColorMakerDialog(self.root, title="Create New Color")
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
		except:
			print("cant open the astronomy image (verbose to see error)")
			return
		
		fig = plt.figure(1)
		plt.clf()
		titles = ["Original", "Model", "Residual"]
		scale = 4 # how much to stretch the data for contrast using log
		for i, title in enumerate(titles, start=1):
			a = fig.add_subplot(1,len(titles),i)
			a.set_title(title)
			data = hdu[i].data
			#if i == 3: # residual
			#	data[data < 0] = 0
			#elif i == 1:
			#	scale = -int(np.log10(np.median(data)))
				
			data -= np.min(data)
			data /= np.max(data)
			data *= 10**scale
			data = np.log10(data+1)/np.log10(data)
			implot = plt.imshow(data)
			implot.set_cmap("cubehelix")
			#implot.set_clim(0.0, scale)
			cb = plt.colorbar(orientation='horizontal')#ticks=range(scale+1), 
			cb.set_label("log10($pixel*10^"+str(scale)+"+1$)")
		
		dialogs.MatPlotLibDialog(self.root, fig, filename.split("/")[-1])
		
	def kmeansRun(self):
		'''
		run kmeans clumping
		'''
		try:
			curFilename = self.odatas.get(self.odatas.curselection())
		except:
			print("No open files")
			return
		data = self.filename2data[curFilename]
		result = dialogs.RunKmeans(self.root, data).result
		if not result:
			return
		colName, k, colHeaders, categories = result
		if self.verbose: print("running kmeans")
		codebook, codes, errors = analysis.kmeans(data, colHeaders, k, categories)
		if self.verbose: print("kmeans done")
		if not colName:
			colName = "-".join(["kmeans%d" % k] + [h[:2] for h in colHeaders])
		data.add_column(colName, "NUMERIC", codes)
		
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
		try:
			curFilename = self.odatas.get(self.odatas.curselection())
		except:
			print("No open files")
			return
		data = self.filename2data[curFilename]
		if self.verbose: print("running multiple linear regression")
		headers = dialogs.MultiLinearRegression(self.root, data,
										title="Pick Regression Axes").result
		if not headers:
			return
		results = analysis.linear_regression(data, headers[:-1], headers[-1])
		for header, slope in zip(headers[:-1], results[0][:-1]):
			print("m%s %.3f" % (header, slope))
		print("b %.3f" % results[0][-1])
		print("sse: %.3f" % results[1])
		print("R2: %.3f" % results[2])
		print("t: %s" % results[3])
		print("p: %s" % results[4])	
		
	def openData(self, event=None):
		'''
		open a dialogs for picking data file and read into field
		'''
		initDir = "../csv"
		if not os.path.isdir(initDir):
			initDir = "."
		filename = tkf.askopenfilename(parent=self.root, 
									title='Choose a data file', 
									initialdir=initDir,
									filetypes=[("All Files","*"),
											("Data files", "*.csv")])
		if filename:
			nodirfilename = filename.split("/")[-1]
			try:
				newData = Data(filename, self.delimiter, self.verbose)
				if self.verbose: print("successfully read data")
			except:
				tkm.showerror("Failed File Read", "Failed to read %s" % filename)
				return
			self.openFilesAppend(nodirfilename, newData)

	def openFilesAppend(self, filename, data):
		'''
		append to the listbox displaying open filenames
		'''
		self.filename2data[filename] = data
		self.odatas.delete(0, tk.END)
		selIndex = tk.END
		for i, fname in enumerate(self.filename2data):
			if fname == filename:
				selIndex = i
			self.odatas.insert(tk.END, fname)
		self.odatas.select_set(selIndex)

	def openFilesDelete(self):
		'''
		delete selected item from the listbox displaying open filenames
		'''
		try:
			selIndex = self.odatas.curselection()
		except:
			print("No open files")
			return
		fn = self.odatas.get(selIndex)
		self.odatas.delete(selIndex)
		del self.filename2data[fn]
		try:
			self.odatas.select_set(0)
		except:
			pass

	def openFilesRename(self):
		'''
		rename selected item from the listbox displaying open filenames
		'''
		try:
			filename = self.odatas.get(self.odatas.curselection())
		except:
			print("No open files")
			return
		newfn = tks.askstring("Rename File", 
							"Input the new filename",
							parent=self.root, initialvalue=filename)
		if not newfn or newfn == filename:
			return
		self.filename2data[newfn] = self.filename2data[filename]
		del(self.filename2data[filename])
		self.odatas.delete(0, tk.END)
		selIndex = tk.END
		for i, fname in enumerate(self.filename2data):
			if fname == newfn:
				selIndex = i
			self.odatas.insert(tk.END, fname)
		self.odatas.select_set(selIndex)
		
	def pcaRun(self):
		'''
		perform a pca analysis
		'''
		try:
			curFilename = self.odatas.get(self.odatas.curselection())
		except:
			print("No open files")
			return
		data = self.filename2data[curFilename]
		result = dialogs.RunPCA(self.root, data).result
		if not result:
			return
		filename, normBool, colHeaders = result
		if self.verbose: print("running pca")
		pcaData = analysis.pca(data, colHeaders, normBool, self.verbose)
		if self.verbose: print("pca done")
		if not filename:
			filename = "-".join(["pca", curFilename] + [h[:2] for h in colHeaders])
		self.openFilesAppend(filename, pcaData)
		
	def pcaSave(self):
		'''
		save the selected pca to a file	
		'''
		try:
			filename = self.odatas.get(self.odatas.curselection())
		except:
			tkm.showerror("No Selected Data", "Select opened data to save")
			return
		try: # verify that the data is a PCAData instance
			self.filename2data[filename].means
		except:
			print("Not PCA data, cancelling")
			return
		initDir = "../csv"
		if not os.path.isdir(initDir):
			initDir = "."
		wfile = tkf.asksaveasfilename(defaultextension=".csv",
								parent=self.root,
								initialdir=initDir,
								initialfile=filename,
								title="Save Displayed Data")
		if wfile:
			self.filename2data[filename].save(wfile)
	
	def pcaShow(self):
		'''
		show a pca analysis
		'''
		try:
			curFilename = self.odatas.get(self.odatas.curselection())
		except:
			print("No open files")
			return
		dialogs.ShowPCA(self.root, self.filename2data[curFilename])
		
	def pickDataAxes(self, event=None):
		'''
		pick the data axesPts and update the displayed data
		'''
		self.headers = dialogs.PickAxesDialog(self.root, self.data, self.headers,
											title="Pick Data Axes").result
		if not self.headers: # if the user cancels the dialogs, abort
			self.data = None
		else: # sets the active data and normalize it
			self.manualDataRanges = {}
			self.removeFit()
			self.processData()
			self.resetViewOrientation()
			
	def plotData(self, event=None):
		'''
		plot the data associated with the currently selected filename
		'''
		state = self.captureState()
		try:
			self.filename = self.odatas.get(self.odatas.curselection())
		except:
			print("No open files")
			return
		self.setData()
		if self.data:
			self.update()
		else:
			self.restoreState(state)
			
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
		forceRanges = [self.manualDataRanges[header] 
					if header in self.manualDataRanges else [] 
					for header in self.headers]
		self.normalizedData = analysis.normalize_columns_separately(self.data, 
																self.headers,
																forceRanges)
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
			self.normalizedData = np.column_stack((self.normalizedData[:, :2], 
												np.zeros(rows), np.ones(rows)))
			self.zLabel.set("")
		else: # pad the homogeneous coordinate
			self.normalizedData = np.column_stack((self.normalizedData[:, :3], 
												np.ones(rows)))
			self.zLabel.set(self.headers[2].capitalize())
		
	def removeFit(self):
		'''
		remove the linear fit from the canvas if there is one
		'''
		if self.fitPoints != None:
			self.linearRegressionEnabled.set(0)
			self.canvas.delete(self.fitLine)
			self.fitPoints = None
		
	def resetViewOrientation(self, event=None):
		'''
		set the view to the specified preset, maintaining current zoom
		'''
		preset = self.getCurrentPreset()
		curView = self.view.clone()
		self.view.reset() # return to default view
		self.view.offset = curView.offset.copy()
		self.view.screen = curView.screen.copy()
		self.view.extent = curView.extent.copy()
		if preset == "XZ":
			self.view.rotateVRC(0, 90)
		elif preset == "YZ":
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
		self.presetView.set(self.getPresets()[0])
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
		initDir = "../images"
		if not os.path.isdir(initDir):
			initDir = ".."
		filename = tkf.asksaveasfilename(defaultextension=".ps",
										parent=self.root,
										initialdir=initDir,
										title="Save Displayed Data")
		if not filename:
			return
		self.canvas.postscript(file=filename, colormode='color')
		if self.verbose: print("saved canvas as %s" % filename)
		try:
			img = image.imread(filename)
			newFilename = ".".join(filename.split(".")[:-1]+["png"])
			image.imsave(newFilename,img)
			#os.remove(filename) # comment to keep ps file
			if self.verbose: print("saved canvas as %s" % newFilename)
		except:
			pass
		
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
		wfile = tkf.asksaveasfilename(defaultextension=".csv",
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
		wfile = tkf.asksaveasfilename(defaultextension=".csv",
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
		self.root.bind( '<Control-d>', self.setDelimiter)
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
		#d = dialogs.ColorMakerDialog(self.root, title="Create New Color")
		result = askcolor()
		if result[0]:
			self.canvas.itemconfig(self.canvasBG, fill=result[1])
	
	def setColorMode(self, event=None):
		'''
		callback for radio button, used to change color function for drawing
		'''
		cmstr = self.colorModeStr.get()
		if cmstr == "s":
			self.getColor = self.getColorCurrent
		elif cmstr == "g":
			self.getColor = self.getColorGradient
		else:# cmstr == "d":
			self.getColor = self.getColorDiscrete
		self.update()
			
	def setData(self):
		'''
		sets the data field using the filename field, return if filename is None
		'''
		try:
			self.data = self.filename2data[self.filename] # opened data
		except:
			self.data = Data(self.filename, self.delimiter, self.verbose) # creating points
		
		# check for missiing data
		if not self.data.get_headers():
			tkm.showerror("Insufficient Data", "Not enough columns of data to plot")
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
			self.data = None
			fig = plt.figure(1)
			plt.clf()
			if ylabel == None:
				plt.hist(xvalues)
			else:
				plt.hist(xvalues)
				plt.ylabel(ylabel)
			plt.xlabel(xlabel)
			dialogs.MatPlotLibDialog(self.root, fig, title)
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
		
	def setDelimiter(self, event=None):
		'''
		set the delimiter used for reading in data files
		'''
		delim = tks.askstring("Set Delimiter", 
							"Input the new delimiter for reading data files",
							parent=self.root, initialvalue=self.delimiter)
		if delim and delim != self.delimiter:
			if self.verbose: print("changing delimiter from '%s' to '%s'" % 
								(self.delimiter, delim))
			self.delimiter = delim
		
	def setDistribution(self, event=None):
		'''
		select the distribution using the dialogs and update status
		'''
		if self.verbose: print("setting a new distribution")
		[xDistribution, yDistribution, zDistribution] = \
			dialogs.DistributionDialog(self.root, 
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
			self.removeFit()
		else:
			
			# do the regression on the current view if data has 3 dimensions
			curView = self.getCurrentPreset()
			if curView == "XY" or not self.zLabel.get():
				indHeader = self.xLabel.get().upper()
				depHeader = self.yLabel.get().upper()
			elif curView == "YZ":
				indHeader = self.yLabel.get().upper()
				depHeader = self.zLabel.get().upper()
			else: # curView == "XZ":
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
			depMin, depMax = ranges[1]
			indlow = 0
			indhigh = 1
			deplow = ((intercept+slope*indMin)-depMin)/(depMax-depMin)
			dephigh = ((intercept+slope*indMax)-depMin)/(depMax-depMin)
			
			# the d endpoints are interpreted based on current view
			if curView == "XY" or not self.zLabel.get():
				self.fitPoints = np.matrix([[indlow, deplow, 0, 1],
											[indhigh, dephigh, 0, 1]])
			elif curView == "YZ":
				self.fitPoints = np.matrix([[0, indlow, deplow, 1],
											[0, indhigh, dephigh, 1]])
			else: #  curView == "XZ":
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
		updates the axesPts line objects with the current vtm
		'''
		VTM = self.view.build()
		axesPts = (VTM * self.axesPts.T).T
		axesLabelsPts = (VTM * self.axesLabelsPts.T).T
		ticksMarksPts = (VTM * self.ticksMarksPts.T).T
		ticksLabelsPts = (VTM * self.ticksLabelsPts.T).T
		labelVars = [self.xLabel, self.yLabel, self.zLabel]
		if self.fitPoints != None:
			fitPts = (VTM * self.fitPoints.T).T
			self.canvas.coords(self.fitLine, 	fitPts[0, 0], fitPts[0, 1], 
												fitPts[1, 0], fitPts[1, 1])
		
		if self.data:
			dataRanges = analysis.data_range(self.data, self.headers)
			dataRanges = [self.manualDataRanges[header] 
						if header in self.manualDataRanges else dataRanges[i] 
						for i, header in enumerate(self.headers)]
		for i in range(3):
			if self.data and len(self.headers) == 5 and i == 2:
				zstate = tk.HIDDEN
			else:
				zstate = tk.NORMAL
			self.canvas.coords(self.axes[i], 
							axesPts[2*i, 0], axesPts[2*i, 1], 
							axesPts[2*i+1, 0], axesPts[2*i+1, 1])
			self.canvas.coords(self.axesLabels[i], 
							axesLabelsPts[i, 0], axesLabelsPts[i, 1])
			axesLabel = labelVars[i].get()
			self.canvas.itemconfigure(self.axesLabels[i], text=axesLabel)
			if self.data: dataMin, dataMax = dataRanges[i]
			for j in range(self.numTicks):
				curTick = self.ticksMarks[self.numTicks*i + j]
				curLabel = self.ticksLabels[self.numTicks*i + j]
				if not self.enableTicks.get() or zstate==tk.HIDDEN: 
					tickstate=tk.HIDDEN
					tickVal = ""
				else:
					tickstate=tk.NORMAL
					self.canvas.coords(curTick, 
									ticksMarksPts[self.numTicks*2*i + 2*j, 0], 
									ticksMarksPts[self.numTicks*2*i + 2*j, 1], 
									ticksMarksPts[self.numTicks*2*i + 2*j+1, 0], 
									ticksMarksPts[self.numTicks*2*i + 2*j+1, 1])
					self.canvas.coords(curLabel, 
									ticksLabelsPts[self.numTicks*i + j, 0], 
									ticksLabelsPts[self.numTicks*i + j, 1])
					if self.data:
						tickVal = dataMin + j*(dataMax-dataMin)/(self.numTicks-1.0)
						tickVal = "%.1f" % tickVal
					else:
						tickVal = ""
				self.canvas.itemconfig( curTick, state=tickstate )
				self.canvas.itemconfig( curLabel, text=tickVal )
		self.canvas.itemconfig(self.axes[2], state=zstate)
		self.canvas.itemconfig(self.axesLabels[2], state=zstate)
			
	def updateNumObjStrVar(self):
		'''
		update the status bar to reflect the current number of objects
		'''
		#if self.verbose: print("updating the number of objects status")
		self.numObjStrVar.set("%d" % len(self.objects))
	
	def updatePresets(self, *args):
		'''
		update the control for the presets to have current options
		'''
		presets = self.getPresets()
		self.presetView.set(presets[0])
		self.presetControl.destroy()
		#if len(presets) > 1: # can disable preset option if 2D
		self.presetControl = tk.OptionMenu( self.rightcntlframe, self.presetView, 
									*presets, command=self.resetViewOrientation)
		self.presetControl.grid( row=self.presetControlRow, columnspan=3 )

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
