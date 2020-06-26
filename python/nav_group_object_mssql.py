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

nav_group_object_mssql = Blueprint('nav_group_object_mssql', __name__)

@nav_group_object_mssql.route("/navigation/retrieveGroupObjectMSSQL", methods=['POST'])
def retrieveGroupObjectMSSQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['object_skey']
    paramCheckStringList = []

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    objectSkey = dataInput['object_skey']

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = """\
    select pl_object_def.object_skey,pl_object_def.win_skey,pl_object_def.node_skey,pl_object_def.object_type,pl_object_def.object_comment,
    pl_object_def.app_skey,pl_object_def.object_name,pl_object_def.access_condition,pl_object_def.create_user_id,pl_object_def.create_date,
    pl_object_def.maint_user_id,pl_object_def.maint_date,pl_object_def.where_condition,pl_object_def.dw_text,
    pl_object_def.dw_back,pl_object_def.dw_border,pl_object_def.win_ref_skey,pl_object_def.qbe_name,
    pl_group_object.group_skey,pl_group_object.access_ind,pl_group_def.group_name,pl_group_def.sec_admin_ind
    from pl_object_def inner join pl_group_object on
    pl_object_def.object_skey = pl_group_object.object_skey inner join pl_group_def on
    pl_group_object.group_skey = pl_group_def.group_skey
    where pl_object_def.object_skey = %(object_skey)s
    """
    params = {'object_skey': objectSkey}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@nav_group_object_mssql.route("/navigation/addGroupObjectMSSQL", methods=['POST'])
def addGroupObjectMSSQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['object_skey','to_group']
    paramCheckStringList = []

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    objectSkey = dataInput['object_skey']
    toGroup = dataInput['to_group']

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()

    for group in toGroup:
        sql = """\
        select count(1)
        from pl_group_object
        where group_skey = %(group_skey)s and
        object_skey = %(object_skey)s
        """
        params = {'group_skey': group['group_skey'], 'object_skey': objectSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            sql = """\
            insert into pl_group_object
            (group_skey,object_skey,access_ind)
            values(%(group_skey)s,%(object_skey)s,%(access_ind)s)
            """
            params = {'group_skey': group['group_skey'], 'object_skey': objectSkey, 'access_ind': 0}
            cursor.execute(sql,params)
            conn.commit()
        else:
            sql = """\
            update pl_group_object
            set access_ind = %(access_ind)s
            where group_skey = %(group_skey)s and
            object_skey = %(object_skey)s
            """
            params = {'group_skey': group['group_skey'], 'object_skey': objectSkey, 'access_ind': 0}
            cursor.execute(sql,params)
            conn.commit()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'Insert Access Object เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@nav_group_object_mssql.route("/navigation/deleteGroupObjectMSSQL", methods=['POST'])
def deleteGroupObjectMSSQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['group_skey', 'object_skey']
    paramCheckStringList = []

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    groupSkey = dataInput['group_skey']
    objectSkey = dataInput['object_skey']

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = """\
    select count(1)
    from pl_group_object
    where group_skey = %(group_skey)s and
    object_skey = %(object_skey)s
    """
    params = {'group_skey': groupSkey, 'object_skey': objectSkey}
    cursor.execute(sql,params)
    (number_of_rows,)=cursor.fetchone()
    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Group Skey " + str(group_skey) + " Object Skey " + str(objectSkey)

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete from pl_group_object
    where group_skey = %(group_skey)s and
    object_skey = %(object_skey)s
    """
    params = {'group_skey': groupSkey, 'object_skey': objectSkey}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'Delete Group Object เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@nav_group_object_mssql.route("/navigation/updateGroupObjectMSSQL", methods=['POST'])
def updateGroupObjectMSSQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['group_skey', 'object_skey','access_ind']
    paramCheckStringList = []

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    groupSkey = dataInput['group_skey']
    objectSkey = dataInput['object_skey']
    accessInd = dataInput['access_ind']

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = """\
    select count(1)
    from pl_group_object
    where group_skey = %(group_skey)s and
    object_skey = %(object_skey)s
    """
    params = {'group_skey': groupSkey, 'object_skey': objectSkey}
    cursor.execute(sql,params)
    (number_of_rows,)=cursor.fetchone()
    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Group Skey " + str(groupSkey) + " Object Skey " + str(objectSkey)

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update pl_group_object
    set access_ind = %(access_ind)s
    where group_skey = %(group_skey)s and
    object_skey = %(object_skey)s
    """
    params = {'group_skey': groupSkey, 'object_skey': objectSkey, 'access_ind': accessInd}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'Update Group Object เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))
