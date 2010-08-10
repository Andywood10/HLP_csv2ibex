#! /usr/bin/python
#-----------------------------------------------------------------
# csv2ibex.py 
# Version 1.2.4
#-----------------------------------------------------------------
# Author: Andrew Wood <andywood@vt.edu>
#                          
# HLP/Jaeger Lab
# University of Rochester
# 08/09/2010
#
# Converts a tab-delimited CSV file to a Javascript input file for
#	Ibex (formerly webSPR) web-based self-paced reading 
#	software, available at http://code.google.com/p/webspr/ 
#	under the New BSD License. 
#------------------------------------------------------------------

import csv
import sys

itemlist = []

END_PUNCTUATION = ['.', '!', '?']
COL_STIMULUS = "Stimulus"
COL_STIM_ID = "StimulusID"
COL_LIST = "List"
COL_ORDER = "TrialOrder"
COL_TYPE = "Item"
COL_CONDITION = "Condition"
COL_QUESTION = "Question"
COL_ANSWER = "Answer"

# UTILITY *************************************************************
qExitOpt = "PROMPT"

# qExit
# - display a message and prompt the user if they would like to continue
# - can pass option to auto fail or auto continue
#
def qExit(msg, option = "PROMPT"):
	if option == "AUTOFAIL": 
		print msg + "...STOPPING"
		sys.exit(1);
	elif option == "AUTOCONTINUE":
		print msg 
		return;
	
	c = raw_input(msg + "\nWould you like to continue anyway? (y/n): ")
	if c == 'y': return
	else: sys.exit(1)

# checkFile
# - check if a file exists and is openable
#
def checkFile(filename):
	try:
		f = open(filename).close()
	except IOError:
		print "\nERROR: Unable to open file '"+filename+"'\n"
		sys.exit(1)


# HEADER GENERATION ***************************************************

# removeWhitespace
# - Simple method to remove tabs and spaces from non-quote strings
#
def removeWhitespace(s):
	quoting = 0
	s2 = ""
	for c in s:
		if quoting == 1:
			if c == '\"': quoting = 0;
		elif quoting == 2:
			if c == '\'': quoting = 0;
		else:
			if c == '\"': quoting = 1;
			elif c == '\'': quoting = 2;
			elif c == '\t': continue;
			elif c == ' ': continue;
		s2 += c;
	return s2


# parseConfigFile
#	params:
#	 * conf:String - name of the input configuration file
#	return:
#	 * dictionary with following entries:
#		* inputfile:String - the name of the default input file (used if one isn't specified on command line)
#		* outputfile:String - name of the default output file (used if one isn't specified on command line)
#		* filler:String - how to treat fillers
#		* order:String - the shuffleSeq that describes the order of the items
#		* defaults:String - the item defaults: see the hlp wiki(FIXME: url here) for specifics
def parseConfigFile(conf):
	checkFile(conf)

	outDict = {}
	defStr = "var defaults = ["
	curDef = ""
	with open(conf, 'r') as fin:
		mode = "vars" #Options are 'vars' 'defaults'
		for line in fin:
			#remove whitespace and comment
			line = line[:-1]
			l = removeWhitespace(line)
			if l=="": continue;
			if l[0] == '#': continue;

			#handle the different kinds of input
			pairs = l.split(":")

			if(pairs[0]=="VARS" and pairs[1]==""): 
				mode ="vars"
				continue
			elif(pairs[0]=="DEFAULTS" and pairs[1]==""):
				mode ="defaults" 
				continue
			elif(pairs[1]==""):
				if(not curDef == ""): 
					defStr += curDef[:-1] + " },";
				curDef = "\n\t\""+pairs[0]+"\", {";
				continue
			
			#Handle actual varables
			if(mode == "vars"):
				outDict[pairs[0]] = pairs[1]
			elif(mode == "defaults"):
				curDef += "\n\t\t"+ pairs[0] + ": " + pairs[1] + ","
			else:
				pass
	defStr += curDef[:-1] + " }\n];"
	outDict["defaults"]=defStr
	return outDict


