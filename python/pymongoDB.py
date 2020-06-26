from flask import Flask, session, redirect, url_for
from flask import Flask, request, jsonify, current_app, abort, send_from_directory, send_file
from flask_cors import CORS, cross_origin
from flask import Blueprint
from flaskext.mysql import MySQL
import json
from bson import BSON
from bson import json_util
import os
import pymssql
from datetime import datetime, timedelta
import re
import random
import io
import base64
import jwt
import time
from pymongo import MongoClient
from flask_pymongo import PyMongo
import gridfs
from db_config import *
from common import *
# from StringIO import StringIO
from io import StringIO

pymongoDB = Blueprint('pymongoDB', __name__)

app2 = Flask(__name__)
app2.config['MONGO_URI'] = "mongodb://localhost:27017/Bigdata"
mongo = PyMongo()
mongo.init_app(app2)

class MongoFile:
    def __init__(self, file, filename):
        self.file = file
        self.filename = filename

    def save_file_to_db(self):
        file = self.file
        file_id = str(mongo.save_file(self.filename, file))
        return file_id

@pymongoDB.route("/pymongoDB/uploadFileMongo", methods=['GET', 'POST'])
def uploadFileMongo():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    userID = returnUserToken["data"]["user_id"]

    file = request.files['file']
    # print(type(file), "=======1=type(file)=")
    mongo = MongoFile(file,file.filename)
    # print(type(mongo), "======2=type(mongo)=")
    file_id = mongo.save_file_to_db()
    # print(file_id, "file_id")

    returnDataColumns = ['file_id']
    returnData = [file_id]
    displayColumns = ['isSuccess','reasonCode','reasonText','data']
    displayData = [(isSuccess,reasonCode,'Upload Completed.',returnData)]
    print(returnData,"=returnData======================================")
    print(displayData,"=displayData======================================")
    return jsonify(toJsonOne(displayData,displayColumns))
