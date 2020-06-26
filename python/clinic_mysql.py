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

clinic_mysql = Blueprint('clinic_mysql', __name__)

@clinic_mysql.route("/clinic/retrieveClinicMySQL", methods=['POST'])
def retrieveClinicMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select clinic_skey,clinic_id,clinic_name,clinic_desc,icon,status,date_created,user_created,date_changed,user_changed
        from clinic_master
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

@clinic_mysql.route("/clinic/addClinicMySQL", methods=['POST'])
def addClinicMySQL():
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
        paramList = ['clinic_id','clinic_name','clinic_desc','status']
        paramCheckStringList = ['clinic_id','clinic_name','clinic_desc','status']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        clinicID = dataInput['clinic_id']
        clinicName = dataInput['clinic_name']
        clinicDesc = dataInput['clinic_desc']
        status = dataInput['status']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from clinic_master
        where clinic_id = %(clinic_id)s
        """
        params = {'clinic_id': clinicID}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows>0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Clinic ID already " + clinicID

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        clinicSkey = getNextSequenceMySQL('clinic_master','clinic_master','clinic_skey')
        sql = """\
        insert into clinic_master
        (clinic_skey,clinic_id,clinic_name,clinic_desc,status,date_created,user_created,date_changed,user_changed)
        values(%(clinic_skey)s,%(clinic_id)s,%(clinic_name)s,%(clinic_desc)s,%(status)s,%(date_created)s,%(user_created)s,%(date_changed)s,%(user_changed)s)
        """
        params = {'clinic_skey': clinicSkey,'clinic_id': clinicID,'clinic_name': clinicName,'clinic_desc': clinicDesc,'status': status,'date_created': now,'user_created': userID,'date_changed': now,'user_changed': userID}
        cursor.execute(sql,params)
        conn.commit()

        cursor.close()
        conn.close()

        returnDataColumns = ['clinic_skey','clinic_id','date_created','user_created','date_changed','user_changed']
        returnData = [(clinicSkey,clinicID,now,userID,now,userID)]

        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'สร้าง Clinic เรียบร้อย',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@clinic_mysql.route("/clinic/updateClinicMySQL", methods=['POST'])
def updateClinicMySQL():
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
        paramList = ['clinic_skey','clinic_id','clinic_name','clinic_desc','status']
        paramCheckStringList = ['clinic_id','clinic_name','clinic_desc','status']
        paramCheckNumberList = ['clinic_skey']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        clinicSkey = dataInput['clinic_skey']
        clinicID = dataInput['clinic_id']
        clinicName = dataInput['clinic_name']
        clinicDesc = dataInput['clinic_desc']
        status = dataInput['status']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from clinic_master
        where clinic_skey = %(clinic_skey)s
        """
        params = {'clinic_skey': clinicSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid clinic Skey " + str(clinicSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        update clinic_master
        set clinic_id = %(clinic_id)s,
        clinic_name = %(clinic_name)s,
        clinic_desc = %(clinic_desc)s,
        status = %(status)s,
        date_changed = %(date_changed)s,
        user_changed = %(user_changed)s
        where clinic_skey = %(clinic_skey)s
        """
        params = {'clinic_skey': clinicSkey,'clinic_id': clinicID,'clinic_name': clinicName,'clinic_desc': clinicDesc,'status': status,'date_created': now,'user_created': userID,'date_changed': now,'user_changed': userID}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        returnDataColumns = ['clinic_skey','clinic_id','date_changed','user_changed']
        returnData = [(clinicSkey,clinicID,now,userID)]

        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'Update Clinic เรียบร้อย',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@clinic_mysql.route("/clinic/deleteClinicMySQL", methods=['POST'])
def deleteClinicMySQL():
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
        paramList = ['clinic_skey','clinic_id']
        paramCheckStringList = ['clinic_id']
        paramCheckNumberList = ['clinic_skey']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        clinicSkey = dataInput['clinic_skey']
        clinicID = dataInput['clinic_id']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from clinic_master
        where clinic_skey = %(clinic_skey)s
        """
        params = {'clinic_skey': clinicSkey}

        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid clinic Skey " + str(clinicSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        delete from clinic_master
        where clinic_skey = %(clinic_skey)s
        """
        params = {'clinic_skey': clinicSkey}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Delete Clinic เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
