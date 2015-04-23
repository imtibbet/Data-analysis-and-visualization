#dialog
header='''
Ian Tibbetts
Colby College CS251 Spring '15
Professors Stephanie Taylor and Bruce Maxwell
'''
from photos import photos, descriptions
import analysis
from datetime import datetime
import numpy as np
import matplotlib
import tkFont
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#try:
#	import tkinter as tk # python 3
#except ImportError:
import Tkinter as tk # python 2
import tkMessageBox as tkm

# abstract super classes

class OkCancelDialog(tk.Toplevel):

	def __init__(self, parent, title = None):

		tk.Toplevel.__init__(self, parent)
		self.transient(parent)
		
		if title:
			self.title(title)

		self.parent = parent

		self.result = None

		body = tk.Frame(self)
		self.initial_focus = self.body(body)
		body.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

		self.buttonbox()
		
		try:
			self.grab_set()
		except:
			self.destroy()
			return
		if not self.initial_focus:
			self.initial_focus = self

		self.protocol("WM_DELETE_WINDOW", self.cancel)

		self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
								  parent.winfo_rooty()+50))

		self.initial_focus.focus_set()

		self.wait_window(self)

	#
	# construction hooks

	def body(self, master):
		# create dialog body.  return widget that should have
		# initial focus.  this method should be overridden

		pass

	def buttonbox(self):
		# add standard button box. override if you don't want the
		# standard buttons

		box = tk.Frame(self)

		w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
		w.pack(side=tk.LEFT, padx=5, pady=5)
		w = tk.Button(box, text="Cancel", width=10, command=self.cancel)
		w.pack(side=tk.LEFT, padx=5, pady=5)

		self.bind("<Return>", self.ok)
		self.bind("<Escape>", self.cancel)

		box.pack()

	#
	# standard button semantics

	def ok(self, event=None):

		if not self.validate():
			self.initial_focus.focus_set() # put focus back
			return

		self.withdraw()
		self.update_idletasks()

		self.apply()

		self.cancel()

	def cancel(self, event=None):

		# put focus back to the parent window
		self.parent.focus_set()
		self.destroy()

	#
	# command hooks

	def validate(self):

		return 1 # override

	def apply(self):

		pass # override

class OkDialog(OkCancelDialog):

	def buttonbox(self):
		box = tk.Frame(self)

		tk.Button(box, text="OK", width=10, command=self.ok, 
				  default=tk.ACTIVE).pack()

		self.bind("<Return>", self.ok)
		self.bind("<Escape>", self.cancel)

		box.pack()

# implementing classes

class AboutAppDialog(OkDialog):
	def body(self, master):
		title = "Welcome to DAPPER"
		desc = "Data Analysis and Plotting for Presenting and Evaluating Results"
		tk.Label(master, text="\n".join([title, desc])).pack(side=tk.TOP)
		photoIan = tk.PhotoImage(data=photos["ian"])
		label = tk.Label(master, image=photoIan)
		label.image = photoIan
		label.pack(side=tk.TOP)
		tk.Label(master, text=header).pack(side=tk.TOP)

class AboutMeDialog(OkDialog):
	def body(self, master):
		photoIan = tk.PhotoImage(data=photos["ian"])
		label = tk.Label(master, image=photoIan)
		label.image = photoIan
		label.pack(side=tk.TOP)
		tk.Label(master, text=descriptions["ian"], wraplength=500
				 ).pack(side=tk.TOP)

class AboutStephDialog(OkDialog):
	def body(self, master):
		photoSte = tk.PhotoImage(data=photos["stephanie"])
		label = tk.Label(master, image=photoSte)
		label.image = photoSte
		label.pack(side=tk.TOP)
		tk.Label(master, text=descriptions["stephanie"], wraplength=500, 
				 anchor=tk.W, justify=tk.LEFT).pack(side=tk.TOP)
		
class AboutBruceDialog(OkDialog):
	def body(self, master):
		photoBru = tk.PhotoImage(data=photos["bruce"])
		label = tk.Label(master, image=photoBru)
		label.image = photoBru
		label.pack(side=tk.TOP)
		tk.Label(master, text=descriptions["bruce"], wraplength=500, 
				 anchor=tk.W, justify=tk.LEFT).pack(side=tk.TOP)