#formatHeader
# - convert the header dictionary into a js string.
def formatHeader(dct):
	order = dct["order"]
	filler = dct["filler"]
	tmp = ""

	if(filler == "SEP_EACH"):
		if(order == "ORDERED"): tmp = 'shuffle(randomize("filler"), anyOf(%s))';
		elif(order == "SHUFFLE"): tmp = 'shuffle(randomize("filler"), shuffle(%s))';
		elif(order == "RANDOM"): tmp = 'shuffle(randomize("filler"), seq(randomize(%s)))';
		elif(order == "RSHUFFLE"): tmp = 'shuffle(randomize("filler"), rshuffle(%s))';
	else:
		if(order == "ORDERED"): tmp = 'not("sep")';
		elif(order == "SHUFFLE"): tmp = 'shuffle("filler",%s)';
		elif(order == "RANDOM"): tmp = 'randomize(anyOf("filler",%s))';
		elif(order == "RSHUFFLE"): tmp = 'rshuffle("filler",%s)';

	try: 
		return 'var shuffleSequence = seq("intro", "practice", sepWith("sep", %s), endmsg);\n\nvar ds = "RegionedSentence"\nvar qs = "Question"\n\n%s' % (tmp, dct["defaults"])
	except KeyError:
		print "WARNING: invalid header dictionary...returning a NoneType"
		return None

#generateHeader
# - Wrappers for the parseConfigFile method that generates a formatted string rather than a dictionary. Has two versions, depending on whether the user wants the intermediate dictionary structure.
#	params (for Cnf version):
#	 * conf:String - name of the input config file
#	params (for Dct version):
#	 * dct: - dict gathered from parseConfigFile
#	return:
#	 * String header (formatted)
def generateHeaderCnf(conf):
	d = parseConfigFile(conf)
	return formatHeader(d)
def generateHeaderDct(dct):
	return formatHeader(dct)

# ITEM GENERATION *****************************************************

