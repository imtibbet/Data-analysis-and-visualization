'''
Ian Tibbetts
Colby College CS251 Spring '15
Professors Stephanie Taylor and Bruce Maxwell
'''
import os
import sys
import csv
import numpy as np
import analysis
import datetime as dt
import re

class Data:
	
	def __init__(self, filename, verbose=True):
		'''
		constructor for the Data class
		parameter filename - either an existing csv filename or
			a list of lists representing data of the form:
			header1, header2, ..., headerN
			type1, type2, ..., typen
			data11, data12, ..., data1N
			data21, data22, ..., data2N
			.
			.
			.
			dataN1, dataN2, ..., dataNN
		parameter [verbose] - default true, enable printing to console
		'''
		# initialize some fields
		np.set_printoptions(suppress=True) # make numpy print nicely
		self.verbose = verbose # enable printing
		self.monthNames = {"January":1,
						   "February":2,
						   "March":3,
						   "April":4,
						   "May":5,
						   "June":6,
						   "July":7,
						   "August":8,
						   "September":9,
						   "October":10,
						   "November":11,
						   "December":12
						   }
		# dictionary mapping month string to number
		# include three letter versions of each month
		for month in self.monthNames.keys():
			self.monthNames[month[:3]] = self.monthNames[month]
		
		# convert input into list of lists of data
		try:
			# build data fields from the given filename
			with open( filename, 'rU' ) as fp: # rU for 'read' and 'universal end of line'
				lines = fp.readlines()
			print("file found,reading data")
			reader = csv.reader(lines)
		except:
			print("File not found, assuming input is list of lists of data")
			reader = filename
			
		# process given data to populate fields
		self.read(reader)
		if self.verbose: print("raw headers: %s" % self.raw_headers)
		if self.verbose: print("raw types: %s" % self.raw_types)
		if self.verbose: print("header2raw: %s" % self.header2raw)
		if self.verbose: print("rows:%d cols:%d" % self.raw_data.shape)
		if self.verbose: print(self.raw_data)
		self.buildNumericData()
		if self.verbose: print("header2matrix: %s" % self.header2matrix)
		if self.verbose: print("rows:%d cols:%d" % self.matrix_data.shape)
		if self.verbose: print(self.matrix_data)
			
	def read(self, reader):
		'''
		parse data lines in reader into fields for headers, types and raw data
		parameter reader - the lines of the csv file to parse
		'''
		self.raw_headers = [] # list of all header
		self.header2raw = {} # map header string to col index in raw data
		self.raw_types = [] # list of all types
		self.raw_data = [] # list of lists of all string data.
		for line in reader:
			line = [str(item) for item in line]
			if line[0].lstrip()[0] == "#":
				if self.verbose: print("comment line")
			elif not self.raw_headers:
				for col, header in enumerate(line):
					header = header.strip()
					self.raw_headers.append(header)
					self.header2raw[header] = col
					self.raw_data.append([])
			elif not self.raw_types:
				for raw_type in line:
					self.raw_types.append(raw_type.strip())
			else:
				for i, data in enumerate(line):
					self.raw_data[i].append(data)
		
		self.raw_data = np.matrix(self.raw_data).T
		
	def parseDate(self, rawDate):
		'''
		parameter rawDate - a generally formatted string month day year
		return - a list of integers of the form [month, day, year]
		'''
		[month, day, year] = re.split("/|-| |, |,", rawDate)
		if len(year) == 2: # resolve a partial year
			curYear = dt.date.today().year
			curCentury = str(curYear)[:2]
			year = curCentury + year # try current century
			if int(year) > curYear: # if future assume previous century
				year = str(int(curCentury)-1) + year[2:]
		if not month.isdigit():
			month = self.monthNames[month]
		return [int(month), int(day), int(year)]
		
	def buildNumericData(self):
		'''
		Builds the numeric data from the raw file data in fields.
		Raw data is assumed to have each list of lists of column data.
		'''
		self.matrix_data = [] # matrix of numeric data
		self.numericHeaders = []
		self.header2matrix = {} # map header string to col index in matrix data
		self.enum2value = {} # conversion dictionary between enum keys and index
		
		rawColIndex = 0
		for colIndex in range(self.raw_data.shape[1]):
			rawType = self.raw_types[colIndex]
			if rawType in ["numeric", "enum", "date"]:
				rawHeader = self.raw_headers[colIndex]
				self.numericHeaders.append(rawHeader)
				self.header2matrix[rawHeader] = rawColIndex
				rawColIndex += 1
				
				if rawType == "numeric":
					self.matrix_data.append([])
					for rawNum in self.raw_data[:, colIndex]:
						rawNum = rawNum[0,0]
						self.matrix_data[-1].append(rawNum)
						
				elif rawType == "enum":
					self.matrix_data.append([])
					enumIndex = 0
					for rawEnum in self.raw_data[:, colIndex]:
						rawEnum = rawEnum[0,0]
						if rawEnum not in self.enum2value:
							self.enum2value[rawEnum] = enumIndex
							enumIndex += 1
						self.matrix_data[-1].append(self.enum2value[rawEnum])
						
				elif rawType == "date":
					self.matrix_data.append([])
					for rawDate in self.raw_data[:, colIndex]:
						rawDate = rawDate[0,0]
						[month, day, year] = self.parseDate(rawDate)
						numDate = dt.date(year, month, day).toordinal()
						self.matrix_data[-1].append(numDate)
		
		self.matrix_data = np.matrix(self.matrix_data, np.float).T

	def addColumn(self, newHeader, newType, newData):
		'''
		adds a column to the data
		'''
		if len(newData) != self.raw_data.shape[0]:
			print("wrong number of points")
			return
		self.raw_headers.append(newHeader)
		self.raw_types.append(newType)
		self.header2raw[newHeader] = self.raw_data.shape[1]
		self.raw_data = np.column_stack((self.raw_data, newData))
		self.buildNumericData() # TODO, rebuilds numeric data from scratch
		
	def get_raw_headers(self): 
		'''
		returns a list of all of the headers.
		'''
		return self.raw_headers
	
	def get_raw_types(self): 
		'''
		returns a list of all of the types.
		'''
		return self.raw_types
	
	def get_raw_num_columns(self): 
		'''
		returns the number of columns in the raw data set
		'''
		return self.raw_data.shape[1]
	
	def get_raw_num_rows(self): 
		'''
		returns the number of rows in the data set
		'''
		return self.raw_data.shape[0]
	
	def get_raw_row(self, rowIndex): 
		'''
		returns a row of data (the type is list) 
		(Note: since there will be the same number of rows in the raw 
		and numeric data, Stephanie is writing just one method and 
		isn't added the name raw to this one. You can do something 
		different if you want.)
		'''
		return self.raw_data[rowIndex]
	
	def get_raw_value(self, rowIndex, colHeader): 
		'''
		takes a row index (an int) and column header (a string) and 
		returns the raw data at that location. 
		(The return type will be a string)
		'''
		return self.raw_data[rowIndex, self.header2raw[colHeader]]
		
	def get_headers(self):
		'''
		return list of headers of columns with numeric data
		'''
		return self.numericHeaders
	
	def get_num_columns(self):
		'''
		returns the number of columns of numeric data
		'''
		return self.matrix_data.shape[1]
	
	def get_row(self, rowIndex):
		'''
		take a row index and returns a row of numeric data
		'''
		return self.matrix_data[rowIndex]
	
	def get_value(self, rowIndex, colHeader): 
		'''
		takes a row index (int) and column header (string) and 
		returns the data in the numeric matrix.
		'''
		return self.matrix_data[rowIndex, self.header2matrix[colHeader]]
	
	def get_data(self, colHeaders, rows=[], rowStart=None, rowEnd=None): 
		'''
		parameter colHeaders - a list of columns headers
		parameter rows, rowStart, rowEnd - optional, rows has priority
		return a matrix with the data for the specified rows and columns.
		'''
		colIndices = [self.header2matrix[x] for x in colHeaders]
		# OR map(self.header2matrix.get, colHeaders)
		if rows:
			return (self.matrix_data[rows])[:, colIndices].copy()
		else:
			return self.matrix_data[rowStart:rowEnd, colIndices].copy()
	
