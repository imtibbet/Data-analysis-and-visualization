'''
Ian Tibbetts
Colby College CS251 Spring '15
Professors Stephanie Taylor and Bruce Maxwell
'''
from scipy import stats

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
	
def linear_regression(d, ind, dep):
	'''
	linear regression for one or more independent variables
	
	Parameters:
	d - data set
	ind - list of headers for the independent variables
	dep - single header (not list) for the dependent variable 
	
	Returns [b, sse, r^2, t, p]
	the values of the fit (b), the sum-squared error (sse), the
	R^2 fit quality, the t-statistic, and the probability of a
	random relationship (p).
	'''
	# assign to y the column of data for the dependent variable
	y = d.get_data([dep])
	# assign to N the number of data points (rows in y)
	N = y.shape[0]
	# assign to A the columns of data for the independent variables
	A = d.get_data(ind)
	# add a column of 1's to A to represent the constant term in the 
	#	regression equation.  Remember, this is just y = mx + b (even 
	#	if m and x are vectors).
	A = np.column_stack((A, [1]*N))
	
	# assign to AAinv the result of calling numpy.linalg.inv( np.dot(A.T, A))
	#	The matrix A.T * A is the covariance matrix of the independent
	#	data, and we will use it for computing the standard error of the 
	#	linear regression fit below.
	AAinv = np.linalg.inv( np.dot(A.T, A))
	
	# assign to x the result of calling nump.linalg.lstsq( A, y )
	#	This solves the equation y = Ab, where A is a matrix of the 
	#	independent data b is the set of unknowns as a column vector, 
	#	and y is the dependent column of data.  The return value x 
	#	contains the solution for b.
	x = np.linalg.lstsq( A, y )
	
	# assign to b the first element of x.
	b = x[0]
	# assign to C the number of coefficients (rows in b)
	C = b.shape[0]
	# assign to df_e the value N-C, 
	#	This is the number of degrees of freedom of the error
	df_e = N - C
	# assign to df_r the value C-1
	#	This is the number of degrees of freedom of the model fit
	df_r = C - 1
	
	# assign to error, the error of the model prediction.  Do this by 
	#	taking the difference between the value to be predicted and
	#	the prediction. 
	#	y - numpy.dot(A, b)
	error = y - np.dot(A, b)
	
	# assign to sse, the sum squared error, which is the sum of the
	#	squares of the errors computed in the prior step, divided by the
	#	number of degrees of freedom of the error.  The result is a 1x1 matrix.
	#	numpy.dot(error.T, error) / df_e
	sse = np.dot(error.T, error) / df_e
	
	# assign to stderr, the standard error, which is the square root
	#	of the diagonals of the sum-squared error multiplied by the
	#	inverse covariance matrix of the data. This will be a Cx1 vector.
	#	numpy.sqrt( numpy.diagonal( sse[0, 0] * AAinv ) )
	stderr = np.sqrt( np.diagonal( sse[0, 0] * AAinv ) )
	
	# assign to t, the t-statistic for each independent variable by dividing 
	#	each coefficient of the fit by the standard error.
	t = b.T / stderr
	
	# assign to p, the probability of the coefficient indicating a
	#	random relationship. To do this we use the cumulative distribution
	#	function of the student-t distribution.
	p = (1 - stats.t.cdf(np.abs(t), df_e))
	
	# assign to r2, the r^2 coefficient indicating the quality of the fit.
	r = 1 - error.var() / y.var()
	
	# Return the values of the fit (b), the sum-squared error, the
	#	 R^2 fit quality, the t-statistic, and the probability of a
	#	 random relationship.
	return [b.T.tolist()[0], sse[0,0], (r*r), t.tolist()[0], p.tolist()[0]]

def mean(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object and 
	returns a list of the mean values for each column. 
	'''
	return np.mean(data.get_data(colHeaders), axis=0).tolist()[0]
	
def median(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object and 
	returns a list of the median values for each column. 
	'''
	return np.median(data.get_data(colHeaders), axis=0).tolist()[0]
	
def mode(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object and 
	returns a list of the mean values for each column. 
	'''
	# for use if no scipy
	#modes = []
	#data = data.get_data(colHeaders).T
	#for datacol in data:
	#	modes.append(collections.Counter(datacol.tolist()[0]).most_common(1)[0][0])
	#return modes
	return stats.mode(data.get_data(colHeaders))[0].tolist()[0]
	
def normalize_columns_separately(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object 
	returns a matrix with each column normalized so its minimum value 
	is mapped to zero and its maximum value is mapped to 1.
	'''
	colRanges = data_range(data, colHeaders)
	colData = data.get_data(colHeaders)
	for i, [colMin, colMax] in enumerate(colRanges):
		if colMin != colMax:
			colData[:, i] = (colData[:, i]-colMin)*(1.0/(colMax-colMin))
		else: # handle data that does not vary to avoid div by zero
			colData[:, i] -= colMin
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
	if mMin != mMax:
		return (colData-mMin)*(1.0/(mMax-mMin))
	else: # handle data that does not vary to avoid div by zero
		return colData-mMin
	
def stdev(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object and 
	returns a list of the standard deviation for each specified column. 
	'''
	return np.std(data.get_data(colHeaders), axis=0).tolist()[0]

	