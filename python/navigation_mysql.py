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

navigation_mysql = Blueprint('navigation_mysql', __name__)

@navigation_mysql.route("/navigation/retrieveComponentMySQL", methods=['POST'])
def retrieveComponentMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select win_skey,app_skey,win_name,open_style,max_open_count,window_comment,create_user_id,create_date,maint_user_id,maint_date,win_dll_name,login from pc_window_def where app_skey = 4"
    # sql = "SELECT user_id,first_name,last_name,ssn,employee_no,facility_cd,to_base64(picture) as picture_base64  from pc_user_def"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@navigation_mysql.route("/navigation/addComponentMySQL", methods=['POST'])
def addComponentMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

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
    sql = "select count(1) from pc_window_def where win_name like %s"
    cursor.execute(sql,winName)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Component already " + winName

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    winSkey = getNextSequenceMySQL('pc_window_def','win_skey','win_skey')
    sql = """\
    insert into pc_window_def
    (win_skey,app_skey,win_name,open_style,max_open_count,window_comment,create_user_id,create_date,maint_user_id,maint_date)
    values(%(win_skey)s,%(app_skey)s,%(win_name)s,"O",1,%(window_comment)s,user(),now(),user(),now())
    """
    params = {'win_skey': winSkey,'app_skey': appSkey,'win_name': winName,'window_comment': windowComment}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้าง Coomponent เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@navigation_mysql.route("/navigation/updateComponentMySQL", methods=['POST'])
def updateComponentMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

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
    sql = "select count(1) from pc_window_def where win_skey like %s"
    cursor.execute(sql,winSkey)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Window Skey " + winSkey

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update pc_window_def
    set win_name = %(win_name)s,
    window_comment = %(window_comment)s
    where win_skey = %(win_skey)s
    """
    params = {'win_skey': winSkey,'win_name': winName,'window_comment': windowComment}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    # print(session['message'])

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'Update Component เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@navigation_mysql.route("/navigation/deleteComponentMySQL", methods=['POST'])
def deleteComponentMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

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
        reasonText = "Invalid Window Skey " + winSkey

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
    displayData = [(isSuccess,reasonCode,'Delete Component เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))