class BindingsDialog(OkDialog):
	def body(self, master):
		keyBindingDescriptions = [
			["B1-Motion", "pan the axes in the canvas"],
			["B2-Motion", "zoom in on the axes in the canvas"],
			["B3-Motion", "rotate the axes in the canvas"],
			["Ctrl-B1-Motion", "same as B2-Motion"],
			["Ctrl-Shift-B1", "delete the clicked object from the canvas"],
			["Ctrl-D", "change the delimiter for reading data files"],
			["Ctrl-F", "filter the data"],
			["Ctrl-N", "clear the canvas"],
			["Ctrl-O", "open a new data file"],
			["Ctrl-F", "plot the selected opened data file"],
			["Ctrl-Q OR Esc", "quit the application"],
			["Ctrl-S", "save the displayed data"],
			["Double-B1", "show the raw data for the clicked object"]
								  ]
		for [row, [k, bd]] in enumerate(keyBindingDescriptions):
			tk.Label(master, text=k, relief=tk.GROOVE, width=20
					 ).grid(row=row, column=0)
			tk.Label(master, text=bd).grid(row=row, column=1)
			
class ClassifyDialog(OkCancelDialog):

	def __init__(self, parent, data, filename2data, title = None):
		
		self.headers = [h.upper() for h in data.get_headers()]
		if len(self.headers) < 2:
			self.result = None
			return
		self.data = data
		self.filename2data = filename2data
		OkCancelDialog.__init__(self, parent, title)
		
	def body(self, master):
		
		tk.Label(master, text="Select Classifying Headers:").pack(side=tk.TOP)
		self.e1 = tk.Listbox(master, selectmode=tk.EXTENDED, exportselection=0)
		for header in self.headers:
			self.e1.insert(tk.END, header.capitalize())
		self.e1.select_set(0)
		self.e1.pack(side=tk.TOP)
		
		tk.Button(master, text="Select All", width=10,
				command=lambda: self.e1.select_set(0, tk.END)).pack(side=tk.TOP)
		tk.Button(master, text="Select One", width=10,
				command=lambda: self.e1.select_clear(1, tk.END)).pack(side=tk.TOP)
				
		tk.Label(master, text="(Optional) Select Category Header:").pack(side=tk.TOP)
		self.e2 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		self.e2.insert(tk.END, "None")
		for header in self.headers:
			self.e2.insert(tk.END, header.capitalize())
		self.e2.select_set(0)
		self.e2.pack(side=tk.TOP)
		
		tk.Label(master, text="(Optional) Choose the test data object").pack(side=tk.TOP)
		self.e3 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		self.e3.insert(tk.END, "None")
		for openDataName in self.filename2data:
			self.e3.insert(tk.END, openDataName)
		self.e3.select_set(0)
		self.e3.pack(side=tk.TOP)

		self.kbool = tk.BooleanVar()
		tk.Checkbutton(master, text = "KNN Classify?", variable=self.kbool
					).pack(side=tk.TOP)
		tk.Label(master, text="K value, optional for KNN")
		self.k = tk.StringVar()
		self.k.set("")
		tk.Entry(master, textvariable=self.k).pack(side=tk.TOP)
		
		return None # initial focus

	def apply(self):
		self.result = [self.e1.get(sel) for sel in self.e1.curselection()]
		self.result = [h.upper() for h in self.result]
		catName = self.e2.get(self.e2.curselection()).upper()
		fname = self.e3.get(self.e3.curselection())
		dtest = self.filename2data[fname] if fname != "None" else None
		self.result = [dtest, catName, self.result, self.kbool.get(), self.k.get()]
			
