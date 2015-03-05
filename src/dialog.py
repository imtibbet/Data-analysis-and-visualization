header='''
Ian Tibbetts
Colby College CS251 Spring '15
Professors Stephanie Taylor and Bruce Maxwell
'''
from photos import photos, descriptions


try:
	import tkinter as tk # python 3
except ImportError:
	import Tkinter as tk # python 2

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
		body.pack(padx=5, pady=5)

		self.buttonbox()

		self.grab_set()

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
		tk.Label(master, text=header).pack(side=tk.TOP)

class AboutMeDialog(OkDialog):
	def body(self, master):
		photoIan = tk.PhotoImage(data=photos["ian"])
		label = tk.Label(master, image=photoIan)
		label.image = photoIan
		label.pack(side=tk.TOP)
		tk.Label(master, text=descriptions["ian"], wraplength=80
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
			["Ctrl-Q", "quit the application"],
			["Ctrl-N", "clear the canvas"],
			["Double-B1", "show the raw data for the clicked object"]
								  ]
		for [row, [k, bd]] in enumerate(keyBindingDescriptions):
			tk.Label(master, text=k, relief=tk.GROOVE, width=20
					 ).grid(row=row, column=0)
			tk.Label(master, text=bd).grid(row=row, column=1)

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
		z = self.e2.get(self.e3.curselection())
		self.result = [x.upper(), y.upper(), z.upper()]
		
class PickAxesDialog(OkCancelDialog):

	def __init__(self, parent, data, title = None):

		self.headers = data.get_headers()
		OkCancelDialog.__init__(self, parent, title)
		
	def body(self, master):
			
		row=0
		col=0
		tk.Label(master, text="X Axes:").grid(row=row, column=col)
		self.e1 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e1.insert(tk.END, header)
		self.e1.select_set(0)
		self.e1.grid(row=row+1, column=col)
		
		col+=1
		tk.Label(master, text="Y Axes:").grid(row=row, column=col)
		self.e2 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e2.insert(tk.END, header)		  
		self.e2.select_set(1) 
		self.e2.grid(row=row+1, column=col)
		
		if len(self.headers) > 2:
			col+=1
			tk.Label(master, text="Z Axes:").grid(row=row, column=col)
			self.e3 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
			for header in self.headers:
				self.e3.insert(tk.END, header)		  
			self.e3.select_set(2)
			self.e3.grid(row=row+1, column=col)
		
		row=2
		col=0
		tk.Label(master, text="Size:").grid(row=row, column=col)
		self.e4 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e4.insert(tk.END, header)
		self.e4.select_set(0)
		self.e4.grid(row=row+1, column=col)
		
		col+=1
		tk.Label(master, text="Color:").grid(row=row, column=col)
		self.e5 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e5.insert(tk.END, header)		  
		self.e5.select_set(0)
		self.e5.grid(row=row+1, column=col)
		
		col+=1
		tk.Label(master, text="Shape:").grid(row=row, column=col)
		self.e6 = tk.Listbox(master, selectmode=tk.SINGLE, exportselection=0)
		for header in self.headers:
			self.e6.insert(tk.END, header)		  
		self.e6.select_set(0)
		self.e6.grid(row=row+1, column=col)
		
		return None # initial focus

	def apply(self):
		x = self.e1.get(self.e1.curselection())
		y = self.e2.get(self.e2.curselection())
		size = self.e4.get(self.e4.curselection())
		color = self.e5.get(self.e5.curselection())
		shape = self.e6.get(self.e6.curselection())
		if len(self.headers) < 3:
			self.result = [x, y, size, color, shape]
		else:
			z = self.e3.get(self.e3.curselection())
			self.result = [x, y, z, size, color, shape]