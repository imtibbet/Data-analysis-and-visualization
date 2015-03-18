'''
Ian Tibbetts
Sorts members of a python source file
'''
from optparse import OptionParser

def sortPy(lines, sortClasses=False, verbose=False):
	'''
	sort the methods of the given source code
	optionally sort classes if there are multiple

	Parameters:
	lines - the list of the lines of the python source file to be sorted
	sortClasses - boolean indicating if the classes should also be sorted

	Returns - the sorted contents as a list of lines
	'''
	result = []
	defs = {}
	curDef = None
	classes = {}
	curClass = None
	curClassDef = None
	inClass = False
	classNames = []
	nameMain = None
	multiLineDef = False
	for line in lines:

		splitline = line.split()
		if multiLineDef:
			newParams = line.split(")")[0].split(",")
			params += [param.strip() for param in newParams]
			if not params[-1]:
				params = params[:-1]
			else:
				multiLineDef = False
				if verbose: print("params %s" % params)
			
		elif splitline and splitline[0] == "def": # method definitions

			# parse method definition and set state variables
			methodName = splitline[1].split(':')[0].split('(')[0]
			params = line.split(":")[0].split("(")			
			if len(params) > 1:
				params = params[1].split(")")[0].split(",")
				params = [param.strip() for param in params]				
			else:
				params = [""]
			if params[0] == "self": # class methods
				if verbose: print("class level method %s" % methodName)
				curClassDef = methodName
				classes[curClass][1][curClassDef] = []
			else: # top level methods
				if verbose: print("top level method %s" % methodName)
				curDef = methodName
				defs[curDef] = []
				inClass = False
			if not params[-1]:
				multiLineDef = True
				params = params[:-1]
			else:
				if verbose: print("params %s" % params)

		elif splitline and splitline[0] == "class": # class definitions
			curClass = splitline[1]
			if verbose: print("class definition %s" % curClass)
			classes[curClass] = [[], {}]
			classNames.append(curClass)
			inClass = True
			curClassDef = None

		elif splitline and splitline[0] == "if" and splitline[1] == "__name__":
			if verbose: print("encountered line '%s'" % " ".join(splitline))
			nameMain = []

		# put the line into the appropriate location
		if nameMain != None: # goes at the end of the result file
			nameMain.append(line)
		elif not (curDef or curClass): # header, before classes or methods
			result.append(line)
		elif not inClass: # store all of the code for top level methods
			defs[curDef].append(line)
		elif not curClassDef: # store headers for top level classes
			classes[curClass][0].append(line)
		else:
			classes[curClass][1][curClassDef].append(line)
	
	if verbose: print("done reading input source file\n")
	for methodName in sorted(defs):
		if verbose: print("writing top level method %s" % methodName)
		for line in defs[methodName]:
			result.append(line)
	if sortClasses:
		classNames.sort()

	for className in classNames:
		for line in classes[className][0]:
			result.append(line)
		for methodName in sorted(classes[className][1]):
			if verbose: print("writing class level method %s" % methodName)
			for line in classes[className][1][methodName]:
				result.append(line)
	if nameMain:
		if verbose: print("writing name == main block")
		for line in nameMain:
			result.append(line)

	return result

if __name__ == '__main__':

	#define the command line interface usage message
	usage = "python %prog [-h help] [options (with '-'|'--' prefix)]"

	# used to parse command line arguments, -h will print options by default
	parser = OptionParser(usage)

	# indicate that the program should sort class definitions
	parser.add_option("-c","--classes", 
				help="to enable sorting of classes",
				action="store_true")
	
	# indicate that the program should overwrite the input file with the result
	parser.add_option("-i","--inplace", 
				help=("to enable sorting the file in place"+
					", otherwise provide an output filename"),
				action="store_true")
	
	# indicate that the program should print actions to console
	parser.add_option("-v","--verbose", 
				help="to enable printing status to the console",
				action="store_true")
	
	[options, args] = parser.parse_args()

	if options.verbose: print("\nreading input file %s" % args[0])
	with open(args[0], 'r') as infile:
		lines = infile.readlines()

	slines = sortPy(lines, options.classes, options.verbose)
	
	outputFilename = args[0] if options.inplace else args[1]

	with open(outputFilename, 'w') as outfile:
		outfile.writelines(slines)
	if options.verbose: print("output written to %s\n" % outputFilename)

