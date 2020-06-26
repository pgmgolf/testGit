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

nav_window_mysql = Blueprint('nav_window_mysql', __name__)

@nav_window_mysql.route("/navigation/retrieveWindowMySQL", methods=['POST'])
def retrieveWindowMySQL():
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
        paramList = ['app_name']
        paramCheckStringList = ['app_name']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appName = dataInput['app_name']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select pc_window_def.win_skey,pc_window_def.app_skey,pc_window_def.win_name,pc_window_def.open_style,pc_window_def.max_open_count,
        pc_window_def.window_comment,pc_window_def.create_user_id,pc_window_def.create_date,pc_window_def.maint_user_id,
        pc_window_def.maint_date,pc_window_def.win_dll_name,pc_window_def.login
        from pc_window_def inner join pc_app_def on
        pc_window_def.app_skey = pc_app_def.app_skey
        where pc_app_def.app_name = %(app_name)s
        """
        params = {'app_name': appName}
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

@nav_window_mysql.route("/navigation/addWindowMySQL", methods=['POST'])
def addWindowMySQL():
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
        paramList = ['app_skey','win_name','window_comment']
        paramCheckStringList = ['win_name','window_comment']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        winName = dataInput['win_name']
        windowComment = dataInput['window_comment']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from pc_window_def
        where win_name like %(win_name)s
        """
        params = {'win_name': winName}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows>0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Window already " + winName

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        winSkey = getNextSequenceMySQL('pc_window_def','win_skey','win_skey')
        sql = """\
        insert into pc_window_def
        (win_skey,app_skey,win_name,open_style,max_open_count,window_comment,create_user_id,create_date,maint_user_id,maint_date)
        values(%(win_skey)s,%(app_skey)s,%(win_name)s,"O",1,%(window_comment)s,%(user_id)s,now(),%(user_id)s,now())
        """
        params = {'win_skey': winSkey,'app_skey': appSkey,'win_name': winName,'window_comment': windowComment,'user_id': userID}
        cursor.execute(sql,params)
        conn.commit()

        cursor.close()
        conn.close()

        returnDataColumns = ['app_skey','win_skey']
        returnData = [(appSkey,winSkey)]

        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'สร้าง Window เรียบร้อย',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_window_mysql.route("/navigation/updateWindowMySQL", methods=['POST'])
def updateWindowMySQL():
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
        paramList = ['win_skey','win_name','window_comment']
        paramCheckStringList = ['win_name','window_comment']
        paramCheckNumberList = ['win_skey','app_skey']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        winSkey = dataInput['win_skey']
        winName = dataInput['win_name']
        windowComment = dataInput['window_comment']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from pc_window_def
        where win_skey = %(win_skey)s
        """
        params = {'win_skey': winSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Window Skey " + str(winSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        update pc_window_def
        set win_name = %(win_name)s,
        window_comment = %(window_comment)s,
        maint_user_id = %(user_id)s,
        maint_date = now()
        where win_skey = %(win_skey)s
        """
        params = {'win_skey': winSkey,'win_name': winName,'window_comment': windowComment,'user_id': userID}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Update Window เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_window_mysql.route("/navigation/deleteWindowMySQL", methods=['POST'])
def deleteWindowMySQL():
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
        paramList = ['win_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        winSkey = dataInput['win_skey']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = "select count(1) from pc_window_def where win_skey like %s"
        cursor.execute(sql,winSkey)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Window Skey " + str(winSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        delete from pc_window_def
        where win_skey = %(win_skey)s
        """
        params = {'win_skey': winSkey}
        cursor.execute(sql,params)
        conn.commit()

        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Delete Window เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