if __name__ == "__main__":
	usage = "Usage: python %s <csv_filename>" % sys.argv[0]
	if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
		d = Data(sys.argv[1])
	else:
		print("File not found")
		print(usage)
		#exit()
		d = Data([["header1", "header2", "header3"], 
				  ["numeric", "numeric", "numeric"], 
				  ["1", "2", "3"], ["4", "5", "6"], 
				  ["7", "8", "9"], ["10", "11", "12"], 
				  ["13", "14", "15"], ["16", "17", "18"], 
				  ["19", "20", "21"], ["22", "23", "24"], 
				  ["25", "26", "27"]])
	
	print("\nraw data test")
	headers = d.get_raw_headers()
	print("d.get_raw_headers()")
	print(d.get_raw_headers())
	print("d.get_raw_types")
	print(d.get_raw_types())
	print("d.get_raw_num_columns")
	print(d.get_raw_num_columns())
	print("d.get_raw_num_rows")
	print(d.get_raw_num_rows())
	print("d.get_raw_row(1)")
	print(d.get_raw_row(1))
	print("type( d.get_raw_row(1) )")
	print(type( d.get_raw_row(1) ))
	print("d.get_raw_value(0,headers(1))")
	print(d.get_raw_value(0,headers[1]))
	print("type(d.get_raw_value(0,headers(1)))")
	print(type(d.get_raw_value(0,headers[1])))
	
	print("\nmatrix data test")
	headers = d.get_headers()
	print("d.get_headers()")
	print(d.get_headers())
	print("d.get_num_columns")
	print(d.get_num_columns())
	print("d.get_row(1)")
	print(d.get_row(1))
	print("type( d.get_row(1) )")
	print(type( d.get_row(1) ))
	print("d.get_value(0,headers(0))")
	print(d.get_value(0,headers[0]))
	print("type(d.get_value(0,headers(0)))")
	print(type(d.get_value(0,headers[0])))
	print("d.get_data(headers(0:1))")
	print(d.get_data(headers[0:1]))
	print("d.get_data(headers(0:1)).shape")
	print(d.get_data(headers[0:1]).shape)
	print("d.get_data(headers(0:1), [1,3,5,7])")
	print(d.get_data(headers[0:1], [1,3,5,7]))
	print("d.get_data(headers(0:1), [1,3,5,7]).shape")
	print(d.get_data(headers[0:1], [1,3,5,7]).shape)
	print("d.get_data(headers(0:1),rowStart=1)")
	print(d.get_data(headers[0:1],rowStart=1))
	print("d.get_data(headers(0:1),rowStart=1).shape")
	print(d.get_data(headers[0:1],rowStart=1).shape)
	print("d.get_data(headers(0:1),rowEnd=2)")
	print(d.get_data(headers[0:1],rowEnd=2))
	print("d.get_data(headers(0:1),rowEnd=2).shape")
	print(d.get_data(headers[0:1],rowEnd=2).shape)
	
	print("\nanalysis test")
	print("analysis.data_range(d, headers)")
	print(analysis.data_range(d, headers))
	print("analysis.mean(d, headers)")
	print(analysis.mean(d, headers))
	print("analysis.stdev(d, headers)")
	print(analysis.stdev(d, headers))
	print("analysis.normalize_columns_separately(d, headers)")
	print(analysis.normalize_columns_separately(d, headers))
	print("analysis.normalize_columns_together(d, headers)")
	print(analysis.normalize_columns_together(d, headers))
	
	print("\nadding a column")
	d.addColumn("newThing", "date", ["Mar 3, 2014"]*d.get_raw_num_rows())
	d.addColumn("newThing", "date", ["Mar/3/80"]*d.get_raw_num_rows())
	print(d.raw_data)
	print(type(d.raw_data))
	print(d.matrix_data)
	print(type(d.matrix_data))