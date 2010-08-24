#! /usr/bin/python
#-----------------------------------------------------------------
# csv2ibex.py
# Version 0.9.5
#-----------------------------------------------------------------
# Author: Andrew Wood <andywood@vt.edu>
# Modified by: Andrew Watts <awatts@bcs.rochester.edu>
#
# HLP/Jaeger Lab
# University of Rochester
# 08/11/2010
#
# Converts a tab-delimited CSV file to a Javascript input file for
#   Ibex (formerly webSPR) web-based self-paced reading
#   software, available at http://code.google.com/p/webspr/
#   under the New BSD License.
#------------------------------------------------------------------

import csv
import sys

itemlist = []

END_PUNCTUATION = ['.', '!', '?']
COL_STIMULUS = "Stimulus"
COL_STIM_ID = "StimulusID"
COL_LIST = "List"
COL_ORDER = "TrialOrder"
COL_TYPE = "StimulusType"
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

# check_file
# - check if a file exists and is openable
#
def check_file(filename):
    try:
        f = open(filename).close()
    except IOError:
        print "\nERROR: Unable to open file '"+filename+"'\n"
        sys.exit(1)


# HEADER GENERATION ***************************************************

# remove_whitespace
# - Simple method to remove tabs and spaces from non-quote strings
#
def remove_whitespace(s):
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


# parse_config_file
#   params:
#    * conf:String - name of the input configuration file
#   return:
#    * dictionary with following entries:
#       * inputfile:String - the name of the default input file (used if one isn't specified on command line)
#       * outputfile:String - name of the default output file (used if one isn't specified on command line)
#       * filler:String - how to treat fillers
#       * order:String - the shuffleSeq that describes the order of the items
#       * defaults:String - the item defaults: see the hlp wiki(FIXME: url here) for specifics
def parse_config_file(conf):
    check_file(conf)

    outDict = {}
    defStr = "var defaults = ["
    curDef = ""
    with open(conf, 'r') as fin:
        mode = "vars" #Options are 'vars' 'defaults'
        for line in fin:
            #remove whitespace and comment
            line = line[:-1]
            l = remove_whitespace(line)
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


#format_header
# - convert the header dictionary into a js string.
def format_header(dct):
    order = dct["order"]
    filler = dct["filler"]
    tmp = ""

    if(filler == "SEP_EACH"):
        tmp = {
            "ORDERED" : 'shuffle(randomize("filler"), anyOf(%s))',
            "SHUFFLE" : 'shuffle(randomize("filler"), shuffle(%s))',
            "RANDOM" : 'shuffle(randomize("filler"), seq(randomize(%s)))',
            "RSHUFFLE" : 'shuffle(randomize("filler"), rshuffle(%s))'
        }[order]
    else:
        tmp = {
            "ORDERED" : 'not("sep")',
            "SHUFFLE" : 'shuffle("filler",%s)',
            "RANDOM" : 'randomize(anyOf("filler",%s))',
            "RSHUFFLE" : 'rshuffle("filler",%s)'
        }[order]

    try:
        return 'var shuffleSequence = seq("intro", "info", "practice", sepWith("sep", %s), endmsg);\n\nvar ds = "RegionedSentence"\nvar qs = "Question"\n\n%s' % (tmp, dct["defaults"])
    except KeyError:
        print "WARNING: invalid header dictionary...returning a NoneType"
        return None

#generateHeader
# - Wrappers for the parse_config_file method that generates a formatted string rather than a dictionary. Has two versions, depending on whether the user wants the intermediate dictionary structure.
#   params (for Cnf version):
#    * conf:String - name of the input config file
#   params (for Dct version):
#    * dct: - dict gathered from parse_config_file
#   return:
#    * String header (formatted)
def generate_header_cnf(conf):
    d = parse_config_file(conf)
    return format_header(d)
def generate_header_dct(dct):
    return format_header(dct)

# ITEM GENERATION *****************************************************