# generateItemDict
#	params:
#	 * infile:String - name of the input tab-separated file
#	return:
#	 * Dictionary of items in format {key: order.list, value: outputstring}
def generateItemDict(infile):
	checkFile(infile)

	listWarning = False
	orderWarning = False
	conditionWarning = False

	defaultOrder = 0
	orderCounters = {}
	outputLines = {}
	idList = []
	IDcount = 1
	
	with open(infile, 'r') as csvin:
		inputdata = csv.DictReader(csvin, delimiter='\t')

		for line in inputdata:
			#format fields (based on what fields do or don't exist in the input file)
			#STIMULUS ID
			try:
				try:
					idList.index(line[COL_STIM_ID])
					qExit("Warning: non-unique Stimulus Identifier: %s" %(line[COL_STIM_ID]), qExitOpt)
				except ValueError:
					if line[COL_STIM_ID] == None or line[COL_STIM_ID] == "":
						qExit("Warning: Blank Stimulus Identifier encountered", qExitOpt)
					idList.append(line[COL_STIM_ID])
					ID = line[COL_STIM_ID]
			except KeyError:
				if idList == []: 
					qExit("Warning: no Stimulus Identifiers provided.", qExitOpt);
					idList.append("NONE")
				ID = "stim"+str(IDcount)
			IDcount += 1
		
			#LIST
			try:
				lst = line[COL_LIST]
			except KeyError:
				if not listWarning: print "Warning: No 'List' column present, using one list."
				lst = 1

			#STIMULUS
			try:
				stimulus = line[COL_STIMULUS]
				if not stimulus.rstrip()[-1] in END_PUNCTUATION:
					print "Warning: no ending punctuation for stimulusID ",ID
			except KeyError:
				print "ERROR: No 'Stimulus' column...\n\tkinda required to build an experiment."
				sys.exit(1)
	
			#ITEM
			#try:
			#	item = line["Item"]
			#	for w in stimulus.split(" "):
			#		if(w == item):
			#			w = w + "@ITEM" 
			#except KeyError:
			#	item = None
	
			#ORDER		
			try:
				order = line[COL_ORDER]
				if order == "" or order == None:
					qExit("Warning: blank order at stimuli: %s" % (ID), qExitOpt)
			except KeyError:
				if not orderWarning: print "Warning: order not specified, using default ordering (1,2,3,...)."; orderWarning = True;
				try:
					order = orderCounters[lst]
				except KeyError:
					order = orderCounters[lst] = 1  #if it's the first item of a list
				orderCounters[lst] = orderCounters[lst]+1
	
			#TYPE
			try:
				stimType = line[COL_TYPE]
			except KeyError:
				stimType = "defaultStim"

			#CONDITION (overwrites type, unless it's '-'
			try:
				if(not line[COL_CONDITION] == "-"):
					stimType = line[COL_CONDITION]
			except KeyError:
				if not conditionWarning: print "Warning: conditions not specified, using 'defaultStim'";
			try: #update the item list for use in shuffleSeq
				if(not (stimType == "practice" or stimType == "filler")):
					itemlist.index(stimType)
			except ValueError:
				itemlist.append(stimType)
	
			#QUESTIONs and ANSWERs
			questionExist = False
			questions = ""
			i = 1
			while True:  #loop until no more questions are found
				try:
					question = line[COL_QUESTION+str(i)]
					answer = line[COL_ANSWER+str(i)]
	
					#make sure both the QuestionN and AnswerN fields have a value
					if((answer == "" or answer == None) and not (question == "" or question == None)): #exists question but no answer
						qExit("Warning at stimuli %s, question %d: No answer present for question" % (ID, i), qExitOpt)
						raise KeyError
					elif((question == "" or question == None) and not (answer == "" or answer == None)): #exists answer but no question
						qExit("Warning at stimuli %s, question %d: No question, but answer exists" % (ID, i), qExitOpt)
						raise KeyError
					elif(answer == "" or question =="" or answer == None or question == None): #Don't display if question or answer is missing
						raise KeyError
					else:
						questionExist = True

					#determine type of question (yes/no vs multiple choice)
					if(answer == "Y" or answer == "N"):
						if(answer == "Y"):
							answer = ', hasCorrect: "Yes", randomOrder: false'
						else:
							answer = ', hasCorrect: "No", randomOrder: false'
					else:
						tmp = '['
						for a in answer.split(','):
							tmp = tmp+'"'+a+'",'
						answer = ", as :"+tmp[:-1] + '], randomOrder: true'
			
					#build the string of questions
					questions += '\n\t\tqs, {q: "%s" %s},' % (question, answer)

				except KeyError:
					if not questionExist: print "WARNING: No question/answer pair found, using only stimulus.";
					break
				i += 1

			#Build output string dictionary
			tmpStr = ""
			if(stimType == "filler" or stimType == "practice"):
				if(questionExist == True):
					tmpStr = '["%s", ds, {s: "%s"}, %s],' % (stimType, stimulus, questions[:-1])
				else:
					tmpStr = '["%s", ds, {s: "%s"}],' % (stimType, stimulus)			
			else:
				if(questionExist == True):
					if(order == 1):
						tmpStr = '[["%s",%d], ds, {s: "%s"}, %s],' % (stimType, order, stimulus, questions[:-1])
					else:
						tmpStr = '[["%s",[%d,1]], ds, {s: "%s"}, %s],' % (stimType, order, stimulus, questions[:-1])
				else:
					tmpStr = '[["%s",[%s,%s]], ds, {s: "%s"}],' % (stimType, order, lst, stimulus)
			i = order+(0.1*float(lst))
			outputLines[i] = tmpStr
	return outputLines


# generateItemStr
#	params:
#	 * indict:Dictionary - contains the dictionary of items to be wrapped in a string
#	return:
#	 * String containing the 'items' structure
def generateItemStr(infile):
	dct = generateItemDict(infile)
	outputStr='\nvar items = [\n\t["sep", "Separator", {}],\n\t ' +\
		'["intro", "Message", {consentRequired: true, html: {include: "intro.html"}}],' +\
		'["info", "Form", {html: {include: "info.html"}}],'
	for i in sorted(dct):
		outputStr += "\n\t"+str(dct[i])
	return outputStr + '\n\t["endmsg", "Message", {consentRequired: false, html: {include: "contacts.html"}}] \n];'


# OUTPUT FILE CREATION **************************************************************	