class ColorMakerDialog(OkCancelDialog):
		
	def body(self, master):
		
		tk.Label(master, text="Name:").grid(row=0)
		self.name = tk.StringVar()
		self.name.set("new color")
		e0 = tk.Entry(master, textvariable=self.name)
		e0.grid(row=0, column=1)
		e0.select_to(tk.END)

		tk.Label(master, text="Red:").grid(row=1)
		self.e1 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for i in range(256):
			self.e1.insert(tk.END, i) 
		self.e1.select_set(0)
		self.e1.grid(row=1, column=1)
		
		tk.Label(master, text="Green:").grid(row=2)
		self.e2 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for i in range(256):
			self.e2.insert(tk.END, i)		  
		self.e2.select_set(0)
		self.e2.grid(row=2, column=1)
		
		tk.Label(master, text="Blue:").grid(row=3)
		self.e3 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for i in range(256):
			self.e3.insert(tk.END, i)		  
		self.e3.select_set(0)
		self.e3.grid(row=3, column=1)
		
		return e0 # initial focus

	def apply(self):
		red = self.e1.get(self.e1.curselection())
		green = self.e2.get(self.e2.curselection())
		blue = self.e3.get(self.e3.curselection())
		self.result = [self.name.get(), red, green, blue]
		
class DistributionDialog(OkCancelDialog):

	def __init__(self, parent, 
				 curxDistribution, curyDistribution, curzDistribution, 
				 distributions, title = None):

		self.curxDistribution = curxDistribution.upper()
		self.curyDistribution = curyDistribution.upper()
		self.curzDistribution = curzDistribution.upper()
		self.distributions = distributions
		OkCancelDialog.__init__(self, parent, title)
		
		if not self.result:
			self.result = [self.curxDistribution, 
						   self.curxDistribution, 
						   self.curzDistribution]
		
	def body(self, master):
		
		tk.Label(master, text="X Distribution:").grid(row=0)
		self.e1 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for distribution in self.distributions:
			self.e1.insert(tk.END, distribution.capitalize())
		self.e1.select_set(self.distributions.index(self.curxDistribution))
		self.e1.grid(row=0, column=1)
		
		tk.Label(master, text="Y Distribution:").grid(row=1)
		self.e2 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for distribution in self.distributions:
			self.e2.insert(tk.END, distribution.capitalize())		 
		self.e2.select_set(self.distributions.index(self.curyDistribution)) 
		self.e2.grid(row=1, column=1)
		
		tk.Label(master, text="Z Distribution:").grid(row=2)
		self.e3 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for distribution in self.distributions:
			self.e3.insert(tk.END, distribution.capitalize())		 
		self.e3.select_set(self.distributions.index(self.curzDistribution)) 
		self.e3.grid(row=2, column=1)
		
		return self.e1 # initial focus

	def apply(self):
		x = self.e1.get(self.e1.curselection())
		y = self.e2.get(self.e2.curselection())
		z = self.e3.get(self.e3.curselection())
		self.result = [x.upper(), y.upper(), z.upper()]
		
		
