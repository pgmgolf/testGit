
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

from db_config import *
from common import *

db_mysql = Blueprint('db_mysql', __name__)

@db_mysql.route("/getMenuMySQL", methods=['POST'])
def getMenuMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['user_id','app_name','sort_type','from_node','language_id']
    paramCheckStringList = ['user_id','app_name','sort_type','language_id']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    userID = dataInput['user_id']
    appName = dataInput['app_name']
    sortType = dataInput['sort_type']
    fromNode = dataInput['from_node']
    languageID = dataInput['language_id']

    dataInput = request.json

    conn = mysql.connect()
    cursor = conn.cursor()
    args = [userID,appName,sortType,fromNode,languageID]
    cursor.callproc('sp_pruned_menu_wrapper', args)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    cursor.close()

    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]
    return jsonify(toJsonOne(displayData,displayColumns))
