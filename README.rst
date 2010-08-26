========================
Readme for csv2ibex.py 
========================

:Author:
  Andrew Wood
:Email:
  <andywood@vt.edu>
:Last Edited:
  8/9/2010

csv2ibex
========

csv2ibex is a Python script to convert a tab-delimited CSV file to a Javascript input file for  `Ibex <http://github.com/addrummond/ibex>`_ (Internet Based EXperiments).  It can also be used to format the results file obtained from Ibex.  Complete documentation for Ibex, including how to host your own server and the format of the JS input files, is available at http://code.google.com/p/webspr/wiki/Documentation03.

Running the Script
------------------
To run the csv2ibex script, type "python csv2ibex.py" followed by any command line parameters ("-rs", etc).  If you use '-c' enter the name of the your custom configuration file followed optionally by the input CSV file and desired output file.  If you use '-O' enter the name of the results file, or alternatively, nothing to use the default result filename.  Otherwise, enter the name of your input CSV and your desired output file name.

Usage
~~~~~
normal::

  python csv2ibex.py [command line params] INPUT_FILE OUTPUT_FILE

custom config file::

  python csv2ibex.py -c [more cmd line params] CONFIG_FILE [INPUT_FILE OUTPUT_FILE]

default config file::

  python csv2ibes.py -d 

results formatting::

  python csv2ibex.py -O [RESULTS_FILE]

Command Line Parameters
~~~~~~~~~~~~~~~~~~~~~~~
This script uses command line parameters in the UNIX style. That is, you may enter a '-' character followed by a letter to indicate some command. Multiple commands may be entered either all together ("-abc") or separately ("-a -b -c").  A list of command line options is as follows:

 * c - run in custom config mode.  Expects the name of a configuration file.

  * example: "python csv2ibex.py -c my_cfg" would tell the script to run using your config file "my_cfg"

 * d - run in default mode (according to the settings in "default_cfg")
 * f - Treat fillers as normal items (see the section "VARS" in "Customizing the Config File")
 * O - (capital 'o'). Output format mode, ie. takes in a results file and outputs more readable CSV files
 * p - Prompt for the items not given on the command line (config file, input/output, ordering)
 * r - Randomize items (see the section "VARS" in "Customizing the Config File")
 * s - Shuffle items (see the section "VARS" in "Customizing the Config File")


The CSV Input File
------------------
Csv2ibex expects a tab-delimited CSV file with certain data columns in no particular order (any extra columns are simply ignored).  The script offers a great deal of flexibility depending on what columns are included and their content. The expected columns are below. They must be named exactly as shown to be recognized, and since all but 'Stimulus' are optional, the script may produce unexpected output if the columns are missnamed.

To avoid confusion, I will use the term 'item' to refer to a row (single entry) in the CSV file.

An example CSV file is available at (./Examples/example_script_input.csv)

'Stimulus' (Required)
~~~~~~~~~~~~~~~~~~~~~
This column contains the sentence you would like to be displayed, shown exactly as you would like it to show up on the screen. If this column is not present, the script will print an error and halt. 

Here is an example without region tagging (everything inside the quotes would be the cell entry)::

  "The horse jumped over the fence."

Ibex (through a modified controller) can also handle region labeling. To tag a word, simply place an '@' character immediately after the word followed by the tag name. Tags are not displayed to the subjects, but show up in the results files. The following example would appear identical to the previous one::

  "The horse@subj jumped@vrb over@prep the fence@obj"

'List'
~~~~~~
This column and all following are optional.  'List' is a numeric (integer) value indicating which list the particular item belongs.  Subjects are assigned to a list in a logical manner by the Ibex server (ie 1,2,3,1,2,3,...) and only see items that belong to that list.  Items with type "filler" or "practice" are constant across all lists, so the number here will only affect where those items appear in the JS file.

If the 'List' column is ommitted, the default behavior is to assign everything that isn't a filler or practice item to the same list.

For example, if you want an item to be in list three, the entry would be "3" 

'Type'
~~~~~~
This column is largely unnecessary, but can be used to indicate "critical" versus "filler" or "practice" items.  If not present, all items type is whatever is in the "Condition" column.

'Condition'
~~~~~~~~~~~
The 'Condition' column identifies what condition the current item falls under.  This is important for ordering as well as identifying lines in the results files.  Reserved conditions are "filler" and "practice" which have special behavior.  Other than those two types, you may use any string to identify a kind of stimuli.

Say you were trying to identify the tense of a sentence; you might use "pastperfect" or something similar.

If the 'Condition' column is ommitted, the default is to assign everything to the "defaultStim" type/condition.