class FilterDataDialog(OkCancelDialog):

	def __init__(self, parent, data, title = None):
		
		self.data = data
		OkCancelDialog.__init__(self, parent, title)
		
	def body(self, master):
		dataRanges = analysis.data_range(self.data, self.data.get_headers())
		self.mins = []
		self.maxs = []
		tk.Label(master, text="header", width=20).grid(row=0, column=0)
		tk.Label(master, text="type", width=20).grid(row=0, column=1)
		tk.Label(master, text="curMin", width=20).grid(row=0, column=2)
		tk.Label(master, text="curMax", width=20).grid(row=0, column=4)
		tk.Label(master, text="newMin", width=20).grid(row=0, column=5)
		tk.Label(master, text="newMax", width=20).grid(row=0, column=7)
		for row, header in enumerate(self.data.get_headers(), start=1):
			curMin, curMax = dataRanges[row-1]
			raw_type = self.data.raw_types[self.data.header2raw[header]]
			tk.Label(master, text=header, relief=tk.GROOVE, width=20
					 ).grid(row=row, column=0)
			typeDesc = raw_type.capitalize()
			if raw_type == "ENUM":
				for [key, val] in self.data.enum2value[header].items():
					typeDesc += "\n%d->%s" % (val, key)
			elif raw_type == "DATE":
				typeDesc += "\n%d->%s" % (int(curMin), datetime.fromordinal(int(curMin)).strftime("%Y-%m-%d"))
				typeDesc += "\n%d->%s" % (int(curMax), datetime.fromordinal(int(curMax)).strftime("%Y-%m-%d"))
			tk.Label(master, text=typeDesc, relief=tk.GROOVE, width=20
					 ).grid(row=row, column=1)
			tk.Label(master, text="%.2f" % curMin, relief=tk.GROOVE, width=20
					 ).grid(row=row, column=2)
			tk.Label(master, text="->").grid(row=row, column=3)
			tk.Label(master, text="%.2f" % curMax, relief=tk.GROOVE, width=20
					 ).grid(row=row, column=4)
			
			self.mins.append(tk.StringVar())
			self.mins[-1].set(curMin)
			tk.Entry(master, textvariable=self.mins[-1]).grid(row=row, column=5)
			tk.Label(master, text="->").grid(row=row, column=6)
			self.maxs.append(tk.StringVar())
			self.maxs[-1].set(curMax)
			tk.Entry(master, textvariable=self.maxs[-1]).grid(row=row, column=7)
			
	def apply(self):
		try:
			self.result = []
			newMins = [float(newMin.get()) for newMin in self.mins]
			newMaxs = [float(newMax.get()) for newMax in self.maxs]
		except:
			self.result = None
			self.cancel()

		for i in range(len(newMins)): 
			if newMins[i] > newMaxs[i]: # verify that min is less than max
				self.result = None
				break
			else:
				self.result.append([newMins[i], newMaxs[i]])


class GetAtBatID(OkCancelDialog):
	"""
	User select at bat to look at
	"""
	def __init__(self, parent, data, title = None):
		
		self.data = data
		OkCancelDialog.__init__(self, parent, title)
		
	def body(self, master):
	
		fixedfont = tkFont.Font(family="TkCaptionFont")
		self.dict = {}
		A = self.data.get_raw_data(self.data.get_raw_headers())
		
		ab_id_index = self.data.header2raw["AB_ID"]
		pitcher_index = self.data.header2raw["PITCHER"]
		batter_index = self.data.header2raw["BATTER"]
		event_index = self.data.header2raw["EVENT"]

	
	
		tk.Label(master, text="Select At-Bat ID:").pack(side=tk.TOP)
		tk.Label(master, text=("%-35s"%"Pitcher") + ("%-35s"%"Hitter") +  ("%-35s"%"Event") + ("%-35s"%"ID")).pack(side=tk.TOP)

		self.e1 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0, width = 70, font = fixedfont)
		#Get At Bat IDS
		

		
		for row in A:
			string = (("%-30s"%row[0, pitcher_index][:28]) + ("%-30s"%row[0, batter_index][:28]) + ("%-30s"%row[0, event_index][:28])+("%-30s"%row[0, ab_id_index][:28]))
			self.dict[string] = float(row[0 , ab_id_index])	
		
		
		#atbatids = np.unique(np.squeeze(np.asarray(self.data.get_data(["AB_ID"]))))
		
		
		for key in self.dict:
			self.e1.insert(tk.END, key)
		self.e1.select_set(0)
		self.e1.pack(side=tk.TOP)
		
		
		
		#Ask for number of frames
		tk.Label(master, text="Frames").pack(side = tk.TOP)
		self.k = tk.StringVar()
		self.k.set("20")
		tk.Entry(master, textvariable=self.k).pack(side=tk.TOP)
		
		return None # initial focus
	
	def apply(self):
		self.result = [self.dict[self.e1.get(self.e1.curselection())], self.k.get()]
	
	

			
class MatPlotLibDialog(OkDialog):
	
	def __init__(self, parent, figure, title=None):
		self.figure = figure
		OkDialog.__init__(self, parent, title)
	
	def body(self, master):
		canvas = FigureCanvasTkAgg(self.figure, master=master)
		canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
			
