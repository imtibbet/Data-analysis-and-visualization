'''
Ian Tibbetts
Colby College CS251 Spring '15
Professors Stephanie Taylor and Bruce Maxwell
'''
from scipy import stats
from data import PCAData
import numpy as np
import scipy.cluster.vq as vq
import random

def appendHomogeneous(m):
	'''
	append the homogeneous coordinate as the last column of given matrix
	'''
	return np.column_stack((m, np.ones(m.shape[0])))

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

def fuzzyPartitionToClusters(points, partition, m):
	'''
	
	'''
	x = np.asarray(points, np.float)
	w = np.asarray(partition, np.float)
	N, k = partition.shape
	clusters = np.empty((k, N))
	for j in range(k):
		num = np.sum([(w[i, j]**m)*x[i] for i in range(N)], axis=0)
		den = np.sum([(w[i, j]**m) for i in range(N)])
		curAvg = num/den
		#sw = np.squeeze(w[:,j])
		#curAvg = np.average(x, axis=0, weights=sw)
		clusters[j] = curAvg
	return clusters

def kmeans(d, headers, K, whiten=True, categories=[]):
	'''Takes in a Data object, a set of headers, and the number of clusters to create
	Computes and returns the codebook, codes and representation errors. 
	If given an Nx1 matrix of categories, it uses the category labels 
	to calculate the initial cluster means.
	'''
	# assign to A the result of getting the data from your Data object
	try:
		A = d.get_data(headers)
	except: # to allow passing just the matrix of the data
		A = d
	# Assign to W the result of calling vq.whiten on the data
	W = vq.whiten(A)
	# assign to codebook the result of calling kmeans_init with W, K, and categories
	codebook = kmeans_init(W, K, categories)
	# assign to codebook, codes, errors, the result of calling kmeans_algorithm with W and codebook		
	codebook, codes, errors = kmeans_algorithm(W, codebook)
	# move means of clusters out of whitened data space
	codebook *= np.std(A, axis=0)
	codebook += np.mean(A, axis=0)
	# return the codebook, codes, and representation error
	return [codebook, codes, errors]

def kmeans_algorithm(A, means):
	# set up some useful constants
	MIN_CHANGE = 1e-7
	MAX_ITERATIONS = 100
	D = means.shape[1]
	K = means.shape[0]
	N = A.shape[0]

	# iterate no more than MAX_ITERATIONS
	for i in range(MAX_ITERATIONS):
		# calculate the codes
		codes, errors = kmeans_classify( A, means )
		# calculate the new means
		newmeans = np.zeros_like( means )
		counts = np.zeros( (K, 1) )
		for j in range(N):
			newmeans[codes[j],:] += A[j,:]
			counts[codes[j],0] += 1.0

		# finish calculating the means, taking into account possible zero counts
		for j in range(K):
			if counts[j,0] > 0.0:
				newmeans[j,:] /= counts[j, 0]
			else:
				newmeans[j,:] = A[random.randint(0,A.shape[0]),:]

		# test if the change is small enough
		diff = np.sum(np.square(means - newmeans))
		means = newmeans
		if diff < MIN_CHANGE:
			break

	# call classify with the final means
	codes, errors = kmeans_classify( A, means )

	# return the means, codes, and errors
	return (means, codes, errors)

def kmeans_classify( d, means ):
	'''
	take in the data and cluster means
	return a matrix of ID values and distances
	The IDs should be the index of the closest cluster mean to the data point. 
	The distances should be the Euclidean distance to the nearest cluster mean. 
	'''
	data = d#.get_data(d.get_headers())
	dists = np.empty((data.shape[0], means.shape[0]))
	for row, point in enumerate(data):
		for k, cluster in enumerate(means):
			dists[row, k] = np.linalg.norm(point-cluster)
	return [np.argmin(dists, axis=1), np.min(dists, axis=1)]

def kmeans_init( d, K, categories=[] ):
	'''
	take in the data, the number of clusters K, and an optional set of categories
	return a numpy matrix with K rows, each one repesenting a cluster mean. 
	If no categories are given choose K random data points to be the means.
	'''
	data = d#.get_data(d.get_headers())
	rows = data.shape[0]
	categories = np.squeeze(np.asarray(categories))
	if len(categories):
		means = []
		for i in range(K):
			means.append(np.mean(data[categories == i], axis=0))
		means = np.vstack(means)
	else:
		means = data[random.sample(xrange(rows), K)]
	return means

