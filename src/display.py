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
from dialog import AboutAppDialog, AboutBruceDialog, AboutMeDialog, \
    AboutStephDialog, BindingsDialog, ColorMakerDialog, DistributionDialog
from optparse import OptionParser
from collections import OrderedDict
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

    def __init__(self, width, height, filename="", verbose=True):
        '''
        Constructor for the display application
        '''
        # make initial fields
        self.verbose = verbose
        self.filename = filename
        self.data = None
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

        # setup the menus
        self.buildMenus()

        # build the controls
        self.buildControlsFrame()

        # build the status bar
        self.buildStatusFrame()

        # build the Canvas
        self.buildCanvas(width, height)

        # bring the window to the front
        self.root.lift()

        # - do idle events here to get actual canvas size
        self.root.update_idletasks()

        # set up the key bindings
        self.setBindings()
        
        # build the axes
        self.buildAxes()
        
        # build the data
        self.buildData()

    def buildAxes(self, axes=[[0,0,0],[1,0,0],
                              [0,0,0],[0,1,0],
                              [0,0,0],[0,0,1]],
                  axeslabels=[[0,0,0],[1.05,0,0],
                              [0,0,0],[0,1.05,0],
                              [0,0,0],[0,0,1.05]]):
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
        self.view = View()
        self.updateScreen()
        self.baseView = self.view.clone()
        VTM = self.view.build()
        self.axes = np.asmatrix(axes)
        self.axesLabels = np.asmatrix(axeslabels)
        axesPts = (VTM * self.axes.T).T
        labelPts = (VTM * self.axesLabels.T).T
        labels = ["x", "y", "z"]
        self.lines = [self.canvas.create_line(axesPts[2*i, 0], axesPts[2*i, 1], 
                                              axesPts[2*i+1, 0], axesPts[2*i+1, 1]) 
                      for i in range(3)]
        self.labels = [self.canvas.create_text(labelPts[2*i+1, 0], labelPts[2*i+1, 1], 
                                               font=("Purina", 20), text=labels[i])
                      for i in range(3)]
                    
    def buildCanvas(self, width, height):
        '''
        build the canvas where objects will be drawn
        '''
        if self.verbose: print("building the canvas")
        self.canvas = tk.Canvas( self.root, width=width, height=height )
        self.canvas.pack( expand=tk.YES, fill=tk.BOTH )

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
                  ).grid( row=row, column=1, pady=10 )
        row+=1

        # make an open button in the frame
        tk.Button( self.rightcntlframe, text="Open", 
                   command=self.openData, width=10
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
                       "xy", "xz", "yz"
                       ).grid( row=row, column=1 )
        row+=1

        # make a reset button in the frame
        tk.Button( self.rightcntlframe, text="Preset", 
                   command=self.viewPreset, width=10
                   ).grid( row=row, column=1 )
        row+=1

        # shape selector
        tk.Label( self.rightcntlframe, text="\nShape Select"
                       ).grid( row=row, column=1 )
        row+=1
        
        self.shapeOption = tk.StringVar( self.root )
        self.shapeOption.set("oval")
        tk.OptionMenu( self.rightcntlframe, self.shapeOption, 
                       "oval", "rectangle", 
                       "up triangle", "down triangle",
                       "x", "star",
                       command=self.update
                       ).grid( row=row, column=1 )
        row+=1
        
        # use a label to set the size of the right panel
        tk.Label( self.rightcntlframe, text="Control"
                  ).grid( row=row, column=1, pady=10 )
        row+=1

        # make a button for selecting predefined colors
        self.colorRow = row
        self.colorOption = tk.StringVar( self.root )
        self.colorOption.set("Select Color")
        self.colorMenu = tk.OptionMenu( self.rightcntlframe, self.colorOption, 
                       *self.colors.keys()).grid( row=row, column=1 )
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
        '''
        
        # if the data is not set, set according to filename
        if not self.data:
            
            # leave data unset if no filename
            if not self.filename:
                return
            
            # otherwise set data instance and read active data columns
            else:
                self.data = Data(self.filename, self.verbose)
                headers = self.data.get_headers()
                if len(headers) < 2:
                    print("not enough columns of numeric data to plot")
                    self.filename = None
                    self.data = None
                    return
                elif len(headers) < 3:
                    print("only 2 columns of numeric data, setting z to 0")
                    headers = headers[:2]
                else:
                    headers = headers[:3]
                self.activeData = analysis.normalize_columns_separately(
                                                        self.data, headers)
                [rows, cols] = self.activeData.shape
                if(cols == 2): # pad missing z data
                    self.activeData = np.column_stack((self.activeData, 
                                                       [0]*rows, [1]*rows))
                else: # pad the homogeneous coordinate
                    self.activeData = np.column_stack((self.activeData, 
                                                       [1]*rows))
        
        # prepare to transform the active data to the current view
        VTM = self.view.build()
        viewData = self.activeData.copy()
        rows = viewData.shape[0]
        
        # save original z values for coloring
        zValues = viewData[:, 2].T.tolist()[0]
        
        # transform into view
        viewData = (VTM * viewData.T).T

        # order so that closer objects draw last
        zIndicesSorted = np.argsort(viewData[:, 2].T.tolist()[0])
        
        # transform sorted data to view and draw on canvas
        dx = 6.0 #/self.view.extent[0,0] # size of data points
        dy = 6.0 #/self.view.extent[0,1]
        for i in zIndicesSorted:
            self.drawObject(viewData[i,0], viewData[i,1], zValues[i], dx, dy)

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
                         ['Quit     Ctrl-Q', self.handleQuit]
                         ]])

        # create another menu for color
        colormenu = tk.Menu( self.menu )
        self.menu.add_cascade( label = "Color", menu = colormenu )
        menulist.append([colormenu,
                        [['Random Color', self.getRandomColor],
                         ['Create Color', self.getUserColor],
                         ['Update Color', self.updateColor]
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

        # display the current distributions
        tk.Label(bottomstatusframe, textvariable=self.numObjStrVar
                 ).grid(row=1, column=cols)
        cols+=1
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
        self.filename = ""
        self.data = None
        self.updateNumObjStrVar()
        self.xLocation.set("")
        self.yLocation.set("")

    def getUserColor(self, event=None):
        '''
        define a new color for the color selector control
        '''
        if self.verbose: print("creating a new color")
        #d = ColorMakerDialog(self.root, title="Create New Color")
        result = askcolor()
        if result[0]:
            (rb, gb, bb) = result[0]
            self.redBand.set(str(rb))
            self.greenBand.set(str(gb))
            self.blueBand.set(str(bb))
            return result[1]
        return None
    
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
        self.data = True
        self.activeData  = np.matrix([[randFuncX(*randArgsX), 
                                       randFuncY(*randArgsY),
                                       randFuncZ(*randArgsZ), 1]
                                      for _ in range(points)])
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
        AboutAppDialog(self.root, title="About Application")

    def displayAboutMe(self, event=None):
        '''
        display the author about dialog
        '''
        AboutMeDialog(self.root, title="About Me")

    def displayAboutSteph(self, event=None):
        '''
        display the Stephanie about dialog
        '''
        AboutStephDialog(self.root, title="About Stephanie Taylor")

    def displayAboutBruce(self, event=None):
        '''
        display the Bruce about dialog
        '''
        AboutBruceDialog(self.root, title="About Bruce Maxwell")

    def displayBindings(self, event=None):
        '''
        display the Key Bindings about dialog
        '''
        BindingsDialog(self.root, title="Key Bindings")
    
    def drawObject(self, x, y, z, dx=6, dy=6):
        '''
        add the control selected shape to the canvas at x, y with size dx, dy
        '''
        [shapeFunc, coords] = self.getShapeFunction(self.shapeOption.get(), 
                                                    x, y, dx, dy)
        if shapeFunc:
            shape = shapeFunc(coords, fill=self.getColorByDepth(z), outline='')
            self.objects.append(shape)
            self.updateNumObjStrVar()
        else:
            if self.verbose: print("No shape function for %s" % 
                                   self.shapeOption.get())
        
    def getColorByDepth(self, z):
        '''
        color according the given normalized z
        '''
        z = max(min(z, 1.0), 0.0)
        
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
        shapeFunctions = {"RECTANGLE":[self.canvas.create_rectangle, 
                                [x-dx, y-dy, 
                                 x+dx, y+dy]],
                          "OVAL":[self.canvas.create_oval,
                                [x-dx, y-dy, 
                                 x+dx, y+dy]],
                          "DOWN TRIANGLE":[self.canvas.create_polygon,
                                [x-dx, y-dy, 
                                 x+dx, y-dy, 
                                 x, y+dy]],
                          "UP TRIANGLE":[self.canvas.create_polygon,
                                [x-dx, y+dy, 
                                 x+dx, y+dy, 
                                 x, y-dy]],
                          "X":[self.canvas.create_polygon,
                                [x-dx, y+dy, 
                                 x, y+dy/2.0,
                                 x+dx, y+dy, 
                                 x+dx/2.0, y, 
                                 x+dx, y-dy, 
                                 x, y-dy/2.0, 
                                 x-dx, y-dy, 
                                 x-dx/2.0, y]],
                          "STAR":[self.canvas.create_polygon,
                                [x-dx, y+dy, 
                                 x, y+dy/2.0,
                                 x+dx, y+dy, 
                                 x+dx/2.0, y, 
                                 x+dx, y-dy/2.0, 
                                 x+dx/3.0, y-dy/2.0,
                                 x, y-dy, 
                                 x-dx/3.0, y-dy/2.0,
                                 x-dx, y-dy/2.0, 
                                 x-dx/2.0, y]]
                          }
        if shape.upper() in shapeFunctions:
            return shapeFunctions[shape.upper()]
        else:
            return [None,None]
            
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
        move the objects selected by the click
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
        scale the objects selected by the click
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
        self.filename = tkf.askopenfilename()
        if self.filename:
            self.data = None
            self.updateData()

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
    
    def setDistribution(self, event=None):
        '''
        select the distribution using the dialog and update status
        '''
        if self.verbose: print("setting a new distribution")
        [xDistribution, yDistribution, zDistribution] = \
            DistributionDialog(self.root, 
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
        self.updateScreen()
        self.updateAxes()
        self.updateData()

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
            self.canvas.coords(self.labels[i], labelPts[2*i+1, 0], labelPts[2*i+1, 1])
        
    def updateData(self):
        '''
        redraw the active data with the current vtm
        ''' 
        for obj in self.objects:
            self.canvas.delete(obj)
        self.objects = []
        self.buildData()
        
    def updateColor(self, event=None):
        '''
        update all the objects on the canvas to the current color
        '''
        if self.verbose: print("updating color of canvas objects")
        for obj in self.objects:
            self.canvas.itemconfig(obj, fill=self.getCurrentColor())

    def updateNumObjStrVar(self):
        '''
        update the status bar to reflect the current number of objects
        '''
        if self.verbose: print("updating the number of objects status")
        self.numObjStrVar.set("%d" % len(self.objects))

    def updateScreen(self):
        '''
        updates the view to the current screen dimensions
        '''
        self.view.offset[0, 0] = self.canvas.winfo_width()*0.1
        self.view.offset[0, 1] = self.canvas.winfo_height()*0.1
        self.view.screen[0, 0] = self.canvas.winfo_width()*0.8
        self.view.screen[0, 1] = self.canvas.winfo_height()*0.8
        
    def viewPreset(self):
        '''
        set the view to the specified preset
        '''
        presetStr = self.presetView.get().upper()
        self.view.reset() # return to xy plane view
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