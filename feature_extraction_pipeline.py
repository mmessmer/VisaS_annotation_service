"""
This file contains several functions for extracting linguistic features from VisArgue Discussion objects.
The input for the pipeline is a list of VisArgue Discussion objects, serialized to JSON. The JSON string is
first converted and saved into temporary POS-tagged text files with convert(). The POS text file is then
used for linguistic feature extractions based on dictionaries in get_feature_tag_for_file().
Dictionaries have a special syntax (see doc below) and are read in with read_feature_dict.
"""
import os,re
import json
import logging
from extract_connectors import extract_connectors


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


def convert(file):
    """
    Convert an JSON file to a POS text file. The XML file is created in VisArgue (class StyleFeatureManager)
    and is a serialized version of a list of Discussions (= essays). Each essay has the structure:
    utterances(=paragraph) > sentences > discourseUnits > words. The POS text file contains sentences consisting of
    words in the following format:
    <sentence ID>.<word ID>.<lexeme>_<POS tag>
    Each sentence is in one line and paragraph splits are marked by an empty line.
    The output is written into a "_pos.txt" file
    :param file: Input file in JSON format
    """
    outfile = file.replace(".json","_pos.txt")
    essays_string = open("temp/" + file,encoding='utf-8', errors='ignore').read()
    essays = json.loads(essays_string)

    for essay in essays:
        with open("temp/" + str(essay['id']) + "_pos.txt", 'w', encoding='utf-8') as posfile, \
                open("temp/" + str(essay['id']) + "_raw.txt", 'w', encoding='utf-8') as txtfile:
            sentID = 0
            for paragraph in essay['utterances']:
                for sentence in paragraph['sentences']:
                    sentID += 1
                    wordID = 0
                    for discourse_unit in sentence['discourseUnits']:
                        for word in discourse_unit['words']:
                            wordID += 1
                            if word['wordform'] is not ' ':
                                posfile.write(str(sentID) + "." + str(wordID) + ":" + word['wordform'] + "_" + word['posTagLabel'] + " ")
                            txtfile.write(word['wordform'])
                    posfile.write("\n")
                    txtfile.write("\n")
                posfile.write("\n")
                txtfile.write("\n")

# Old code: read XML file. Not used anymore because XML files have issues with characters like ' and &
    # parser = XMLParser(recover=True)
    # tree = parser.parse(file)
    # root = tree.getroot()
    # if not os.path.exists(IN + outfile):
    #     for essay in root.iter("item"):
    #         with open("temp/" + essay.find("name").text + "_pos.txt", 'w', encoding='utf-8') as outf:
    #             sentID = 0
    #             for paragraph in root.iter("utterance"):
    #                 for sentence in paragraph.iter("sentence"):
    #                     sentID += 1
    #                     wordID = 0
    #                     for word in sentence.iter("word"):
    #                         wordID += 1
    #                         outf.write(str(sentID) + "." + str(wordID) + "." + word.find("wordform").text + "_" + word.attrib["posTagLabel"] + " ")
    #                     outf.write("\n")
    #                 outf.write("\n")