def kmeans_numpy( d, headers, K, whiten=True, categories=[]):
	'''
	Takes in a Data object, a set of headers, and the number of clusters to create
	Computes and returns the codebook, codes, and representation error.
	'''
	# assign to A the result of getting the data from your Data object
	try:
		A = d.get_data(headers)
	except: # to allow passing just the matrix of the data
		A = d
	# assign to W the result of calling vq.whiten on A
	W = np.asarray(vq.whiten(A))
	# assign to codebook, bookerror the result of calling vq.kmeans with W and K
	
	categories = np.squeeze(np.asarray(categories))
	if len(categories):
		means = []
		for i in range(K):
			means.append(np.mean(W[categories == i], axis=0))
		K = np.asarray(np.vstack(means))
	codebook, bookerror = vq.kmeans(W, K)
	# assign to codes, error the result of calling vq.vq with W and the codebook
	codes, error = vq.vq(W, codebook)
	# return codebook, codes, and error
	return [codebook, codes, error]

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
	A = appendHomogeneous(A)
	
	# assign to AAinv the result of calling numpy.linalg.inv( np.dot(A.T, A))
	#	The matrix A.T * A is the covariance matrix of the independent
	#	data, and we will use it for computing the standard error of the 
	#	linear regression fit below.
	AAinv = np.linalg.inv(np.dot(A.T, A))
	
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
	r2 = 1 - error.var() / y.var()
	
	# Return the values of the fit (b), the sum-squared error, the
	#	 R^2 fit quality, the t-statistic, and the probability of a
	#	 random relationship.
	return [b.T.tolist()[0], sse[0,0], r2, t.tolist()[0], p.tolist()[0]]

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
	return stats.mode(data.get_data(colHeaders))[0].tolist()[0]
	
def normalize_columns_separately(data, colHeaders, forceRanges=[]):
	'''
	Takes in a list of column headers and the Data object 
	returns a matrix with each column normalized so its minimum value 
	is mapped to zero and its maximum value is mapped to 1.
	'''
	colRanges = data_range(data, colHeaders)
	for i, forceRange in enumerate(forceRanges):
		if forceRange:
			colRanges[i] = forceRange
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
	
def pca(data, colHeaders, prenorm=True, verbose=False):
	'''
	perform a PCA analysis on the data for the given headers
	returns a PCAData object with the source column headers, projected data, 
			eigenvalues, eigenvectors, and source data means within it
	'''
	
	# get data from parameters, use to compute eigenvectors/values
	A = (normalize_columns_separately(data, colHeaders) if prenorm 
		else data.get_data(colHeaders))
	C = np.cov(A, rowvar=0)
	W, V = np.linalg.eig(C)
	
	# sort the eigenvectors V and eigenvalues W to be in descending order 
	oW = np.empty_like(W)
	oV = np.empty_like(V)
	for i, j in enumerate(reversed(np.argsort(W))):
		oW[i] = W[j]
		oV[:,i] = V[:,j]
	W = np.asmatrix(oW)
	V = np.asmatrix(oV).T
	
	# project the data onto the eigenvectors
	m = np.mean(A, axis=0)
	D = A - m
	projData = (V * D.T).T
	return PCAData(colHeaders, projData, W, V, m, verbose=verbose)

def stdev(data, colHeaders):
	'''
	Takes in a list of column headers and the Data object and 
	returns a list of the standard deviation for each specified column. 
	'''
	return np.std(data.get_data(colHeaders), axis=0).tolist()[0]

	
if __name__ == '__main__':
	
	d = np.matrix([	[0.9, 0.9, 0.8, 0.8],
					[0.86, 0.86, 0.86, 0.86],
					[0.2, 0.2, 0.11, 0.1],
					[0.14, 0.15, 0.15, 0.14]] )
	w = np.matrix([	[0,  1],
					[ 0,  1],
					[ 1,  0],
					[ 1,  0]])
	w = np.matrix([	[0.1,  0.9],
					[ 0.2,  0.8],
					[ 0.5,  0.5],
					[ 0.8,  0.2]])
	print("")
	print(fuzzyPartitionToClusters(d, w, 2))
	#print(kmeans_numpy(d, [], 2)[0])
	