'Order'
~~~~~~~
If you wanted to specify a specific ordering, include this column.  Entries should be a numeric (integer) value indicating the order you'd like the stimuli to appear in (not necessarily in order).  For example, "3" would appear before "5" but after "2".  Since subjects will only see items that are in the same list, you can use the same 'Order' number in different lists, but there should only be one of each number per list. 

Practice items always appear first, but in the order you specify.

NOTE: Remember to run the script without the -r or -s flags or to use a config file with 'order:ORDERED', or the order specified here will be ignored and the items may be randomized/shuffled depending on your config/command flag settings. If you want to specify the order of filler items set the 'filler:ITEM' option or run the script with the -f flag.

If there is no 'Order' specified, items will appear in the same order they do in the CSV file.  If the field is blank, it will assign a number (not recommended).

'QuestionN'
~~~~~~~~~~~
This column contains a comprehension question to go with the stimulus.  It should be formatted exactly as you'd like it to appear, and there should be an entry in the corresponding 'Answer' field (or the question won't display).

If there is no 'Question' column or it (or its corresponding 'Answer') is blank for an item, the experiment simply moves on to the next item.

There may be arbitrarily many question and answer columns so long as they follow in order (ie 1,2,3,...,n).

'AnswerN'
~~~~~~~~~
This indicates both the correct answer and the answer choices for the given question. 

In the case of a yes/no question it is sufficient to simply put a "Y" or "N" in the field, indicating the correct answer.  In the case of a multiple choice question, include all of the options separated by commas, with the correct answer first. For example, say the question is "Which is a primary paint color?" and the desired options were "orange," "purple," and "yellow." The correct answer is "yellow," so the entry in the 'Answer' field would be "yellow,orange,purple."  The options will be displayed in random order, so it only matters that the correct answer is first.


Customizing the Config File
---------------------------
The csv2ibex script makes use of a configuration file for all of its defaults.  Users may create custom configuration files to reflect the needs of their particular experiments.  It is recommended that you create a copy of the default_cfg file rather than editing it directly, passing the new file as an option when you call the script.

The configuration file is made up of white space, comments (lines that start with '#'), and variable assignments of the format 'variable_name : value'.  White space (spaces, tabs, newlines) and comments are ignored, except that each variable assignment must be on its own line.  For the most part the order of the assignments does not matter.  The exceptions is the section headers "VARS:" and "DEFAULTS:" which contain specific types of variables.

VARS (csv2ibex script defaults)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This section contains several variables which control how the script executes:

inputfile : <name of the default input file, which will be overwritten if a file is given at command line>

outputfile: <name of default output file>

order : < ORDERED, SHUFFLE, RANDOMIZE, or RSHUFFLE (described below) >

 * ORDERED - the default setting (equivalent to neither -r or -s).  Items will be ordered as they appear in the input file (ie. how they are specified in the 'Order' field of your input CSV)
 * SHUFFLE - Items will be shuffled (aka evenly spaced)(equivalent to -s).  This means that Ibex will try to order the items such that a subject sees each type of item at regular intervals. Relative ordering among items of the same type are preserved.  For example, say you have three types: "a," "b," and "c," and your list of items is (a1, a2, ..., b1, b2, ..., c1, c2, ...) where "..." means "and so on."  With the SHUFFLE option, the final ordering would be (a1, b1, c1, a2, b2, c2, ...).
 * RANDOMIZE - Items will be randomized (equivalent to -r).  That is, items of each type will be randomized, but the ordering of types will be preserved.  For example, suppose you have the same types and initial ordering as above.  The output ordering would be (randomized items of "a", randomized items of "b", randomized items of "c").  A more specific possible example: (a1, a3, a2, b2, b1, b3, c1, c3, c2).
 * RSHUFFLE - Items will be both shuffled and randomized (equivalent to -rs). 

filler : <SEP_ALL or ITEM>

 * SEP_ALL - fillers are shuffled with items, that is, fillers and non-filler, non-practice items will be shuffled/evenly spaced (filler, non-filler, filler, ...).
 * ITEM - fillers are treated as normal items (equiv to -f option) for the purposes of ordering and are subject to whatever rule you chose for the 'order' variable above.

DEFAULTS (Ibex controller defaults)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This section details the defaults for the various item controllers.  The format of this section is as follows (white space is just for ease of read):: 

  <Controller1 Name>:
    <Controller1,Parameter1 Name> : <Controller1,Parameter1 Value>
    ...
  <Controller2 Name>:
    <Controller2,Parameter1 Name> : <Controller2,Parameter1 Value>
    ...
  ...

The parameters are exactly as found in the Ibex Documentation.  See the default_cfg for some examples.
