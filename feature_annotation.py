"""
This file contains functions for annotating DU-XML files and collecting results in a CSV file,
 based on the patterns extracted in feature_extraction_pipeline.py.
 It is currently not needed for the VisArgue service.
"""
import os, re
import xml.etree.ElementTree as ET
from feature_extraction_pipeline import convert, get_annotation

IN = "output/temp/"
POS = "output/POS/"
EXTRACTED = "output/extracted/"


#Not used anymore
#TODO find appropriate tags for n-gram matches
#TODO adapt new XML format (no IDs anymore)
#so far they all have the same tag, but for the visualization it might make
#more sense to specify the start and end of the n-gram
def annotate_du_file(xmlfile,results):
    """
    Takes a list of results as created by method get_pattern_from_file() and annotates the input file
    with the respective tag given for each result.
    :param file: DU file to be annotated. Need to be in the VisArgue/VisaS DU XML format
    :param results: List of result tuples containing the location of a match and its feature tag
    """
    outfile = xmlfile.replace(".xml", "_visasAnnot_temp.xml")
    tree = ET.parse(IN + xmlfile)
    root = tree.getroot()
    sentID = 0
    for par in root.iter("utterance"):
        for sent in par:
            sentID += 1
            remove_results = []
            for result in results:
                if sentID is result[0]:
                    wordID = 0
                    for lexeme in sent.iter('word'):
                        wordID += 1
                        if result[1] <= wordID <= result[2]:
                            lexeme.set('ling_feature',result[3])
                            remove_results.append(result)
            for r in remove_results:
                if r in results:
                    results.remove(r)

    tree.write(IN + "annotated/" + outfile)



def annotate_pattern(pos_dict,ex_dict,tag):
    """
    Finds and extracts the patterns given in pos_dict from all essay files. Matches that coincide with ex_dict
    are excluded. The tag parameter is the name of the feature. Results are stored into a list where each
    entry stores the position for each match along with the feature tag.
    Each result is a tuple of the form (<sentID>,<startLexemeID>,<endLexemeID>,<tag>).
    These results are then added to the DU files by calling annotate_du_file()
    :param pos_dict: Dictionary for positive matches. Must be in appropriate format as output
                     by read_feature_dict
    :param ex_dict: Dictionary for negative matches that are excluded from the results.
                    Must be in appropriate format as output by read_feature_dict
    :param tag: Tag that is used for this feature.
    """
    for dufile in os.listdir(IN):
        if dufile.endswith("_parsed.xml"):
            # call function to creat a POS file (into directory ./output/POS by default)
            convert(IN + dufile)
            posfile = dufile.replace("_parsed.xml", "_pos.txt")
            # Do extraction and annotation step for each feature
            results = get_annotation(posfile, pos_dict, ex_dict, tag)
            print("results for file " +dufile + " :" + str(results))

            # Annotate results to du_file
            annotate_du_file(dufile,results)


def extract_pattern(pos_dict,ex_dict,tag):
    """
    Finds and extracts the patterns given in pos_dict from all essay files. Matches that coincide with ex_dict
    are excluded. The tag parameter is the name of the feature and also the name of the output CSV file
    :param pos_dict: Dictionary for positive matches. Must be in appropriate format as output
                     by read_feature_dict
    :param ex_dict: Dictionary for negative matches that are excluded from the results.
                    Must be in appropriate format as output by read_feature_dict
    :param tag: Tag that is used for this feature and for naming the CSV output file, e.g. "hedging.csv"
    """
    output = open(EXTRACTED + tag + ".csv", 'w', encoding='utf-8')
    for dufile in os.listdir(IN):
        if dufile.endswith("_parsed.xml"):
            # call function to creat a POS file (into directory ./output/POS by default)
            convert(IN + dufile)
            posfile = dufile.replace("_parsed.xml", "_pos.txt")
            # Do extraction and annotation step for each feature
            extract_pattern_from_file(posfile,pos_dict,ex_dict,tag,output)
    output.close()
    print("Done extracting " + tag + "--------------------------------------\n")



def extract_pattern_from_file(file,pos_dict,ex_dict,tag,output):
    """
    Goes through a POS file and checks for dictionary matches. Each match with the positive
    dictionary is checked against the negative dictionary. If the positive match coincides
    with a negative match it is excluded from the results. Results are saved are written into
    the output file along with the file name, sentence number and context of the match.

    :param file: The file to be checked for matches. Must be in VisaS POS format
    :param pos_dict: Dictionary for positive matches. Must be in appropriate format as output
                     by read_feature_dict
    :param ex_dict: Dictionary for negative matches that are excluded from the results.
                    Must be in appropriate format as output by read_feature_dict
    :param tag: The tag for this feature. Is added to the output file.
    :param output: The output CSV file into which the results are written, separated by tabstops
    """
    if file.endswith("_pos.txt"):
        with open(POS + file, 'r', encoding='utf-8') as f:
            for line in f:
                for entry in pos_dict:
                    # For each entry find all occurrences in this sentence
                    matches = re.finditer(entry, line, re.I)
                    for match in matches:
                        exclude = 0
                        for exItem in ex_dict:
                            exMatches = re.finditer(exItem.rstrip('\n'), line, re.I)
                            for exMatch in exMatches:
                                # Check if positive match is within range of exclusion match, as the exclusion
                                # may contain additional context
                                if exMatch and (exMatch.start() <= match.start(1) <= exMatch.end()):
                                    exclude = 1
                        # Save result to list of results with appropriate tag
                        if match and exclude is 0:
                            # Print match with context
                            pre, post, m = "", "", ""
                            for w in line[0:match.start()].split():
                                pre = pre + w.rsplit("_")[0].split(":")[1] + " "
                            for w in line[match.end():].split():
                                if w.startswith("_"):
                                    continue
                                post = post + w.rsplit("_")[0].split(":")[1] + " "
                            for w in match.group(0).split():
                                m = m + w.rsplit("_")[0].split(":")[1] + " "
                            print(file + " | sent. " + match.group(1) + ": \t" + pre + "\t"
                                  + m + " \t" + post + "\t" + tag + "\n")
                            output.write(file + " | sent. " + match.group(1) + ": \t" + pre + "\t"
                                         + m + " \t" + post + "\t" + tag + "\n")