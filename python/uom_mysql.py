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

uom_mysql = Blueprint('uom_mysql', __name__)

@uom_mysql.route("/uom/retrieveUOMMySQL", methods=['POST'])
def retrieveUOMMySQL():
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
        select uom,uom_desc
        from uom
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

@uom_mysql.route("/uom/addUOMMySQL", methods=['POST'])
def addUOMMySQL():
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
        paramList = ['uom','uom_desc']
        paramCheckStringList = ['uom','uom_desc']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        uom = dataInput['uom']
        uomDesc = dataInput['uom_desc']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from uom
        where uom = %(uom)s
        """
        params = {'uom': uom}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows>0:
            isSuccess = False
            reasonCode = 500
            reasonText = "UOM already " + uom

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        insert into uom
        (uom,uom_desc)
        values(%(uom)s,%(uom_desc))
        """
        params = {'uom': uom,'uom_desc': uomDesc}
        cursor.execute(sql,params)
        conn.commit()

        cursor.close()
        conn.close()

        returnDataColumns = ['uom','uom_desc']
        returnData = [(uom,uomDesc)]

        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'สร้าง UOM เรียบร้อย',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@uom_mysql.route("/uom/updateUOMMySQL", methods=['POST'])
def updateUOMMySQL():
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
        paramList = ['uom','uom_desc']
        paramCheckStringList = ['uom','uom_desc']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        uom = dataInput['uom']
        uomDesc = dataInput['uom_desc']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from uom
        where uom = %(uom)s
        """
        params = {'uom': uom}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid UOM " + str(uom)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        update uom
        set uom_desc = %(uom_desc)s,
        where uom = %(uom)s
        """
        params = {'uom': uom,'uom_desc': uomDesc}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        returnDataColumns = ['uom','uom_desc']
        returnData = [(uom,uomDesc)]

        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'Update UOM เรียบร้อย',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@uom_mysql.route("/uom/deleteUOMMySQL", methods=['POST'])
def deleteUOMMySQL():
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
        paramList = ['uom']
        paramCheckStringList = ['uom']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        uom = dataInput['uom']
        uomDesc = dataInput['uom_desc']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from uom
        where uom = %(uom)s
        """
        params = {'uom': uom}

        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid UOM" + str(uom)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        delete from uom
        where uom = %(uom)s
        """
        params = {'uom': uom}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Delete UOM เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
