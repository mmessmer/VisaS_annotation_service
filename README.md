# VisaS annotation pipeline
Preprocessing and annotation pipeline for the [VisaS project](http://www.visargue.uni-konstanz.de/de/).
This pipeline is used as a web service called by the VisArgue server.
Web service functionality was implemented with [Flask](http://flask.pocoo.org/).

## The pipeline
The main file which contains the server functions is [app.py](./app.py). It contains the functions that are called
by the preprocessing step on the VisArgue server via routing HTTP requests. Please refer to the Flask documentation
for more information on this. The main method in *app.py* calls functions from *feature_extraction_pipeline.py* to
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



## Feature extractions: feature_extraction_pipeline.py
 Feature extraction is based mostly on dictionaries which consist of regex-like entries. Entries may be n-grams of any length 
 consisting of any combination of lemmas, POS tags or lemmas with POS tags. The dictionaries are usually in the
 *wordlists* folder.
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
 



## Ideas for prototype (3.5.)

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

    - Academic vs. colloquial lingo:
        - linguistic features (noun/verb ratio etc.)
        - phrases (Manchester phrase bank?)


## To Do

- Flask needs to use authentification: MongoDB server has authentification,
needs to be hooked up to Flask

- Check encoding, so that apostrophes are handled properly
    - also check why the \ufeff byte isn't removed properly

- For topic modelling remove author names (based on bibliography)

- Topic detection/modelling with WordNet:
    The algorithm based on WordNet similarities definitely works better than the one based on conceptual similiarity.
    The following parameters should be tested:
    - lesk disambiguation verbessern indem ganze Sätze genommen werden?
  
 - Topic detection with Word2Vec similarities:
    - normalization seems to help, a small threshold too
    - thresholds between 0.2 and 0.3 seems to work best
    