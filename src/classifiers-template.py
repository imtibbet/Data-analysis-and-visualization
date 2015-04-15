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

    def __init__(self, type):
        '''The parent Classifier class stores only a single field: the type of
        the classifier.  A string makes the most sense.

        '''
        self._type = type

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
        N = max(truecats.shape)
		confmtx = np.zeros((N, N))
		for i in range(classcats.shape[0]):
			confmtx[classcats[i]][int(truecats[i])-1] += 1
        return 

    def confusion_matrix_str( self, confmtx ):
        '''Takes in a confusion matrix and returns a string suitable for printing.'''
        s = ''
		s += "\nConfusion Matrix:\n"
		s += 'Actual->     Walking   Walk-up   Walk-dwn  Sitting   Standing   Laying'
		for i in range(len(confmtx)):
			s += 'Cluster %d' % (i)
			for val in confmtx[i]:
				s += "%10d" % (val)
		return s

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
        Classifier.__init__(self, 'Naive Bayes Classifier')
        
        # store the headers used for classification
        self.headers = headers
        # categories, labels and mapping
        self.categories = np.squeeze(np.asarray(categories))
        unique, mapping = np.unique( categories, return_inverse=True)
        self.classLabels = unique
        self.classMapping = mapping
        # unique data for the Naive Bayes: means, variances, scales
        if dataObj != None:
            A = dataObj.get_data(headers)
            self.means, self.varis, self.scales = build(A, categories)

    def build( self, A, categories ):
        '''Builds the classifier give the data points in A and the categories'''
        C = len(self.classLabels)
        # compute the means/vars/scales for each class
        means = np.vstack([np.mean(A[self.classMapping==i], axis=0) 
        					for i in range(C)])
        varis = np.square(np.vstack([np.std(A[self.classMapping==i], axis=0) 
        					for i in range(C)]))
        scales = 1.0/(np.sqrt(2.0*math.pi*varis)
        return [means, varis, scales]

    def classify( self, A, return_likelihoods=False ):
        '''Classify each row of A into one category. Return a matrix of
        category IDs in the range [0..C-1], and an array of class
        labels using the original label values. If return_likelihoods
        is True, it also returns the NxC likelihood matrix.

        '''

        # error check to see if A has the same number of columns as
        # the class means
        
        # make a matrix that is N x C to store the probability of each
        # class for each data point
        P = '' # a matrix of zeros that is N (rows of A) x C (number of classes)

        # calculate the probabilities by looping over the classes
        #  with numpy-fu you can do this in one line inside a for loop

        # calculate the most likely class for each data point
        cats = '' # take the argmax of P along axis 1

        # use the class ID as a lookup to generate the original labels
        labels = self.class_labels[cats]

        if return_likelihoods:
            return cats, labels, P

        return cats, labels

    def __str__(self):
        '''Make a pretty string that prints out the classifier information.'''
        s = "\nNaive Bayes Classifier\n"
        for i in range(self.num_classes):
            s += 'Class %d --------------------\n' % (i)
            s += 'Mean  : ' + str(self.class_means[i,:]) + "\n"
            s += 'Var   : ' + str(self.class_vars[i,:]) + "\n"
            s += 'Scales: ' + str(self.class_scales[i,:]) + "\n"

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
        Classifier.__init__(self, 'KNN Classifier')
        
        # store the headers used for classification
        # number of classes and number of features
        # original class labels
        # unique data for the KNN classifier: list of exemplars (matrices)
        # if given data,
            # call the build function

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
            s += 'Mean of Exemplars  :' + str(np.mean(self.exemplars[i], axis=0)) + "\n"

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
    

