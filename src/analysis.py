'''
Ian Tibbetts
Colby College CS251 Spring '15
Professors Stephanie Taylor and Bruce Maxwell
'''
import numpy as np

def data_range(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object 
	returns a list of 2-element lists with the minimum and maximum values for
	each column. The function is required to work only on numeric data types.
	'''
	colRanges = []
	colData = data.get_data(colHeaders)
	colMins = np.min(colData, axis=0)
	colMaxs = np.max(colData, axis=0)
	for i in range(colMins.shape[1]):
		colRanges.append([colMins[0,i], colMaxs[0,i]])
	return colRanges
	
def mean(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object and 
	returns a list of the mean values for each column. 
	'''
	return np.mean(data.get_data(colHeaders), axis=0).tolist()[0]
	
def stdev(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object and 
	returns a list of the standard deviation for each specified column. 
	'''
	return np.std(data.get_data(colHeaders), axis=0).tolist()[0]
		
def normalize_columns_separately(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object 
	returns a matrix with each column normalized so its minimum value 
	is mapped to zero and its maximum value is mapped to 1.
	'''
	colRanges = data_range(data, colHeaders)
	colData = data.get_data(colHeaders)
	for i, [colMin, colMax] in enumerate(colRanges):
		colData[:, i] = (colData[:, i]-colMin)*(1.0/(colMax-colMin))
	return colData
	
def normalize_columns_together(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object
	returns a matrix with each entry normalized so that the minimum value 
	(of all the data in this set of columns) is mapped to zero and 
	its maximum value is mapped to 1. 
	'''
	colData = data.get_data(colHeaders)
	mMin = np.min(colData)
	mMax = np.max(colData)
	return (colData-mMin)*(1.0/(mMax-mMin))