# generate_item_dict
#   params:
#    * infile:String - name of the input tab-separated file
#   return:
#    * Dictionary of items in format {key: order.list, value: outputstring}
def generate_item_dict(infile):
    check_file(infile)

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
                if stimulus == "":
                    qExit("Warning: Blank stimulus: "+ID, qExitOpt)
                    continue
                elif not stimulus.rstrip()[-1] in END_PUNCTUATION:
                    print "Warning: no ending punctuation for stimulusID ",ID
            except KeyError:
                print "ERROR: No 'Stimulus' column...\n\t-required to build an experiment!"
                sys.exit(1)

            #ITEM
            #try:
            #   item = line["Item"]
            #   for w in stimulus.split(" "):
            #       if(w == item):
            #           w = w + "@ITEM"
            #except KeyError:
            #   item = None

            #ORDER
            try:
                order = int(line[COL_ORDER])
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
                if(not line[COL_CONDITION].upper() in ["-", "", "NA", "N/A"]):
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
                        qExit("WARNING at stimuli %s, question %d: No answer present for question" % (ID, i), qExitOpt)
                        raise KeyError
                        continue
                    elif((question == "" or question == None) and not (answer == "" or answer == None)): #exists answer but no question
                        qExit("WARNING at stimuli %s, question %d: No question, but answer exists" % (ID, i), qExitOpt)
                        raise KeyError
                        continue
                    elif(answer == "" or question =="" or answer == None or question == None): #Don't display if question or answer is missing
                        raise KeyError
                        continue
                    else:
                        questionExist = True

                    #determine type of question (yes/no vs multiple choice)
                    if(answer.upper() == "Y" or answer.upper() == "N"):
                        if(answer.upper() == "Y"):
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
                    if not questionExist: print "No question/answer pair found for stimulus",ID,", using only stimulus.";
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


# generate_item_str
#   params:
#    * indict:Dictionary - contains the dictionary of items to be wrapped in a string
#   return:
#    * String containing the 'items' structure
def generate_item_str(infile):
    dct = generate_item_dict(infile)
    outputStr='\nvar items = [\n\t["sep", "Separator", {}],\n\t' +\
        '["intro", "Message", {consentRequired: true, html: {include: "intro.html"}}],\n\t' +\
        '["info", "Form", {html: {include: "info.html"}}],'
    for i in sorted(dct):
        outputStr += "\n\t"+str(dct[i])
    return outputStr + '\n\t["endmsg", "Message", {consentRequired: false, html: {include: "contacts.html"}}] \n];'


# OUTPUT FILE CREATION **************************************************************

# create_outfile
# -simple wrapper to create an output file (can be used for more than just ibex files...)
#   params:
#    * outfile:String - name of the file to be created/overwritten
#    * header:String - the file header
#    * items:String - the items string
#    * footer:String - file footer
#   return: nothing (creates output file)
def create_outfile(outfile, header, items, footer):
    if len(itemlist) > 0:
        tmp = ""
        for item in itemlist:
            tmp += '"'+item+'",'
        try:
            header = header % (tmp[:-1])
        except TypeError:
            pass

    with open(outfile, 'w') as fout:
        fout.write("%s\n%s\n%s\n" % (header, items, footer))
    print "File '" + outfile + "' sucessfully created"


# FORMAT RESULTS FILE *********************************************************************
# Produce two tab-delimited files from the supplied results file
def format_results(infile):
    check_file(infile)

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

def set_force_continue(option, opt_str, value, parser):
    """
    A callback for optparse
    """
    global qExitOpt
    qExitOpt = "AUTOCONTINUE"

def set_strict(option, opt_str, value, parser):
    """
    A callback for optparse
    """
    global qExitOpt
    qExitOpt = "AUTOFAIL"

# USER INTERFACE *********************************************************************

