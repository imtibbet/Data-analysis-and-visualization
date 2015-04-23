# Template by Bruce Maxwell
# Author: Ian Tibbetts
# Spring 2015
# CS 251 Project 8
#
# Classifier class and child definitions

import sys
import data
import analysis as an
import numpy as np
import math

def classify(dtrain, dtest, classHeader, headers=[], knnbool=False, K=None):
	'''
	use the training set to build a classifier
	knnbool = False -> Naive Bayes else -> KNN using k parameter
	using the classes in the column associated with the given class Header
	classifies the training and test data and prints the confusion matrices
	returns the column of classifications for the test data
	'''
	# fix up the parameters
	headers = headers if len(headers) else dtrain.get_headers()
	if classHeader in headers:
		headers.remove(classHeader)

	# do the classification
	truetraincats = dtrain.get_data([classHeader])
	nb = (NaiveBayes(dtrain, headers, categories = truetraincats) if not knnbool else
		KNN(dtrain, headers, categories = truetraincats, K=K))
	traincats, trainlabels = nb.classify(dtrain.get_data(headers))
	testcats, testlabels = nb.classify(dtest.get_data(headers))
	print("train")
	print(nb.confusion_matrix_str(nb.confusion_matrix(truetraincats, traincats)))
	try:
		print("test")
		truetestcats = dtest.get_data([classHeader])
		print(nb.confusion_matrix_str(nb.confusion_matrix(truetestcats, testcats)))
	except:
		print("test data has no header "+classHeader)
	return testcats

class Classifier:
	'''The parent Classifier class stores the common fields and methods
	
	'''

	def __init__(self, typ, dataObj=None, headers=[], verbose=False):
		'''Takes in a type, a set of F headers, and an array of
		categories, one category label for each data point.
		'''
		#  the type of the classifier (e.g. string)
		self._type = typ
		self.verbose = verbose
		if dataObj == None:
			return
		# store the headers used for classification
		self.headers = headers if headers else dataObj.get_headers()

	def setCategoryFields( self, categories ):
		'''Set the fields associated with the categories'''
		if self.verbose: print("setting categories")
		# categories, labels and mapping
		self.categories = np.squeeze(np.asarray(categories))
		unique, mapping = np.unique( self.categories, return_inverse=True)
		self.classLabels = unique
		self.numClasses = len(self.classLabels)
		self.classMapping = mapping

	def type(self, newtype = None):
		'''Set or get the type with this function'''
		if newtype != None:
			self._type = newtype
		return self._type

	def confusion_matrix( self, truecats, classcats ):
		'''Takes in two Nx1 matrices of zero-index numeric categories and
		computes the confusion matrix. The rows represent true
		categories, and the columns represent the classifier output.
		'''
		if self.verbose: print("building confusion matrix")
		# allow lists, column matrix, row matrix, etc for the N length lists
		truecats = np.squeeze(np.asarray(truecats))
		unique, mapping = np.unique( truecats, return_inverse=True)
		truecats = mapping
		classcats = np.squeeze(np.asarray(classcats))
		N = len(truecats)
		confmtx = np.zeros((self.numClasses, self.numClasses))
		for i in range(N):
			confmtx[classcats[i]][truecats[i]] += 1
		return confmtx 

	def confusion_matrix_str( self, confmtx ):
		'''Takes in a confusion matrix and returns a string suitable for printing.'''
		confmtx = np.asmatrix(confmtx)
		s = ''
		s += "\nConfusion Matrix:\n"
		s += 'Predicted |    '+'   |   '.join(self.classLabels.astype(str))+'\n'
		s += 'Actual--------------------------------------\n'
		for i in range(confmtx.shape[0]):
			s += 'Cluster %d | ' % (i)
			for j in range(confmtx.shape[1]):
				s += "%8d" % (confmtx[i, j])
			s+='\n'
		return s

	def __str__(self):
		'''Converts a classifier object to a string.  Prints out the type.'''
		return str(self._type)



