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

from db_config import *
from common import *

LabOrderEntry = Blueprint('LabOrderEntry', __name__)

@LabOrderEntry.route("/LabOrderEntry/retrieveTestCatOrderEntry", methods=['POST'])
def retrieveTestCatOrderEntry():
    try:
        print('1')
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        dataInput = request.json
        paramList = ['languageId']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        languageId = dataInput['languageId']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_bnh_labonline_testcat_retrieve @language_id = %(languageId)s
        """
        params = {'languageId': languageId}
        cursor.execute(sql,params)

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
        errData = [(isSuccess,reasonCode,e.message if hasattr(e, 'message') else str(e))]
        return jsonify(toJsonOne(errData,errColumns))
@LabOrderEntry.route("/LabOrderEntry/retrieveTestOrderDetailEntry", methods=['POST'])
def retrieveTestOrderDetailEntry():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        dataInput = request.json
        paramList = ['categorySkey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        categorySkey = dataInput['categorySkey']
        languageId = dataInput['languageId']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_bnh_labonline_testOrder_retrieve @category_skey = %(categorySkey)s, 
        @language_id = %(languageId)s
        """
        params = {'categorySkey': categorySkey, 'languageId': languageId}
        cursor.execute(sql,params)

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
        errData = [(isSuccess,reasonCode, e.message if hasattr(e, 'message') else str(e))]
        return jsonify(toJsonOne(errData,errColumns))
@LabOrderEntry.route("/LabOrderEntry/addRequest", methods=['POST'])
def addRequest():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        dataInput = request.json
        paramList = ['cartProducts']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        cartProducts = dataInput['cartProducts']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        conn.autocommit(False)

        sql = """\
        select count(1) from pc_user_def a
        inner join lis_patient b on a.patient_skey = b.patient_skey
        where user_id = %(userID)s
        """
        params = {'userID': userID}
        cursor.execute(sql,params)

        (number_of_rows,)=cursor.fetchone()
        if number_of_rows<1:
            isSuccess = False
            reasonCode = 500
            reasonText = "Not found patient info."

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        select a.patient_skey from pc_user_def a
        inner join lis_patient b on a.patient_skey = b.patient_skey
        where user_id = %(userID)s
        """
        params = {'userID': userID}
        cursor.execute(sql,params)

        (patientSkey,)=cursor.fetchone()


        sql = """\
        INSERT INTO LOL_REQUEST_HEADER(PATIENT_SKEY, REQUEST_DATE)
        VALUES (%(patientSkey)s, getdate())

        SELECT  TOP 1 @@IDentity As [@@IDentity] 
        FROM LOL_REQUEST_HEADER 
        """
        params = {'patientSkey': patientSkey}
        cursor.execute(sql,params)

        (requestSkey,)=cursor.fetchone()
        print(requestSkey, ' ===========requestSkey=============')
        for data in cartProducts:   
            print(data['CATEGORY_ORDER_SKEY'])
            sql = """\
            INSERT INTO LOL_REQUEST_DETAIL(REQUEST_SKEY, CATEGORY_ORDER_SKEY)
            VALUES (%(requestSkey)s, %(categoryOrderSkey)s)
            """
            params = {'requestSkey': requestSkey, 'categoryOrderSkey': data['CATEGORY_ORDER_SKEY']}
            cursor.execute(sql,params)

        conn.commit()

        returnDataColumns = ['requestSkey']
        returnData = [(str(requestSkey))]
        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'Success',toJsonOne(returnData,returnDataColumns))] 

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        conn.rollback()

        print('rollback')

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
@LabOrderEntry.route("/LabOrderEntry/retrieveRequest", methods=['POST'])
def retrieveRequest():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        dataInput = request.json
        languageId = dataInput['languageId']
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_bnh_labonline_request_retrieve @user_id= %(userID)s, @language_id= %(languageId)s
        """
        params = {'userID': userID, 'languageId': languageId}
        cursor.execute(sql,params)

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
        errData = [(isSuccess,reasonCode,e.message if hasattr(e, 'message') else str(e))]
        return jsonify(toJsonOne(errData,errColumns))

@LabOrderEntry.route("/LabOrderEntry/retrieveRequestDetail", methods=['POST'])
def retrieveRequestDetail():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        dataInput = request.json
        requestSkey = dataInput['requestSkey']
        languageId = dataInput['languageId']
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_bnh_labonline_request_detail_retrieve @request_skey= %(requestSkey)s, @language_id= %(languageId)s
        """
        params = {'requestSkey': requestSkey, 'languageId': languageId}
        cursor.execute(sql,params)

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
        errData = [(isSuccess,reasonCode,e.message if hasattr(e, 'message') else str(e))]
        return jsonify(toJsonOne(errData,errColumns))
