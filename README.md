# VisaS annotation pipeline
Preprocessing and annotation pipeline for the [VisaS project](https://wiki.studiumdigitale.uni-frankfurt.de/FB10_VisaS/index.php/Hauptseite).
This pipeline is used as a web service called by the [VisArgue](http://www.visargue.uni-konstanz.de/de/) server.
Web service functionality was implemented with [Flask](http://flask.pocoo.org/).

## The pipeline
The main file which contains the server functions is [app.py](./app.py). It contains the functions that are called
by the preprocessing step on the VisArgue server via routing HTTP requests. Please refer to the Flask documentation
for more information on this. The main method in *app.py* calls functions from [feature_extraction_pipeline.py](./feature_extraction_pipeline.py) to
get the annotations: 
- *get_all_annotations* calls the various helper functions to annotate all the features. 
- *convert* converts the input JSON structure into **POS tagged** files and **raw full text** files for each essay. The
input data is a JSON file sent from the VisArgue server. The JSON file consists of serialized Java objects:
    - *Discussions* (=essays) consisting of 
    - *Utterances* (=paragraphs) consisting of
    - *Sentences* consisting of 
    - *DiscourseUnits* consisting of
    - *Words*, which are the atomic units and containt the wordform and the POS tag (as Strings).
- Depending on which type of text data (POS-tagged or raw) is used, the feature extractions are called. So far
style features based on dictionaries are based on POS-tagged files and connectives are extracted from the raw full
text via the [PDTB-parser](https://wing.comp.nus.edu.sg/~linzihen/parser/).

For more information on how the feature extractions work please refer to the documentation within the Python files.

## Output format
The feature extraction function delivers two types of output which are combined into one JSON string in the end:
One is based on POS-tagged input (files that end with *_pos.txt*) and one that is based on raw text (files that
end with *_raw.txt*).
    - POS-tagged results:
These results are created when extracting features based on dictionaries (see below) and are listed per paragraph. 
Most of the features are in this format.

_Example:_

    "file1_pos": {"paragraph1": [ {"sentID": 47,"spanStart": 15,"spanEnd": 15,"tag": "reinforcement"},
                                  {"sentID": 21,"spanStart": 15,"spanEnd": 17,"tag": "hedging"},
                                   {...}
                                ],
                   "paragraph2": [ {"sentID": 7,"spanStart": 17,"spanEnd": 21,"tag": "reinforcement"},
                                    {...} 
                                 ]
                  },
    
    
   - raw text results:
These results are created when extracting features based on raw text input. For now only the connectors extracted
with the PDTB parser use this format (see [extract_connectors.py](./extract_connectors.py)). The results are stored in one list.

_Example:_

    "file1_raw": {"connectors": [ {"connective": "Furthermore",
                                    "type": "Expansion",
                                    "subtype": "Conjunction",
                                    "arg1": "This essay ...",
                                    "arg2": "it points out ..."
                                    },
                                  {"connective": "when",...} 
                                ]
                   }

While the two type of results use different tags, their structure is necessarily the same, as it needs to be
convertible to Java objects. For each essay two files are created, one *[essayname]_pos.txt* file and one 
*[essayname]_raw.txt* file. In the result list, each of these filenames is a separate entry containing all the
individual annotations in the format shown above.

## Feature extractions: feature_extraction_pipeline.py
 Feature extraction is based mostly on dictionaries which consist of regex-like entries. Entries may be n-grams of any length 
 consisting of any combination of lemmas, POS tags or lemmas with POS tags.
 These are the notation conventions for VisaS .dict files:
 
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
 

## Miscellaneous

### Ideas for prototype (3.5.18)

- topic recurrence (based on g-square and named entities, also topic shift/recurrence as in VisArgue) across paragraphs

- detect topic sentences

- keywords (provided dynamically)

- lower order errors (typos, grammar errors)

- matrix visualization (Toronto)

- Argumentation: gerunds, connectors, hedges

- Complexity: passives, sentence complexity

- Sophistication: hapax legomena

- Named entity graph/mind map/concept map similar to VisArgue


- Features: subsume again, rather and use of "to" under connectors
    - paired connectives, congruence of phrases ("on the one hand"+"on the other hand")

    - academic vs. colloquial language:
        - linguistic features (noun/verb ratio etc.)
        - phrases (Manchester phrase bank?)


### To Do


- For topic modelling remove author names (based on bibliography)

- Topic detection/modelling with WordNet:
    The algorithm based on WordNet similarities definitely works better than the one based on conceptual similiarity.
    The following parameters should be tested:
    - lesk disambiguation verbessern indem ganze Sätze genommen werden?
  
 - Topic detection with Word2Vec similarities:
    - normalization seems to help, a small threshold too
    - thresholds between 0.2 and 0.3 seems to work best
    