def read_feature_dict(path):
    """
    Read a .dict file and create regex patterns for extracting and annotating features.

    Please note the conventions for VisaS .dict files:
    LEMMA       - a token with a simple lemma
    NOTE: several plain lemmas may be concatenated in a regex: (LEMMA1|LEMMA2|...)
    _POS        - a token with a POS tag
    LEMMA_POS   - a token with lemma and POS tag
    #COMMENT    - a comment line that will be ignored
    (TOKEN)?    - an optional token
    (TOKEN)*    - zero or more of TOKEN
    (TOKEN)+    - one or more of TOKEN
    ...         - one or more tokens of any kind
    Tokens themselves may contain any regex operators within.
    Several tokens can be written in one line, separated by whitespaces

    :param path: the path of the .dict file to be read
    """
    feature_dict = []
    with open(path, 'r', encoding='utf-8') as dictfile:
        for line in dictfile:
            if line.lstrip(' \t').startswith('#'):
                # This line is a comment line, ignore it
                continue
            else:
                # This line contains one or more tokens, split them up and wrap them in the format for VisaS POS files.
                tokens = line.rstrip(' \t\n').rstrip(' \t').split()
                dict_tokens = ""
                for token in tokens:
                    quantifier = ""
                    if re.match("\(.+\)([?*+])",token):
                        quantifier = re.match("\(.+\)([?*+])",token).group(1)
                        token = token.lstrip('(').rstrip(')?*+')
                    if '_' in token:
                        if token.startswith('_'):
                            # token starts with '_' and is a POS tag
                            if quantifier:
                                dict_tokens = dict_tokens + "(?:(\d+)\.(\d+):\S+?_" + token.lstrip('_').replace("(","(?:") + " )" + quantifier
                            else:
                                dict_tokens = dict_tokens + "(\d+)\.(\d+):\S+?_" + token.lstrip('_').replace("(","(?:") + " "
                        else:
                            try:
                                # token is a lemma with POS tag attached, split the lemma and pos tag
                                pos_token = token.split('_')
                                if quantifier:
                                    dict_tokens = dict_tokens + "(?:(\d+)\.(\d+):" + pos_token[0].replace("(","(?:") + "_" + pos_token[1].replace("(","(?:") + " )" + quantifier
                                else:
                                    dict_tokens = dict_tokens + "(\d+)\.(\d+):" + pos_token[0].replace("(","(?:") + "_" + pos_token[1].replace("(","(?:") + " "

                            except IndexError:
                                print("Warning! Invalid token found in line '" + line + "'")
                    elif token == '...':
                        # ... is converted to one or more arbitrary tokens
                        dict_tokens = dict_tokens + "(?:(\d+)\.(\d+):\S+_\S+? )+"
                    else:
                        # token is a lemma without POS tag
                        if quantifier:
                            dict_tokens = dict_tokens + "(?:(\d+)\.(\d+):" + token.replace("(", "(?:") + "_\S+? )" + quantifier
                        else:
                            dict_tokens = dict_tokens + "(\d+)\.(\d+):" + token.replace("(", "(?:") + "_\S+? "
                if dict_tokens:
                    feature_dict.append(dict_tokens)
    if len(feature_dict) is 0:
        print("Warning! No valid entries found in dictionary " + path)
        return None
    else:
        return feature_dict


def get_annotation(file, pos_dict, ex_dict, tag):
    """"
    Finds and extracts the patterns given in pos_dict from the input file. Matches that coincide with ex_dict
    are excluded. The tag parameter is the name of the feature. Results are stored into a list where each
    entry stores the position for each match along with the feature tag.
    Each result is a tuple of the form (<sentID>,<startLexemeID>,<endLexemeID>,<tag>).
    :param pos_dict: Dictionary for positive matches. Must be in appropriate format as output
                     by read_feature_dict
    :param ex_dict: Dictionary for negative matches that are excluded from the results.
                    Must be in appropriate format as output by read_feature_dict
    :param tag: Tag that is used for this feature.
    :return List of result tuples
    """
    results = {}
    with open(file, 'r', encoding='utf-8') as f:
        par = 0
        par_results = []
        for line in f:
            if line is "\n":
                if par_results:
                    if "paragraph" + str(par) in results:
                        results["paragraph" + str(par)].append(par_results)
                    else:
                        results["paragraph" + str(par)] = par_results
                par += 1
                par_results = []
                continue
            for q in pos_dict:
                qmatches = re.finditer(q, line, re.I)
                for qmatch in qmatches:
                    exclude = 0
                    for exItem in ex_dict:
                        exMatches = re.finditer(exItem.rstrip('\n'), line, re.I)
                        for exMatch in exMatches:
                            if exMatch and qmatch.start(1) is exMatch.start(1):
                                exclude = 1
                    # Save result to list of results with appropriate tag
                    if (qmatch and exclude is 0):
                        try:
                            #results.append((int(qmatch.group(1)),int(qmatch.group(2)), int(qmatch.group(len(qmatch.groups()))), tag))
                            par_results.append({"sentID": int(qmatch.group(1)), "spanStart":int(qmatch.group(2)), "spanEnd":int(qmatch.group(len(qmatch.groups()))), "tag": tag})
                        except TypeError:
                            # TypeErrors are usually raised when one of the capture groups of fields is empty (NoneType)
                            # Simply throw a warning message and keep going
                            print("Warning! Something went wrong while matching expression'" + q + "' in line '" + line[0:50] + "...'")
        return results


def get_paired_connectors(file):
    results = []
    connectors = [
        ("(\d+)\.(\d+):(both)_\S+?","(\d+)\.(\d+):(and)_\S+?")
    ]


