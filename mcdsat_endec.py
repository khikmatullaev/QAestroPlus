#!/usr/bin/python

import sys, getopt, re


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def invertdict(dictionary):
    """
    Invert keys and values of a dictionary
    """
    return {v: k for k, v in dictionary.iteritems()}


def getmapping(dictionary, key, isfunc=True):
    """
    Get the mappings of the variables
    If q is name of a function do not replace (restriction for query file)
    """
    if key == 'cost':
        return key
    if key == 'q' and isfunc:
        return key
    if key in dictionary:
        return dictionary[key]
    else:
        return key

def explode(s):
    """
    Get all function names and arguments from views
    """
    pattern = r'(\w[\w\d_]*)\((\w[\w\d,._ ]*)\)'
    match = re.findall(pattern, s)
    if match:
        return list(match)
    else:
        return []


def generate_mappings(inputf, mappingsf, mappingsConstFile):
    """
    Generate all mappings for encoding/decoding views and query files
    """
    ifile  = open(inputf, 'r')
    mfile  = open(mappingsf, 'w')
    mcfile = open(mappingsConstFile, 'w')
    
    # Get all function names and arguments
    views = []
    viewCosts = []
    funcs = []
    args = []
    tmp = []

    for line in ifile:
        match = explode(line)
        lineList = list(enumerate(match))

        lineView  = lineList.pop(0)
        lineConst = lineList.pop(-1)

        if lineView[1][0] not in views:
            views.append(lineView[1][0])

        if lineView[1][0] not in viewCosts:
            viewCosts.append(lineView[1][0] + ': ' +lineConst[1][1])

        for idx, pair in lineList:
            if pair[0] not in funcs:
                funcs.append(pair[0])
            for arg in pair[1].split(','):
                if arg not in args:
                    args.append(arg)

    # Produce the mappings for all functions and arguments
    viewmappings = {}
    for idx, view in enumerate(views):
        viewmappings[view] = 'v' + str(idx)

    funcmappings = {}
    for idx, func in enumerate(funcs):
        funcmappings[func] = 'r' + str(idx + 1)

    argmappings = {}
    for idx, arg in enumerate(args):
        argmappings[arg] = 'X' + str(idx + 1)

    # Merge all dictionaries
    mappings = merge_dicts(viewmappings, funcmappings, argmappings)
    
    # Write all mappings to a file
    # <mcdsatname> = <qaestro_name>
    for key, value in sorted(mappings.iteritems(), key=lambda (k, v): (v, k)):
        mfile.write(value + '=' + key + '\n')

    # Produce the mappings const for all views
    viewCostmappings = {}
    for idx, view in enumerate(viewCosts):
        viewCostmappings[view] = 'v' + str(idx)


    mappingsCost = merge_dicts(viewCostmappings)

    for key, value in sorted(mappingsCost .iteritems(), key=lambda (k, v): (v, k)):
        mcfile.write(value + '=' + key.split(':')[1] + '\n')

    # Close files
    ifile.close()
    mfile.close()
    mcfile.close()


def transform_file(inputf, mappingsf, outputf, encode=True):
    """
    Decode or encode qaestro <--> mcdsat
    """
    ifile = open(inputf, 'r')
    mfile = open(mappingsf, 'r')
    ofile = open(outputf, 'w')

    mappings = dict(line.strip().split('=') for line in mfile)
    if encode:
        mappings = invertdict(mappings)

    ifile = open(inputf, 'r')

    # Replace all strings
    lines = []
    for line in ifile:
        match = explode(line)
        view = ''
        if encode:
            for idx, pair in enumerate(match):
                if pair[0] != 'cost':
                    view += getmapping(mappings, pair[0]) + '(' + ','.join(getmapping(mappings, i, isfunc=False) for i in pair[1].split(',')) + ')'
                    if idx == 0:
                        view += ':- '
                    else:
                        view += ','
        else:
            for idx, pair in enumerate(match):
                view += getmapping(mappings, pair[0]) + '(' + ','.join(getmapping(mappings, i, isfunc=False) for i in pair[1].split(',')) + ')'
                if idx == 0:
                    view += ':- '
                else:
                    view += ','

        if match:
            lines.append(view[:-1])
        else:
            lines.append(line)

    # Write the file for mcdsat
    with open(outputf, 'aw') as file:
        for line in lines:
            file.write(line + '\n')
        file.close()

    # Close files
    ifile.close()
    mfile.close()


# Main method
def main(argv):
    inputfile = ''
    outputfile = ''
    mappingsfile = ''
    mappingsCostFile = ''
    action = ''

    try:
        opts, args = getopt.getopt(argv,"ha:i:m:c:o:",["action=","ifile=","mfile=", "-mcfile", "ofile="])
    except getopt.GetoptError:
        print('mcdsat_endec.py -a <action> -i <inputfile> -m <mappings> -mc <mappinsCost> -o <outputfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('mcdsat_endec.py -a <generate|encode|decode> -i <inputfile> -m <mappings> -o <outputfile>')
            sys.exit()
        elif opt in ("-a", "--action"):
            action = arg
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-m", "--mfile"):
            mappingsfile = arg
        elif opt in ("-c", "--mcfile"):
            mappingsCostFile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    if action == 'generate':
        generate_mappings(inputfile, mappingsfile, mappingsCostFile)
    elif action == 'encode':
        transform_file(inputfile, mappingsfile, outputfile)
    elif action == 'decode':
        transform_file(inputfile, mappingsfile, outputfile, False)

if __name__ == "__main__":
   main(sys.argv[1:])





