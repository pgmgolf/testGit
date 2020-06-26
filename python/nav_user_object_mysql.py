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

nav_user_object_mysql = Blueprint('nav_user_object_mysql', __name__)

@nav_user_object_mysql.route("/navigation/retrieveUserObjectMySQL", methods=['POST'])
def retrieveUserObjectMySQL():
    try:
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

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select pl_object_def.object_skey,pl_object_def.win_skey,pl_object_def.node_skey,pl_object_def.object_type,pl_object_def.object_comment,
        pl_object_def.app_skey,pl_object_def.object_name,pl_object_def.access_condition,pl_object_def.create_user_id,pl_object_def.create_date,
        pl_object_def.maint_user_id,pl_object_def.maint_date,pl_object_def.where_condition,pl_object_def.dw_text,
        pl_object_def.dw_back,pl_object_def.dw_border,pl_object_def.win_ref_skey,pl_object_def.qbe_name,
        pl_user_object.user_skey,pl_user_object.access_ind,pc_user_def.user_id,concat(pc_user_def.first_name," ",pc_user_def.first_name) as full_name
        from pl_object_def inner join pl_user_object on
        pl_object_def.object_skey = pl_user_object.object_skey inner join pc_user_def on
        pl_user_object.user_skey = pc_user_def.user_skey
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
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_user_object_mysql.route("/navigation/addUserObjectMySQL", methods=['POST'])
def addUserObjectMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['object_skey','to_user']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        objectSkey = dataInput['object_skey']
        toUser = dataInput['to_user']

        conn = mysql.connect()
        cursor = conn.cursor()

        for user in toUser:
            sql = """\
            select count(1)
            from pl_user_object
            where user_skey = %(user_skey)s and
            object_skey = %(object_skey)s
            """
            params = {'user_skey': user['user_skey'], 'object_skey': objectSkey}
            cursor.execute(sql,params)
            (number_of_rows,)=cursor.fetchone()

            if number_of_rows==0:
                sql = """\
                insert into pl_user_object
                (user_skey,object_skey,access_ind)
                values(%(user_skey)s,%(object_skey)s,%(access_ind)s)
                """
                params = {'user_skey': user['user_skey'], 'object_skey': objectSkey, 'access_ind': 0}
                cursor.execute(sql,params)
                conn.commit()
            # else:
            #     sql = """\
            #     update pl_user_object
            #     set access_ind = %(access_ind)s
            #     where user_skey = %(user_skey)s and
            #     object_skey = %(object_skey)s
            #     """
            #     params = {'user_skey': user['user_skey'], 'object_skey': objectSkey, 'access_ind': 0}
            #     cursor.execute(sql,params)
            #     conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Insert Access Object เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_user_object_mysql.route("/navigation/deleteUserObjectMySQL", methods=['POST'])
def deleteUserObjectMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['user_skey', 'object_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        userSkey = dataInput['user_skey']
        objectSkey = dataInput['object_skey']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from pl_user_object
        where user_skey = %(user_skey)s and
        object_skey = %(object_skey)s
        """
        params = {'user_skey': userSkey, 'object_skey': objectSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()
        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid User Skey " + str(userSkey) + " Object Skey " + str(objectSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        delete from pl_user_object
        where user_skey = %(user_skey)s and
        object_skey = %(object_skey)s
        """
        params = {'user_skey': userSkey, 'object_skey': objectSkey}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Delete User Object เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_user_object_mysql.route("/navigation/updateUserObjectMySQL", methods=['POST'])
def updateUserObjectMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['user_skey', 'object_skey','access_ind']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        userSkey = dataInput['user_skey']
        objectSkey = dataInput['object_skey']
        accessInd = dataInput['access_ind']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from pl_user_object
        where user_skey = %(user_skey)s and
        object_skey = %(object_skey)s
        """
        params = {'user_skey': userSkey, 'object_skey': objectSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()
        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid User Skey " + str(userSkey) + " Object Skey " + str(objectSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        update pl_user_object
        set access_ind = %(access_ind)s
        where user_skey = %(user_skey)s and
        object_skey = %(object_skey)s
        """
        params = {'user_skey': userSkey, 'object_skey': objectSkey, 'access_ind': accessInd}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Update Access Object เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