class MultiLinearRegression(OkCancelDialog):

	def __init__(self, parent, data, title = None):
		
		self.headers = [h.upper() for h in data.get_headers()]
		if len(self.headers) < 2:
			self.result = None
			return
		OkCancelDialog.__init__(self, parent, title)
		
	def body(self, master):
			
		row=0
		col=0
		tk.Label(master, text="Independent:").grid(row=row, column=col)
		self.e1 = tk.Listbox(master, selectmode=tk.EXTENDED, exportselection=0)
		for header in self.headers:
			self.e1.insert(tk.END, header.capitalize())
		self.e1.select_set(0)
		self.e1.grid(row=row+1, column=col)
		
		col+=1
		tk.Label(master, text="Dependent:").grid(row=row, column=col)
		self.e2 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e2.insert(tk.END, header.capitalize())	
		self.e2.select_set(1)
		self.e2.grid(row=row+1, column=col)
		
		return None # initial focus

	def apply(self):
		self.result = [self.e1.get(sel) for sel in self.e1.curselection()]
		self.result.append(self.e2.get(self.e2.curselection()))
		self.result = [h.upper() for h in self.result]
		
class PickAxesDialog(OkCancelDialog):

	def __init__(self, parent, data, oldHeaders, title = None):
		
		self.oldHeaders = oldHeaders
		print(oldHeaders)
		self.headers = [h.upper() for h in data.get_headers()]
		OkCancelDialog.__init__(self, parent, title)
		
	def body(self, master):
			
		row=0
		col=0
		tk.Label(master, text="X Axes:").grid(row=row, column=col)
		self.e1 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e1.insert(tk.END, header.capitalize())
		if self.oldHeaders:
			self.e1.select_set(self.headers.index(self.oldHeaders[0]))
		else:
			self.e1.select_set(0)
		self.e1.grid(row=row+1, column=col)
		
		col+=1
		tk.Label(master, text="Y Axes:").grid(row=row, column=col)
		self.e2 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e2.insert(tk.END, header.capitalize())	
		if self.oldHeaders:
			self.e2.select_set(self.headers.index(self.oldHeaders[1]))
		else:
			self.e2.select_set(1)
		self.e2.grid(row=row+1, column=col)
		
		col+=1
		tk.Label(master, text="Z Axes:").grid(row=row, column=col)
		self.e3 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		self.e3.insert(tk.END, "NONE")
		for header in self.headers:
			self.e3.insert(tk.END, header.capitalize())
		if self.oldHeaders:
			if len(self.oldHeaders) < 6:
				self.e3.select_set(0)
			else:
				self.e3.select_set(self.headers.index(self.oldHeaders[2])+1)
		else:
			if len(self.headers) > 2:
				self.e3.select_set(3)
			else:
				self.e3.select_set(0)
		self.e3.grid(row=row+1, column=col)
	
		row=2
		col=0
		tk.Label(master, text="Size:").grid(row=row, column=col)
		self.e4 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e4.insert(tk.END, header.capitalize())
		if self.oldHeaders:
			self.e4.select_set(self.headers.index(self.oldHeaders[-3]))
		else:
			self.e4.select_set(0)
		self.e4.grid(row=row+1, column=col)
		
		col+=1
		tk.Label(master, text="Color:").grid(row=row, column=col)
		self.e5 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e5.insert(tk.END, header.capitalize())
		if self.oldHeaders:
			self.e5.select_set(self.headers.index(self.oldHeaders[-2]))
		else:
			self.e5.select_set(0)
		self.e5.grid(row=row+1, column=col)
		
		col+=1
		tk.Label(master, text="Shape:").grid(row=row, column=col)
		self.e6 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e6.insert(tk.END, header.capitalize())	
		if self.oldHeaders:
			self.e6.select_set(self.headers.index(self.oldHeaders[-1]))
		else:
			self.e6.select_set(0)
		self.e6.grid(row=row+1, column=col)
		
		return None # initial focus

	def apply(self):
		x = self.e1.get(self.e1.curselection())
		y = self.e2.get(self.e2.curselection())
		z = self.e3.get(self.e3.curselection())
		size = self.e4.get(self.e4.curselection())
		color = self.e5.get(self.e5.curselection())
		shape = self.e6.get(self.e6.curselection())
		if z == "NONE":
			self.result = [x, y, size, color, shape]
		else:
			self.result = [x, y, z, size, color, shape]
		self.result = [h.upper() for h in self.result]
		
