# Bruce Maxwell
# Spring 2015
# CS 251 Project 8
#
# Naive Bayes class test
#

import sys
import data
import classifiers

def main(argv):

    if len(argv) < 2:
        print 'Usage: python %s <data file> <optional category file>' % (argv[0])
        exit(-1)
        
    d = data.Data(argv[1])

    if len(argv) > 2:
        catdata = data.Data(argv[2])
        cats = catdata.get_data( [catdata.get_headers()[0]] )
        A = d.get_data( d.get_headers() )
    else:
        # assume the categories are the last column
        cats = d.get_data( [d.get_headers()[-1]] )
        A = d.get_data( d.get_headers()[:-1] )

    # create a new classifier
    nbc = classifiers.NaiveBayes()

    # build the classifier
    nbc.build( A, cats )

    # print the classifier
    print nbc

    return

if __name__ == "__main__":
    main(sys.argv)    
