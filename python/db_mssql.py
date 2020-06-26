
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

db_mssql = Blueprint('db_mssql', __name__)

@db_mssql.route("/getMenuMSSQL", methods=['POST'])
def getMenuMSSQL():
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

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()

    sql = """\
    EXEC sp_pruned_menu_wrapper @a_s_user_id = %(a_s_user_id)s,@a_s_app_name = %(a_s_app_name)s,@a_s_sort_type = %(a_s_sort_type)s,@language_id = %(language_id)s;
    """
    params = {'a_s_user_id': userID,'a_s_app_name': appName,'a_s_sort_type': sortType,'language_id': languageID}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    cursor.close()

    indexIcon = columns.index('icon')
    newData = []
    # for row in data:
    #     listRow = list(row)
    #     del listRow[indexIcon]
    #     newData.append(listRow)
        # listRow.append(base64.encodestring(row[indexIcon]))

    for row in data:
        listRow = list(row)
        if row[indexIcon] != None:
            listRow.append(base64.encodestring(row[indexIcon]))
        else:
            listRow.append(None)

        if 'icon_base64' not in columns:
            columns.append('icon_base64')
        del listRow[indexIcon]
        newData.append(listRow)

    del columns[indexIcon]

    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(newData,columns))]
    return jsonify(toJsonOne(displayData,displayColumns))

    # displayColumns = ['isSuccess','data']
    # displayData = [(isSuccess,toJson(data,columns))]
    # return jsonify(toJsonOne(displayData,displayColumns))
