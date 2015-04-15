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

class Classifier:
	'''The parent Classifier class stores the common fields and methods
	
	'''

	def __init__(self, type, dataObj=None, headers=[]):
		'''Takes in a type, a set of F headers, and an array of
		categories, one category label for each data point.
		'''
		#  the type of the classifier (e.g. string)
		self._type = type
		if dataObj == None:
			return
		# store the headers used for classification
		self.headers = headers if headers else dataObj.get_headers()

	def setCategoryFields( self, categories ):
		'''Set the fields associated with the categories'''
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
		# allow lists, column matrix, row matrix, etc for the N length lists
		truecats = np.squeeze(np.asarray(truecats))
		classcats = np.squeeze(np.asarray(classcats))
		N = len(truecats)
		confmtx = np.zeros((self.numClasses, self.numClasses))
		for i in range(N):
			confmtx[classcats[i]][truecats[i]] += 1
		return confmtx 

	def confusion_matrix_str( self, confmtx ):
		'''Takes in a confusion matrix and returns a string suitable for printing.'''
		s = ''
		s += "\nConfusion Matrix:\n"
		s += 'Actual -> '+' | '.join(self.headers)+'\n'
		for i in range(len(confmtx)):
			s += 'Cluster %d' % (i)
			for val in confmtx[i]:
				s += "%10d" % (val)
		return s+'\n'

	def __str__(self):
		'''Converts a classifier object to a string.  Prints out the type.'''
		return str(self._type)



class NaiveBayes(Classifier):
	'''NaiveBayes implements a simple NaiveBayes classifier using a
	Gaussian distribution as the pdf.

	'''

	def __init__(self, dataObj=None, headers=[], categories=None):
		'''Takes in a Data object with N points, a set of F headers, and a
		matrix of categories, one category label for each data point.'''

		# call the parent init with the type
		Classifier.__init__(self, 'Naive Bayes Classifier', dataObj, headers)
		
		# unique data for the Naive Bayes: means, variances, scales
		if dataObj != None and categories != None:
			A = dataObj.get_data(self.headers)
			self.build(A, categories)

	def build( self, A, categories ):
		'''Builds the classifier give the data points in A and the categories'''
		# compute the means/vars/scales for each class
		print("building")
		self.setCategoryFields(categories)
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
		print("classifying")
		# error check to see if A has the same number of columns as the class means
		if A.shape[1] != self.means.shape[1]:
			print("classify error: A and means have wrong shapes")
			return
			
		N = A.shape[0]
		# calculate the N x C matrix of probabilities by looping over the classes
		P = np.hstack([np.prod(np.multiply(self.scales[c], 
								np.exp(-np.square(A-self.means[c])/(2*self.varis[c]))),
							axis=1)
						for c in range(self.numClasses)])
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

	def __init__(self, dataObj=None, headers=[], categories=None, K=None):
		'''Take in a Data object with N points, a set of F headers, and a
		matrix of categories, with one category label for each data point.'''

		# call the parent init with the type
		Classifier.__init__(self, 'KNN Classifier', headers, categories)
		
		# unique data for the KNN classifier: list of exemplars (matrices)
		if dataObj != None:
			A = dataObj.get_data(headers)
			self.means, self.varis, self.scales = build(A, categories)

	def build( self, A, categories, K = None ):
		'''Builds the classifier give the data points in A and the categories'''

		# figure out how many categories there are and get the mapping (np.unique)
		# for each category i, build the set of exemplars
			# if K is None
				# append to exemplars a matrix with all of the rows of A where the category/mapping is i
			# else
				# run K-means on the rows of A where the category/mapping is i
				# append the codebook to the exemplars

		# store any other necessary information: # of classes, # of features, original labels

		return

	def classify(self, A, K=3, return_distances=False):
		'''Classify each row of A into one category. Return a matrix of
		category IDs in the range [0..C-1], and an array of class
		labels using the original label values. If return_distances is
		True, it also returns the NxC distance matrix.

		The parameter K specifies how many neighbors to use in the
		distance computation. The default is three.'''

		# error check to see if A has the same number of columns as the class means
		

		# make a matrix that is N x C to store the distance to each class for each data point
		D = '' # a matrix of zeros that is N (rows of A) x C (number of classes)
		
		# for each class i
			# make a temporary matrix that is N x M where M is the number of examplars (rows in exemplars[i])
			# calculate the distance from each point in A to each point in exemplar matrix i (for loop)
			# sort the distances by row
			# sum the first K columns
			# this is the distance to the first class

		# calculate the most likely class for each data point
		cats = '' # take the argmin of D along axis 1

		# use the class ID as a lookup to generate the original labels
		labels = self.class_labels[cats]

		if return_distances:
			return cats, labels, D

		return cats, labels

	def __str__(self):
		'''Make a pretty string that prints out the classifier information.'''
		s = "\nKNN Classifier\n"
		for i in range(self.num_classes):
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
	