# createOutfile
# -simple wrapper to create an output file (can be used for more than just ibex files...)
#	params:
#	 * outfile:String - name of the file to be created/overwritten
#	 * header:String - the file header
#	 * items:String - the items string
#	 * footer:String - file footer
#	return: nothing (creates output file)
def createOutfile(outfile, header, items, footer):
	if len(itemlist) > 0: 
		tmp = ""
		for item in itemlist:
			tmp += '"'+item+'",'
		header = header % (tmp[:-1])

	with open(outfile, 'w') as fout: 
		fout.write("%s\n%s\n%s\n" % (header, items, footer))
	print "File '" + outfile + "' sucessfully created"


# FORMAT RESULTS FILE *********************************************************************
# Produce two tab-delimited files from the supplied results file
def formatResults(infile):
	checkFile(infile)

	qOut = "Timestamp\tIP_MD5\tSeq\tType\tAnswerCorrect\n"
	sOut = "Timestamp\tIP_MD5\tSeq\tType\tWordNum\tWord\tTag\tReadTime\n"
	qSeq = 0
	sSeq = 0

	with open(infile, 'r') as fin:
		lastCtr = 1
		for line in fin:
			if (line[0] == '#'): continue;
			else:
				s = line.split(",")
				if(s[2] == "RegionedSentence"):
					if(qSeq == sSeq): sSeq += 1;
					elif(lastCtr > int(s[7])): sSeq += 1;  qSeq+=1;

					lastCtr = int(s[7])
					sOut += "%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\n" % (s[0],s[1],sSeq,s[5],s[7],s[8],s[10],s[9])					
				elif(s[2] == "Question"):
					if(qSeq != sSeq): qSeq += 1;
					qOut += "%s\t%s\t%d\t%s\t%s\n" % (s[0],s[1],qSeq,s[5],s[9])
				else:
					print "Warning: Unrecognized Controller: %s" % (s[2])

	with open('sentences.csv','w') as fout:
		fout.write(sOut)
		print "File 'sentences.csv' successfully written"
	with open('questions.csv','w') as fout:
		fout.write(qOut)
		print "File 'questions.csv' successfully written"


# USER INTERFACE *********************************************************************