def get_all_annotations(filename,log):
    """
        This is the main function for annotating all features to one file. It calls get_pattern_from_file
        to collect and concatenate the result list for each individual feature. The results are then returned
        as a dictionary (keys: input file names) with each key containing a dictionary which in turn contains a list of
        dictionaries which are the actual results. These results dictionaries must contain string keys and values.
        e.g.
        {"file1_pos": {"paragraph1": [ {"sentID": 47,"spanStart": 15,"spanEnd": 15,"tag": "reinforcement"},
                                        {...}],
                       "paragraph2": [ {"sentID": 7,"spanStart": 17,"spanEnd": 21,"tag": "reinforcement"},
                                        {...} ]},
         "file1_raw": {"connectors": [ {"connective": "Furthermore",
                                        "type": "Expansion",
                                        "subtype": "Conjunction",
                                        "arg1": "This essay ...",
                                        "arg2": "it points out ..."
                                        },
                                        {"connective": "when",...} ]
                       }
        }

        This structure must be kept, because it is converted into a Java data structure with strict typing!
        Changes to the structure of the results must therefore also be done in the VisArgue code
        :param filename: A text file (raw text or POS tagged) containing the essay to be analyzed
        """
    results = {}
    log.info("Creating POS-tagged files and raw text files for '{}'".format(filename))
    # call function to creat a POS file (into directory ./output/POS by default)
    convert(filename)

    # Do annotations in POS tagged files
    for filename in os.listdir("temp/"):
        fileresults = {}

        # Do annotations in POS tagged files
        if filename.endswith("_pos.txt"):
            posfile = "temp/" + filename

            log.info("Extracting features from file '{}'".format(posfile))

            # Do extraction and annotation step for each feature
            # Results are dictionaries of lists that are merged with a helper function
            fileresults = merge_results(fileresults, get_annotation(posfile, evaluative_dict, [], "evaluative"))
            fileresults = merge_results(fileresults, get_annotation(posfile, reinforcement_dict, reinforcement_exclude_dict, "reinforcement"))
            fileresults = merge_results(fileresults, get_annotation(posfile, hedging_dict, hedging_exclude_dict, "hedging"))
            fileresults = merge_results(fileresults, get_annotation(posfile, quant_dict, quant_exclude_dict, "quantifier"))

            # Add connectors as provided by Iverina and Janina's lists
            fileresults = merge_results(fileresults, get_annotation(posfile, conn_argumentation_dict, [], "conn.argumentation"))
            fileresults = merge_results(fileresults, get_annotation(posfile, conn_concluding_dict, [], "conn.concluding"))
            fileresults = merge_results(fileresults, get_annotation(posfile, conn_exemplification_dict, [], "conn.exemplification"))
            fileresults = merge_results(fileresults, get_annotation(posfile, conn_listing_dict, [], "conn.listing"))
            fileresults = merge_results(fileresults, get_annotation(posfile, conn_paired_dict, [], "conn.paired"))

            os.remove(posfile)


        # Do annotations in raw text files without POS tags
        elif filename.endswith("_raw.txt"):
            fulltxtfile = "temp/" + filename

            log.info("Extracting features from file '{}'".format(fulltxtfile))

            # Add connectors based on PDTB-parser
            connectors = extract_connectors(fulltxtfile)
            fileresults['connectors'] = connectors

            os.remove(fulltxtfile)

        if fileresults:
            results[filename.rstrip(".txt")] = fileresults

    log.info("Finished annotations for file '{}'".format(filename))
    #print(json.dumps(results, indent=True))
    return results


def merge_results(res1, res2):
    """
    A helper method for merging two dictionaries of lists, as the lists would otherwise be
    overwritten.
    :param res1: dictionary 1
    :param res2: dictionary 2
    :return: The merged dictionary
    """
    empty = []
    keys = set(res1).union(res2)
    return dict((k, res1.get(k, empty) + res2.get(k, empty)) for k in keys)


# Initialize dictionaries:
#quantifiers
quant_dict = read_feature_dict("wordlists/quantifiers.dict")
quant_exclude_dict = read_feature_dict("wordlists/quantifiers_exclude.dict")

#hedging
hedging_dict = read_feature_dict("wordlists/hedging.dict")
hedging_exclude_dict = read_feature_dict("wordlists/hedging_exclude.dict")

#reinforcement
reinforcement_dict = read_feature_dict("wordlists/reinforcement.dict")
reinforcement_exclude_dict = read_feature_dict("wordlists/reinforcement_exclude.dict")

#evaluative
evaluative_dict = read_feature_dict("wordlists/evaluative_expressions.dict")

#connectors
conn_argumentation_dict = read_feature_dict("wordlists/connectors_argumentation.dict")
conn_concluding_dict = read_feature_dict("wordlists/connectors_concluding.dict")
conn_exemplification_dict = read_feature_dict("wordlists/connectors_exemplification.dict")
conn_listing_dict = read_feature_dict("wordlists/connectors_listing.dict")
conn_paired_dict = read_feature_dict("wordlists/connectors_paired.dict")