class SetDataRanges(OkCancelDialog):

	def __init__(self, parent, data, manualDataRanges, headers, title = None):		
		self.data = data
		self.manualDataRanges = manualDataRanges
		self.headers = [h.upper() for h in headers]
		OkCancelDialog.__init__(self, parent, title)
		
	def body(self, master):
		dataRanges = analysis.data_range(self.data, self.headers)
		dataRanges = [self.manualDataRanges[header] 
					if header in self.manualDataRanges else dataRanges[i] 
					for i, header in enumerate(self.headers)]
		self.mins = []
		self.maxs = []
		tk.Label(master, text="min", width=20).grid(row=0, column=1)
		tk.Label(master, text="max", width=20).grid(row=0, column=2)
		for row, header in enumerate(self.headers, start=1):
			curMin, curMax = dataRanges[row-1]
			tk.Label(master, text=header, relief=tk.GROOVE, width=20
					 ).grid(row=row, column=0)
			self.mins.append(tk.StringVar())
			self.mins[-1].set(curMin)
			tk.Entry(master, textvariable=self.mins[-1]).grid(row=row, column=1)
			self.maxs.append(tk.StringVar())
			self.maxs[-1].set(curMax)
			tk.Entry(master, textvariable=self.maxs[-1]).grid(row=row, column=2)
			
	def apply(self):
		try:
			self.result = []
			newMins = [float(newMin.get()) for newMin in self.mins]
			newMaxs = [float(newMax.get()) for newMax in self.maxs]
		except:
			self.result = None
			self.cancel()

		for i in range(len(newMins)): 
			if newMins[i] > newMaxs[i]: # verify that min is less than max
				self.result = None
				break
			else:
				self.result.append([newMins[i], newMaxs[i]])
			
class RunKmeans(OkCancelDialog):

	def __init__(self, parent, data, title = None):
		
		self.headers = [h.upper() for h in data.get_headers()]
		if len(self.headers) < 2:
			self.result = None
			return
		self.data = data
		OkCancelDialog.__init__(self, parent, title)
		
	def body(self, master):
			
		self.name = tk.StringVar()
		self.name.set("")
		tk.Entry(master, textvariable=self.name).pack(side=tk.TOP)
		
		tk.Label(master, text="Select Clumping Headers:").pack(side=tk.TOP)
		self.e1 = tk.Listbox(master, selectmode=tk.EXTENDED, exportselection=0)
		for header in self.headers:
			self.e1.insert(tk.END, header.capitalize())
		self.e1.select_set(0)
		self.e1.pack(side=tk.TOP)
		
		tk.Button(master, text="Select All", width=10,
				command=lambda: self.e1.select_set(0, tk.END)).pack(side=tk.TOP)
		tk.Button(master, text="Select One", width=10,
				command=lambda: self.e1.select_clear(1, tk.END)).pack(side=tk.TOP)
				
		tk.Label(master, text="Select Category Header (optional):").pack(side=tk.TOP)
		self.e2 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		self.e2.insert(tk.END, "None")
		for header in self.headers:
			self.e2.insert(tk.END, header.capitalize())
		self.e2.select_set(0)
		self.e2.pack(side=tk.TOP)
		
		tk.Label(master, text="K value, if no category selected")
		self.k = tk.StringVar()
		self.k.set("2")
		tk.Entry(master, textvariable=self.k).pack(side=tk.TOP)
		
		return None # initial focus

	def apply(self):
		self.result = [self.e1.get(sel) for sel in self.e1.curselection()]
		self.result = [h.upper() for h in self.result]
		catName = self.e2.get(self.e2.curselection()).upper()
		strK = self.k.get()
		if catName == "NONE" and not strK.isdigit():
			tkm.showerror("K Error", "k is not a digit, cancelling")
			self.result = None
		else:
			if catName == "NONE":
				cat = []
				k = int(strK)			
			else:
				cat = np.squeeze(np.asarray(self.data.get_data([catName])))
				k = len(np.unique(cat))
			tkm.showinfo("K value", "K = %d" % k)
			self.result = [self.name.get(), k, self.result, cat]
			
