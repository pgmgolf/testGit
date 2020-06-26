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

nav_node_language_mssql = Blueprint('nav_node_language_mssql', __name__)

@nav_node_language_mssql.route("/navigation/retrieveLanguageMSSQL", methods=['POST'])
def retrieveLanguageMSSQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        select language_skey,language_id,language_comment
        from language_def
        """
        cursor.execute(sql)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        conn.commit()
        cursor.close()
        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(data,columns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_node_language_mssql.route("/navigation/addNodeLanguageMSSQL", methods=['POST'])
def addNodeLanguageMSSQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['app_skey','node_skey','language_skey','node_name']
        paramCheckStringList = ['node_name']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        nodeSkey = dataInput['node_skey']
        languageSkey = dataInput['language_skey']
        nodeName = dataInput['node_name']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        sql = """\
        select count(1) from pn_node_language
        where app_skey = %(app_skey)s and node_skey = %(node_skey)s and language_skey = %(language_skey)s
        """
        params = {'app_skey': appSkey,'node_skey': nodeSkey,'language_skey': languageSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows>0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Node already App Skey " + str(appSkey) + " and Node Skey " + str(nodeSkey) + " and Language Skey " + str(languageSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        insert into pn_node_language
        (app_skey,node_skey,language_skey,node_name)
        values(%(app_skey)s,%(node_skey)s,%(language_skey)s,%(node_name)s)
        """
        params = {'app_skey': appSkey,'node_skey': nodeSkey,'language_skey': languageSkey,'node_name': nodeName}
        cursor.execute(sql,params)
        conn.commit()

        cursor.close()
        conn.close()

        returnDataColumns = ['app_skey','node_skey','language_skey']
        returnData = [(appSkey,nodeSkey,languageSkey)]
        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'สร้าง Node เรียบร้อย',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_node_language_mssql.route("/navigation/updateNodeLanguageMSSQL", methods=['POST'])
def updateNodeLanguageMSSQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['app_skey','node_skey','language_skey','node_name']
        paramCheckStringList = ['node_name']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        nodeSkey = dataInput['node_skey']
        languageSkey = dataInput['language_skey']
        nodeName = dataInput['node_name']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = "select count(1) from pn_node_language where app_skey = %(app_skey)s and node_skey = %(node_skey)s and language_skey = %(language_skey)s"
        params = {'app_skey': appSkey,'node_skey': nodeSkey,'language_skey': languageSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid App Skey " + str(appSkey) + " and Node Skey " + str(nodeSkey) + " and Language Skey " + str(languageSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        update pn_node_language
        set node_name = %(node_name)s
        where app_skey = %(app_skey)s and
        node_skey = %(node_skey)s and
        language_skey = %(language_skey)s
        """
        params = {'app_skey': appSkey,'node_skey': nodeSkey,'language_skey': languageSkey,'node_name': nodeName}
        cursor.execute(sql,params)
        conn.commit()

        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Update Component เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_node_language_mssql.route("/navigation/deleteNodeLanguageMSSQL", methods=['POST'])
def deleteNodeLanguageMSSQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['app_skey','node_skey','language_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        nodeSkey = dataInput['node_skey']
        languageSkey = dataInput['language_skey']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = "select count(1) from pn_node_language where app_skey = %(app_skey)s and node_skey = %(node_skey)s and language_skey = %(language_skey)s"
        params = {'app_skey': appSkey,'node_skey': nodeSkey,'language_skey': languageSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid App Skey " + str(appSkey) + " and Node Skey " + str(nodeSkey) + " and Language Skey " + str(languageSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        delete from pn_node_language
        where app_skey = %(app_skey)s and node_skey = %(node_skey)s and language_skey = %(language_skey)s
        """
        params = {'app_skey': appSkey,'node_skey': nodeSkey,'language_skey': languageSkey}
        cursor.execute(sql,params)
        conn.commit()

        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Delete Node Language เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