class NaiveBayes(Classifier):
	'''NaiveBayes implements a simple NaiveBayes classifier using a
	Gaussian distribution as the pdf.

	'''

	def __init__(self, dataObj=None, headers=[], categories=None, verbose=False):
		'''Takes in a Data object with N points, a set of F headers, and a
		matrix of categories, one category label for each data point.'''

		# call the parent init with the type
		Classifier.__init__(self, 'Naive Bayes Classifier', dataObj, headers, verbose)
		
		# categories being None means that build will require categories param
		if categories == None:
			self.categories = None
		else:
			self.setCategoryFields(categories)
			if dataObj != None and categories != None:
				A = dataObj.get_data(self.headers)
				self.build(A, categories)

	def build( self, A, categories=None ):
		'''Builds the classifier give the data points in A and the categories'''
		if self.verbose: print("building Naive Bayes classifier")
		if categories == None and self.categories == None:
			print("categories not set, aborting")
			return
		elif self.categories == None: self.setCategoryFields(categories)
		
		# compute the means/vars/scales for each class
		self.means = np.vstack([np.mean(A[self.classMapping==i], axis=0) 
							for i in range(self.numClasses)])
		self.varis = np.square(np.vstack([np.std(A[self.classMapping==i], axis=0) 
							for i in range(self.numClasses)]))
		self.scales = 1.0/np.sqrt(2.0*math.pi*self.varis)

	def classify( self, A, return_likelihoods=False ):
		'''Classify each row of A into one category. Return a matrix of
		category IDs in the range [0..C-1], and an array of class
		labels using the original label values. If return_likelihoods
		is True, it also returns the NxC likelihood matrix.

		'''
		if self.verbose: print("classifying Naive Bayes")
		# error check to see if A has the same number of columns as the class means
		if A.shape[1] != self.means.shape[1]:
			print("classify error: A and means have wrong shapes, aborting")
			return
			
		# calculate the N x C matrix of probabilities by looping over the classes
		P = np.column_stack([ # number of columns in P == num classes
							np.prod(np.multiply(self.scales[i], 
								np.exp(-np.square(A-self.means[i])/
									(2*self.varis[i]))),
							axis=1)
						for i in range(self.numClasses)])
		# calculate the most likely class for each data point
		cats = np.squeeze(np.asarray(np.argmax(P, axis=1)))

		# use the class ID as a lookup to generate the original labels
		labels = self.classLabels[cats]
		return [cats, labels, P] if return_likelihoods else [cats, labels]

	def __str__(self):
		'''Make a pretty string that prints out the classifier information.'''
		s = "\nNaive Bayes Classifier\n"
		for i in range(self.numClasses):
			s += 'Class %d --------------------\n' % (i)
			s += 'Mean	: ' + str(self.means[i,:]) + "\n"
			s += 'Var	: ' + str(self.varis[i,:]) + "\n"
			s += 'Scales: ' + str(self.scales[i,:]) + "\n"

		s += "\n"
		return s
		
	def write(self, filename):
		'''Writes the Bayes classifier to a file.'''
		# extension
		return

	def read(self, filename):
		'''Reads in the Bayes classifier from the file'''
		# extension
		return

	
class KNN(Classifier):

	def __init__(self, dataObj=None, headers=[], categories=None, K=None, verbose=False):
		'''Take in a Data object with N points, a set of F headers, and a
		matrix of categories, with one category label for each data point.'''

		# call the parent init with the type
		Classifier.__init__(self, 'KNN Classifier', dataObj, headers, verbose)
		self.K = K
		# categories being None means that build will require categories param
		if categories == None:
			self.categories = None
		else:
			self.setCategoryFields(categories)
			if dataObj != None and categories != None:
				A = dataObj.get_data(self.headers)
				self.build(A, categories)

	def build( self, A, categories=None, K = None ):
		'''Builds the classifier give the data points in A and the categories'''
		if self.verbose: print("building KNN classifier")
		if categories == None and self.categories == None:
			print("categories not set, aborting")
			return
		if K != None: self.K = K
		if self.categories == None: self.setCategoryFields(categories)
		self.exemplars = ([A[self.classMapping == i]
							for i in range(self.numClasses)] if self.K == None 
						else [an.kmeans(A[self.classMapping == i], K=self.K, whiten=True)[0]
							for i in range(self.numClasses)])

	def classify(self, A, K=3, return_distances=False):
		'''Classify each row of A into one category. Return a matrix of
		category IDs in the range [0..C-1], and an array of class
		labels using the original label values. If return_distances is
		True, it also returns the NxC distance matrix.

		The parameter K specifies how many neighbors to use in the
		distance computation. The default is three.'''

		if self.verbose: print("classifying KNN")
		# error check to see if A has the same number of columns as the class means
		if A.shape[1] != self.exemplars[0].shape[1]:
			print("classify error: A and means have wrong shapes, aborting")
			return
		# make a matrix that is N x C to store the distance to each class for each data point
		# numpy fu!
		D = np.column_stack([ # number of columns in D == num classes
					np.sum(np.sort(
						# classD
						np.vstack([[np.linalg.norm(row-exemplar) 
								for exemplar in self.exemplars[i]] 
									for row in A])
								)[:, :K], axis=1)
					for i in range(self.numClasses)])

		# calculate the most likely class for each data point
		cats = np.argmin(D, axis=1) # take the argmin of D along axis 1

		# use the class ID as a lookup to generate the original labels
		labels = self.classLabels[cats]

		if return_distances:
			return cats, labels, D

		return cats, labels

	def __str__(self):
		'''Make a pretty string that prints out the classifier information.'''
		s = "\nKNN Classifier\n"
		for i in range(self.numClasses):
			s += 'Class %d --------------------\n' % (i)
			s += 'Number of Exemplars: %d\n' % (self.exemplars[i].shape[0])
			s += 'Mean of Exemplars	 :' + str(np.mean(self.exemplars[i], axis=0)) + "\n"

		s += "\n"
		return s


	def write(self, filename):
		'''Writes the KNN classifier to a file.'''
		# extension
		return

	def read(self, filename):
		'''Reads in the KNN classifier from the file'''
		# extension
		return
	