if __name__=="__main__":
    import sys
    from optparse import OptionParser

    usageStr= "\t%prog [PARAMETERS] INPUT_FILE OUTPUT_FILE\n" +\
          "or:\t %prog -c CONFIG_FILE [MORE PARAMETERS] [INPUT_FILE OUTPUT_FILE]\n" +\
          "or:\t %prog -O [RESULTS_FILE (default 'results')]\n" +\
          "or:\t %prog --help"
    parser = OptionParser(usage=usageStr,
                          description="IBEX Input File Converter: " +\
                                      "Converts a tab-delimited CSV file to a JavaScript input file " +\
                                      "for Ibex.\n",
                          epilog="Author: Andrew Wood <andywood@vt.edu>",
                          version="%prog 0.9.5")

    parser.add_option("-c", "--config", dest="configfile", default="default_cfg",
                  help="Use a custom config file")
    parser.add_option("-d", "--defaults", action="store_true", dest="defaults",
                  default=True, help="Use default in-out files")
    parser.add_option("-f", "--fillernormal", action="store_true", default=False,
                      dest="fillerin", help = "Treat Fillers as a normal item")
    parser.add_option("-F", "--force", action="callback", callback=set_force_continue,
                      help="Ignore warnings and continue")
    parser.add_option("-n", "--nothing", action="store_true", dest="doNothing", default=False,
                      help="Stop after parsing arguments")
    parser.add_option("-O", "--outputformat", action="store_true", dest="outputFmtMode", default=False,
                      help="Run in 'Format Output' mode: make the Ibex results file more readable")
    parser.add_option("-p", "--prompt", action="store_true", dest="prompt", default=False,
                      help="Prompt the user for any missing information")
    parser.add_option("-r", "--randomize", action="store_true", dest="randomize", default=False,
                      help="Randomize items of each type (don't use if you hard coded an ordering)")
    parser.add_option("-s", "--shuffle", action="store_true", dest="shuffle", default=False,
                      help="Shuffle (evenly space) the different types of items")
    parser.add_option("-S", "--strict", action="callback", callback=set_strict,
                      help="Strict: will automatically stop if an error is encountered")

    (options, args) = parser.parse_args()

    infile = None
    outfile = None
    if len(args) == 2:
        infile = args[0]
        outfile = args[1]
    else:
        if not options.prompt:
            parser.print_usage()
            sys.exit(-1)

    #format output mode
    if(options.outputFmtMode):
        if(infile):
            format_results(infile)
        else:
            format_results("results")
        sys.exit(0)

    orderChanged = False
    #handle defaults
    if not options.defaults:
        if(options.prompt): #(gather this info via command prompts)
            if(options.configfile == "default_cfg"):
                options.configfile = raw_input("Enter the name of your custom config file, or simply hit enter to continue with prompts:")
                if(options.configfile == ""):
                    options.configfile = "default_cfg"
            if(options.infile == None or configfile == "default_cfg"):
                options.infile = raw_input("Enter the name of your input file (required): ")
                check_file(options.infile)
            if(outfile == None or options.configfile == "default_cfg"):
                outfile = raw_input("Enter the desired output file name [data.js]: ")
                if(options.outfile == ""):
                    outfile="data.js"
            if(options.configfile == "default_cfg"):
                if( (raw_input("Evenly space different item types? \nUse this option unless you have specified an order for all items (y/n)")) == 'y'):
                    options.shuffle = True
                if( (raw_input("Randomize items? \nIMPORTANT: Only use this option if you did not specify an order! (y/n)")) == 'y'):
                    options.randomize = True
                if( (raw_input("Separate all items with a filler? If no, fillers are treated as normal items. (y/n)")) == 'n'):
                    options.fillerin = False

    if (options.randomize or options.shuffle):
        orderChanged = True

    dct = {}
    dct = parse_config_file(options.configfile)

    #figure out appropriate ordering variables
    if not options.fillerin:
        dct["filler"] = "SEP_EACH"
    else:
        dct["filler"] = "ITEM"

    if orderChanged:
        if options.shuffle:
            if options.randomize:
                dct["order"] = "RSHUFFLE"
            else: dct["order"] = "SHUFFLE"
        else:
            if options.randomize:
                dct["order"] = "RANDOMIZE"
            else:
                dct["order"] = "ORDERED"

    if infile == None:
        infile = dct["inputfile"];
    if outfile == None:
        outfile = dct["outputfile"];
    else:
        dct["outputfile"] = outfile;

    print dct

    header = generate_header_dct(dct)
    items = generate_item_str(infile)

    #debug the cmd-line processor
    if options.doNothing:
        print "doing nothing:\ninput_file: " +infile+ "\noutput_file: " +outfile+ \
        "\nconfig_file: " +str(options.configfile)+"\nOrderChanged? "+str(orderChanged) \
        +"\nShuffle? "+str(options.shuffle)+"\nRandomize? "+str(options.randomize)+"\nFiller as normal item? " \
        +str(not options.fillerin) +"\n\n"+header+"\n"+items
        sys.exit(0)
    else:
        create_outfile(outfile, header, items, "")
        try:
            import tab
            tab.replace(outfile)
        except ImportError:
            pass