class RunPCA(OkCancelDialog):

	def __init__(self, parent, data, title = None):
		
		self.headers = [h.upper() for h in data.get_headers()]
		if len(self.headers) < 2:
			self.result = None
			return
		OkCancelDialog.__init__(self, parent, title)
		
	def body(self, master):
			
		self.name = tk.StringVar()
		self.name.set("")
		tk.Entry(master, textvariable=self.name).pack(side=tk.TOP)
		
		tk.Label(master, text="Select Headers:").pack(side=tk.TOP)
		self.e1 = tk.Listbox(master, selectmode=tk.EXTENDED, exportselection=0)
		for header in self.headers:
			self.e1.insert(tk.END, header.capitalize())
		self.e1.select_set(0)
		self.e1.pack(side=tk.TOP)
		
		tk.Button(master, text="Select All", width=10,
				command=lambda: self.e1.select_set(0, tk.END)).pack(side=tk.TOP)
		tk.Button(master, text="Select One", width=10,
				command=lambda: self.e1.select_clear(1, tk.END)).pack(side=tk.TOP)
				
		self.normalize = tk.BooleanVar()
		tk.Checkbutton(master, text="Normalize", variable=self.normalize
					).pack(side=tk.TOP)
		
		return None # initial focus

	def apply(self):
		self.result = [self.e1.get(sel) for sel in self.e1.curselection()]
		self.result = [h.upper() for h in self.result]
		self.result = [self.name.get(), self.normalize.get(), self.result]
			
class ShowPCA(OkDialog):

	def __init__(self, parent, data, title = None):
		
		self.data = data
		try: # verify that the data is a PCAData instance
			self.data.means
		except:
			print("Not PCA data, cancelling")
			self.result = None
			return
		OkDialog.__init__(self, parent, title)
		
	def body(self, master):
			
		frames = []
		frames.append(tk.Frame(master))
		frames[-1].pack(side=tk.LEFT, padx=2, pady=2, fill=tk.Y)
		tk.Label(frames[-1], text="E-vec").pack(side=tk.TOP)
		for eigvechead in self.data.get_headers():
			tk.Label(frames[-1], text=eigvechead).pack(side=tk.TOP)
		
		frames.append(tk.Frame(master))
		frames[-1].pack(side=tk.LEFT, padx=2, pady=2, fill=tk.Y)
		tk.Label(frames[-1], text="E-val").pack(side=tk.TOP)
		eigvals = self.data.get_eigenvalues()
		for i in range(eigvals.shape[1]):
			tk.Label(frames[-1], text="%.4f" % eigvals[0,i]).pack(side=tk.TOP)
		
		frames.append(tk.Frame(master))
		frames[-1].pack(side=tk.LEFT, padx=2, pady=2, fill=tk.Y)
		tk.Label(frames[-1], text="Energy").pack(side=tk.TOP)
		eigvalsum = np.sum(eigvals)
		for i in range(eigvals.shape[1]):
			curEnergy = eigvals[0,i]/eigvalsum
			tk.Label(frames[-1], text="%.4f" % curEnergy).pack(side=tk.TOP)
		
		frames.append(tk.Frame(master))
		frames[-1].pack(side=tk.LEFT, padx=2, pady=2, fill=tk.Y)
		tk.Label(frames[-1], text="Cumulative").pack(side=tk.TOP)
		curSum = 0
		for i in range(eigvals.shape[1]):
			curSum += eigvals[0,i]/eigvalsum
			tk.Label(frames[-1], text="%.4f" % curSum).pack(side=tk.TOP)
		
		# Eigenvectors
		eigvecs = self.data.get_eigenvectors()
		for col, header in enumerate(self.data.get_data_headers()):
			frames.append(tk.Frame(master))
			frames[-1].pack(side=tk.LEFT, padx=2, pady=2, fill=tk.Y)
			tk.Label(frames[-1], text=header.capitalize()).pack(side=tk.TOP)
			for row in range(eigvecs.shape[0]):
				curVal = eigvecs[row, col]
				tk.Label(frames[-1], text="%.4f" % curVal).pack(side=tk.TOP)
			
		return None # initial focus
		