if __name__=="__main__":
	import sys

	usageStr= "USAGE:\tpython csv2ibex.py [PARAMETERS] INPUT_FILE OUTPUT_FILE\n" +\
		  "or:\tpython csv2ibex.py -c [MORE PARAMETERS] CONFIG_FILE [INPUT_FILE OUTPUT_FILE]\n" +\
		  "or:\tpython csv2ibex.py -O [RESULTS_FILE (default 'results')]"

	helpStr = "\n======== IBEX Input File Converter ========\n" +\
		  "Author: Andrew Wood <andywood@vt.edu>\n" +\
		  "\n" +\
		  "Converts a tab-delimited CSV file to a javascript input file for Ibex.\n" +\
		  "\n"+usageStr +\
		  "\nCommand line options: \n" +\
		  "\t-c\tConfig File:\tIndicates the use of a custom configuration file (given on command line)\n" +\
		  "\t-d\tDefaults:   \tUse default IO files and ordering from the default config file\n" +\
		  "\t-f\tFiller opts:\tUse filler items in the normal ordering (default is to separate all items with a filler)\n" +\
		  "\t-O\tOutputMode: \tRun in 'Format Output' mode: make the Ibes results file more readable\n" +\
		  "\t-p\tPrompt:     \tPrompt the user for any missing information\n" +\
		  "\t-r\tRandomize:  \tRandomize items of each type (don't use if you hard coded an ordering)\n" +\
		  "\t-s\tShuffle:    \tShuffle (evenly space) the different types of items\n" +\
		  "======== ========================= ========\n"

	## Parse command line args ##
	infile = None
	outfile = None
	configfile = "default_cfg"

	cfile = False
	defaults = False
	doNothing = False
	fillerin = True
	outputFmtMode = False
	prompt = False
	randomize = False
	orderChanged = False
	shuffle = False
	ctr = 0;
	dct = {}

	#UNIX-style command parameters:
	for arg in sys.argv:
		if(ctr == 0): ctr += 1; continue;

		if(arg == "help"):
			print helpStr
			sys.exit(0)
		if(arg[0] != '-'):
			break
		else:
			for c in arg:
				if c == '-': continue;
				elif c == 'c': cfile = True;     #Use a custom config file
				elif c == 'd': defaults = True;  #Use default in-out files
				elif c == 'f': fillerin = False; #Treat Fillers as a normal item
				elif c == 'F': qExitOpt = "AUTOCONTINUE" #Force: ignore warnings and continue 
				elif c == 'n': doNothing = True; #Stop after parsing argv
				elif c == 'O': outputFmtMode = True #Output format mode
				elif c == 'p': prompt = True;    #Prompt for non-supplied info
				elif c == 'r': randomize = True; orderChanged = True   #Randomize items
				elif c == 's': shuffle = True; orderChanged = True  #Shuffle different types
				elif c == 'S': qExitOpt = "AUTOFAIL" #Strict: will automatically stop if an error is encountered
				else: print "Warning: unrecognized command '" + c + "'."
		ctr += 1

	#format output mode
	if(outputFmtMode):
		if(len(sys.argv) == ctr+1):
			infile = sys.argv[ctr]
			formatResults(infile)
		else:
			formatResults("results")
		sys.exit(0) 

	#handle defaults
	if not defaults:
		if (not cfile and len(sys.argv) == (2+ctr)): #(default config)
			infile = sys.argv[ctr]
			outfile = sys.argv[ctr+1]
		elif(cfile and len(sys.argv) == (1+ctr)): #(custom config...contains IO info)
			configfile = sys.argv[ctr]
		elif(cfile and len(sys.argv) == (3+ctr)): #(custom config...supplying IO from cmd)
			infile = sys.argv[ctr+1]
			outfile = sys.argv[ctr+2]
			configfile = sys.argv[ctr]
		elif(prompt): #(gather this info via command prompts)
	
			if(configfile == "default_cfg"):
				configfile = raw_input("Enter the name of your custom config file, or simply hit enter to continue with prompts:")
				if(configfile == ""): configfile = "default_cfg";
			if(infile == None or configfile == "default_cfg"):
				infile = raw_input("Enter the name of your input file (required): ")
				checkFile(infile)
			if(outfile == None or configfile == "default_cfg"):
				outfile = raw_input("Enter the desired output file name [data.js]: ")
				if(outfile == ""): outfile="data.js";
			if(configfile == "default_cfg"):
				if( (raw_input("Evenly space different item types? \nUse this option unless you have specified an order for all items (y/n)")) == 'y'): 
					shuffle = True
					orderChanged = True
				if( (raw_input("Randomize items? \nIMPORTANT: Only use this option if you did not specify an order! (y/n)")) == 'y'): 
					randomize = True
				orderChanged = True
				if( (raw_input("Separate all items with a filler? If no, fillers are treated as normal items. (y/n)")) == 'n'):
					fillerin = False
		#incorrect usage
		else:
			print usageStr + "Type 'python conversion0.3.py' help for more details"
			sys.exit(1)

	dct = parseConfigFile(configfile)

	#figure out appropriate ordering variables
	if not fillerin: dct["filler"] = "ITEM";
	
	if orderChanged:
		if shuffle:
			if randomize: dct["order"] = "RSHUFFLE";
			else: dct["order"] = "SHUFFLE";
		else:
			if randomize: dct["order"] = "RANDOMIZE";
			else: dct["order"] = "ORDERED";
	
	if infile == None: infile = dct["inputfile"];
	if outfile == None: outfile = dct["outputfile"];
	else: dct["outputfile"] = outfile;
	
	header = generateHeaderDct(dct)	
	items = generateItemStr(infile)
	
	#debug the cmd-line processor
	if doNothing:
		print "doing nothing:\ninput_file: " +infile+ "\noutput_file: " +outfile+ "\nconfig_file: " +str(configfile)+"\nOrderChanged? "+str(orderChanged)	+"\nShuffle? "+str(shuffle)+"\nRandomize? "+str(randomize)+"\nFiller as normal item? "+str(not fillerin)+"\n\n"+header+"\n"+items
		sys.exit(0)
	else:
		createOutfile(outfile, header, items, "")
		try:
			import tab
			tab.replace(outfile)
		except ImportError:
			pass


