"""
This file manages the Python flask server and all interaction with the VisArgue server.
The get_and_annotate_essays method does all the work, basically. It is called from the VisArgue server
with a POST request and takes the raw essays as a JSON string from the POST request body.
All annotation steps are then executed and the resulting JSON containing all result matches is sent back
to the server.
"""
import os
import time, hashlib
import logging

import pymongo
from pymongo import MongoClient
from flask import Flask, jsonify, request
from feature_extraction_pipeline import get_all_annotations
import unicodedata
import urllib.parse

app = Flask(__name__)
log = logging.getLogger(__name__)

# The magic key used in VisArgue to create authentication tokens
MAGIC_KEY = "obfuscate"
json_temp = "temp/essays_temp_parsed.json"

@app.route("/test")
def test():
    print("This is a server test and should return Hello World.")
    return "Hello world!!!!!!"


@app.route('/annotate', methods=['POST'])
def get_and_annotate_essays():
    # Get the token and validate it (raises an error if validation fails)
    log.info("Received HTTP request. Trying to validate token...")
    token = request.headers.get("X-Auth-Token")
    validate_token(token)
    log.info("Request was successfully authenticated.")

    log.info("Receiving JSON data.")
    # Read and decode the data
    json_input = request.data.decode('unicode-escape',errors='replace')

    # Remove control characters that might cause problems
    json_string = "".join(c for c in json_input if unicodedata.category(c)[0] != 'C' or (c == '\n' or c == '\t'))

    log.info("Creating temporary file '{}'".format(json_temp))
    # Write the data to a temporary file
    temp = open(json_temp, 'w', encoding='utf-8')
    temp.write(json_string)
    temp.close()

    log.info("Starting annotation...")
    # Do the actual annotation
    result_list = get_all_annotations("essays_temp_parsed.json",log)

    os.remove("temp/essays_temp_parsed.json")
    return jsonify(result_list)


# "mongodb://visargue:$visargue$@134.34.226.184:27017"
def get_user_from_db(username):
    """
    Access the VisArgue MongoDB and retrieve the user from the users
    database in order to retrieve the user data (password hash)
    :param username: The username to look for in the db
    :return: A user object consisting of a username and a password hash among other things
    """
    login = urllib.parse.quote_plus('visargue')
    pw = urllib.parse.quote_plus('$visargue$')

    # Contact the server and access the users database
    #userClient = MongoClient('134.34.226.184',port=27017,username=username,password=pw,authSource='visargue')
    userClient = MongoClient("mongodb://{}:{}@134.34.226.184:27017/?authSource=visargue".format(login,pw))
    db = userClient.get_database('visargue')
    users = db['user']

    return users.find_one({'name': username})



def validate_token(token):
    """
    Helper method for validating the auth-token sent by the VisArgue server. The authentication logic
    is adapted from VisArgue (class TokenUtils)
    :param token: the token to be checked
    :return: True if validations succeeds, otherwise raises a PythonServerError
    """
    token_parts = token.split(":")
    username = token_parts[0]
    expiration = token_parts[1]
    client_signature = token_parts[2]
    user = get_user_from_db(username)
    if not user:
        raise PythonServerError("Error while retrieving user information: "
                                "User '{}' was not found in user database".format(username))

    #expires = int(round(time.time() * 1000)) + 12 * 1000 * 60 * 60
    hash = hashlib.md5()
    hash.update(str.encode(user['name'] + ":" + expiration + ":"
                           + user['passwordHash'] + ":" + MAGIC_KEY))
    server_signature = hash.hexdigest()
    if (int(expiration) >= int(round(time.time() * 1000))
            and client_signature == server_signature):
        return True
    else:
        raise PythonServerError("Authentication failed for token '{}'".format(token))


class PythonServerError(Exception):
    def __init__(self,message):
        self.message = message
