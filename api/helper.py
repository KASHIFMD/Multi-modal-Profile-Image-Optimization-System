import random
import string
import toml
from functools import reduce
from operator import getitem
from pathlib import Path
import re, sys, os
import traceback
import requests, json

def checkKeyExists(dictionary, key):
    try:
        if key in dictionary.keys():
            return True
        else:
            return False
    except Exception as e:
        return False


def getConfigData(key, index=None):
    try:
        config = toml.load('config.toml')
        path = key.split('.')
        response = reduce(getitem, path, config)
        if index is None:
            return response
        else:
            return response[index]
    except Exception as e:
        print('error_traceback')
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        print("".join(tb_str[-3:]))
        return None

def clean_latin1(data):
    LATIN_1_CHARS = (
        ("\xe2\x80\x99", "'"),
        ("\xc3\xa9", "e"),
        ("\xe2\x80\x90", "-"),
        ("\xe2\x80\x91", "-"),
        ("\xe2\x80\x92", "-"),
        ("\xe2\x80\x93", "-"),
        ("\xe2\x80\x94", "-"),
        ("\xe2\x80\x94", "-"),
        ("\xe2\x80\x98", "'"),
        ("\xe2\x80\x9b", "'"),
        ("\xe2\x80\x9c", '"'),
        ("\xe2\x80\x9c", '"'),
        ("\xe2\x80\x9d", '"'),
        ("\xe2\x80\x9e", '"'),
        ("\xe2\x80\x9f", '"'),
        ("\xe2\x80\xa6", '...'),
        ("\xe2\x80\xb2", "'"),
        ("\xe2\x80\xb3", "'"),
        ("\xe2\x80\xb4", "'"),
        ("\xe2\x80\xb5", "'"),
        ("\xe2\x80\xb6", "'"),
        ("\xe2\x80\xb7", "'"),
        ("\xe2\x81\xba", "+"),
        ("\xe2\x81\xbb", "-"),
        ("\xe2\x81\xbc", "="),
        ("\xe2\x81\xbd", "("),
        ("\xe2\x81\xbe", ")")
    )

    try:
        data = data.decode('iso-8859-1')
        for _hex, _char in LATIN_1_CHARS:
            data = data.replace(_hex, _char)
        return data
    except Exception as e:
        return data

def addSlashes(string):

    try:

        if string != None and string.strip() != '':

            string  = string.strip()
            string  = string.replace("'", "\'")
            string  = string.replace('"', '\"')
        
        return string

    except Exception as e:

        return string

def stripSlashes(string):
    try:

        if string != None and string.strip() != '':

            string = re.sub(r"\\(n|r)", "\n", string)
            string = re.sub(r"\\", "", string)
            
        return string

    except Exception as e:

        return string

def getConfigInfo(key, index=None):
    project_directory = os.path.dirname(os.path.realpath(__file__))
    parent1 = os.path.dirname(project_directory)

    sys.path.append(parent1)
    try:
        config = toml.load(project_directory + '/config.toml')
        path = key.split('.')
        response = reduce(getitem, path, config)
        if index is None:
            return response
        else:
            return response[index]
    except Exception as e:
        print(e)
        return None

def generateRandom(val):
    range_val = int(val)
    random_str = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(range_val))
    return random_str

def RemoveFile(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File {file_path} removed successfully")
        else:
            print(f"File {file_path} does not exist")
    except Exception as e:
        print(f"Error removing file {file_path}: {e}")
        
def RemoveDirectory(directory_path):
    try:
        if os.path.exists(directory_path):
            os.rmdir(directory_path)
            print(f"Directory {directory_path} removed successfully")
        else:
            print(f"Directory {directory_path} does not exist")
    except Exception as e:
        print(f"Error removing directory {directory_path}: {e}")

def RemoveDirectoryContents(directory_path):
    try:
        if os.path.exists(directory_path):
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")
        else:
            print(f"Directory {directory_path} does not exist")
    except Exception as e:
        print(f"Error removing directory contents {directory_path}: {e}")
        
def CurlGetRequest(url):
    try:
        payload = {}
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        return response.text
    except Exception as e:
        print(f"Error in curlGetRequest: {e}")
        return None
