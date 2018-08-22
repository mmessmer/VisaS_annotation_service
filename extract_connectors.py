import os
import shutil
import subprocess


def extract_connectors(textfile):
    """
    This function uses the PDTB-parser to read a text file and extract the connective as well as their arguments
    in a VisArgue compliant format. The output of the PDTB-parser (pipe-file) is read and transformed into a
    dictionary with the necessary fields: connective, type, subtype, arg1-span and arg2-span.
    This function was originally written by Leo Vrana and modified by Moritz Messmer
    :param textfile:
    :return:
    """
    markups = []
    connector_matches = []

    # Go to directorys of pdtb-parser and run the jar file.
    #   Note by Moritz: I had to slightly modify the parser so it doesn't attempt to extract
    #   implicit connectors (which didn't work anyways), this led to some problems. The modified
    #   version is in the 'parser-explicit.jar' file
    os.chdir("pdtb-parser/")
    subprocess.run(["java", "-jar", "parser-explicit.jar", "../" + textfile], stdout=subprocess.PIPE)

    # Output shows up in "./pdtb_output/" + file + ".pipe"
    pipefile = textfile.replace("temp/", "../temp/output/") + ".pipe"
    parsed = open(pipefile, 'r', encoding="utf-8", errors="replace")

    # The output of the parser is 47(?) fields separated by pipes. Only
    # a few of these are useful.
    pipes = parsed.readlines()

    # Why not.
    parsed.close()

    #Separate out the fields to get the important ones.
    matches = []

    for line in pipes:
        matches.append(line.split("|"))

    # We will now take the entries which will be marked up in the final
    # visualization.
    for m in matches:
        # [0] is explicit, only use those.
        # [3] is the span of the connector in the file.
        # [5] is the raw text,
        # [7] is the sentence number,
        # [22] is Arg1 Spanlist,
        # [24] is arg1 raw text,
        # [32] is arg2 spanlist,
        # [34] is arg2 raw text,
        # [11] is the name of the connector type.
        # [12] is supposed to be the subclass but nothing is showing up.

        # Don't want to use implicit connectors, the accuracy is
        # much worse.
        if m[0] == 'Explicit':
            types = m[11].split('.')
            markups.append([m[5], m[3], m[7], m[22], m[24], m[32], m[34], types[0], types[1]])


    for entry in markups:

        index = []

        # Some connectors like "if...then..." work in concert and are
        # split over multiple spans.
        if ";" in entry[1]:
            separated = entry[1].split(";")
            for mult_entry in separated:
                conn_index = (mult_entry.split(".."))
                #This gets the span back in contents. Yiss.
                #print(contents[int(mult_entry[0]):int(mult_entry[1])])
                conn_index = [int(i) for i in conn_index]
                conn_index = tuple(conn_index)
                index.append(conn_index)


        else:
            conn_index = entry[1].split("..")
            conn_index = [int(i) for i in conn_index]
            conn_index = tuple(conn_index)
            index.append(conn_index)

        entry[1] = index

        # Some arguments are also split over spans.
        arg_1_index = []
        if ";" in entry[3]:
            separated_arg = entry[3].split(";")
            for mult_entry in separated_arg:
                arg_index =(mult_entry.split(".."))
                arg_index = [int(i) for i in arg_index]
                arg_index = tuple(arg_index)
                arg_1_index.append(arg_index)
                #This gets the span back in contents. Yiss.
                #print(contents[int(mult_entry[0]):int(mult_entry[1])])
        else:
            arg_index = entry[3].split("..")
            arg_index = [int(i) for i in arg_index]
            arg_1_index.append(tuple(arg_index))

        entry[3] = arg_1_index

        arg_2_index = []
        if ";" in entry[5]:
            separated_arg_2 = entry[5].split(";")
            for mult_entry in separated_arg_2:
                arg_index =(mult_entry.split(".."))
                arg_index = [int(i) for i in arg_index]
                arg_index = tuple(arg_index)
                arg_2_index.append(arg_index)

                #This gets the span back in contents. Yiss.
                #print(contents[int(mult_entry[0]):int(mult_entry[1])])
        else:
            arg_index = entry[5].split("..")
            arg_index = [int(i) for i in arg_index]
            arg_2_index.append(tuple(arg_index))


        entry[5] = arg_2_index


    # Sort all of the markups by start location.
    #markups.sort(key=lambda x: (x[1][0]))
    for m in markups:
        #match_text = m[4] + ' [' + m[0] + '] ' + m[6]
        conn_match = {'connective': m[0], 'type': m[7], 'subtype': m[8], 'arg1': m[4], 'arg2': m[6]}
        connector_matches.append(conn_match)

    # Go back to the parent directory and delete all temporary files from the PDTB-parser
    os.chdir("..")
    shutil.rmtree("temp/output/")

    return connector_matches



#connectors = extract_connectors("test.txt")

