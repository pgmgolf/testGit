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

user_mysql = Blueprint('user_mysql', __name__)

@user_mysql.route("/getUserWithImageMySQL", methods=['POST'])
def getUserWithImageMySQL():
    dataInput = request.json
    userID = dataInput['user_id']

    conn = mysql.connect()
    cursor = conn.cursor()
    # sql = "select user_id,first_name,last_name,user_password,picture from pc_user_def where user_id = %(user_id)"
    # param = {'user_id': userID}
    # cursor.execute(sql, param)
    sql = "select user_id,first_name,last_name,user_password,picture from pc_user_def where user_id like %s"
    cursor.execute(sql,userID)
    row = cursor.fetchone()
    columns = [column[0] for column in cursor.description]
    if row == None:
        isSuccess = False
        reasonCode = 501
        reasonText = "Not Found User"

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    dataOne = toJsonOne(row,columns)
    user_id = dataOne["user_id"]
    first_name = dataOne["first_name"]
    last_name = dataOne["last_name"]
    user_password = dataOne["user_password"]
    picture_blob = dataOne["picture"]
    print(dataOne)
    # filename = first_name + last_name
    # with open(filename, 'wb') as output_file:
    #     output_file.write(picture_blob)
    # return filename
    return send_file(io.BytesIO(picture_blob),
                     attachment_filename='logo.png',
                     mimetype='image/png')
    return jsonify({'result': base64.b64encode(picture_blob)})

@user_mysql.route("/user/validateUserMySQL", methods=['POST'])
def validateUserMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['user_id','password']
        paramCheckStringList = ['user_id','password']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        userID = dataInput['user_id']
        password = dataInput['password']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select user_skey,user_id,first_name,last_name,user_password,salt_value,hash_value
        from pc_user_def
        where user_id = %(user_id)s
        """
        params = {'user_id': userID}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = toJson(data,columns)
        conn.commit()
        cursor.close()

        if len(result) == 0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid User " + userID

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        # passwordDB = Decrypt(result[0]["user_password"])
        # if password != passwordDB:

        hashPassword = encryptHashSHA512(password + result[0]["salt_value"])

        if result[0]["hash_value"] != hashPassword:
            isSuccess = False
            reasonCode = 501
            reasonText = "Invalid password"

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        loginTime = now.strftime("%Y-%m-%d %H:%M")

        payload = {
            'user_id': userID,
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + timedelta(minutes=10000)
            }

        token = jwt.encode(payload, current_app.config['SECRET_KEY'], 'HS256')

        displayColumns = ['isSuccess','user_id','loginTime','token']
        # displayData = [(isSuccess,userID,loginTime,firstname,lastname,base64.b64encode(picture_blob),token.decode('UTF-8'))]
        displayData = [(isSuccess,userID,loginTime,token.decode('UTF-8'))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@user_mysql.route("/user/getUserInfoMySQL", methods=['POST'])
def getUserInfoMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        # try:
        #     payload = getUserToken(request.headers.get('Authorization'))
        #     userID = payload['user_id']
        # except Exception as e:
        #     isSuccess = False
        #     reasonCode = 500
        #     reasonText = "Token Invalid"
        #
        #     errColumns = ['isSuccess','reasonCode','reasonText']
        #     errData = [(isSuccess,reasonCode,str(e))]
        #
        #     return jsonify(toJsonOne(errData,errColumns))

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userIDToken = returnUserToken["data"]["user_id"]

        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """\
        select user_skey,user_id,first_name,last_name,user_password,facility_cd,salt_value,hash_value,to_base64(picture) as picture_base64
        from pc_user_def where user_id = %(user_id)s
        """
        params = {'user_id': userIDToken}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        cursor.close()

        if len(data) == 0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid User " + userIDToken

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJsonOne(data,columns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@user_mysql.route("/user/retrieveUserMySQL", methods=['POST'])
def retrieveUserMySQL():
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
        select user_skey,user_id,first_name,last_name,user_password,facility_cd,salt_value,hash_value,to_base64(picture) as picture_base64
        from pc_user_def
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

@user_mysql.route("/user/addUserMySQL", methods=['POST'])
def addUserMySQL():
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
        paramList = ['user_id','password','first_name','last_name']
        paramCheckStringList = ['user_id','password','first_name','last_name']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        userID = dataInput['user_id']
        password = dataInput['password']
        first_name = dataInput['first_name']
        last_name = dataInput['last_name']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from pc_user_def
        where user_id = %(user_id)s
        """
        params = {'user_id': userID}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows>0:
            isSuccess = False
            reasonCode = 500
            reasonText = "User ID already " + userID

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        saltValue = randomStringDigits(20)
        userSkey = getNextSequenceMySQL('pc_user_def','pc_user_def','user_skey')
        sql = """\
        insert into pc_user_def
        (user_skey,user_id,first_name,last_name,user_password,salt_value,hash_value)
        values(%(user_skey)s,%(user_id)s,%(first_name)s,%(last_name)s,%(user_password)s,%(salt_value)s,%(hash_value)s)
        """
        params = {'user_skey': userSkey,'user_id': userID,'user_password': Encrypt(password),'first_name': first_name,'last_name': last_name, 'salt_value': saltValue, 'hash_value': encryptHashSHA512(password + saltValue)}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'สร้าง User เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@user_mysql.route("/user/updateUserMySQL", methods=['POST'])
def updateUserMySQL():
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
        paramList = ['user_id','first_name','last_name']
        paramCheckStringList = ['user_id','first_name','last_name']
        paramCheckNumberList = ['user_skey']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        # userSkey = dataInput['user_skey']
        userID = dataInput['user_id']
        first_name = dataInput['first_name']
        last_name = dataInput['last_name']
        if 'password' in dataInput:
            password = dataInput['password']
        else:
            password = ''
        if 'picture_base64' in dataInput:
            picture_base64 = dataInput['picture_base64']
        else:
            picture_base64 = ''

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select user_skey,user_id,first_name,last_name,user_password,salt_value,hash_value
        from pc_user_def
        where user_id = %(user_id)s
        """
        params = {'user_id': userID}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = toJson(data,columns)

        if len(result) == 0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid User " + userID

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        if result[0]['salt_value'] is None or len(result[0]["salt_value"]) == 0:
            saltValue = randomStringDigits(20)
        else:
            saltValue = result[0]["salt_value"]

        sql = """\
        update pc_user_def
        set user_id = %(user_id)s,
        first_name = %(first_name)s,
        last_name = %(last_name)s,
        """
        if len(password) > 0:
            sql = sql + """\
            user_password = %(user_password)s,
            hash_value = %(hash_value)s,
            """
        if 'picture_base64' in dataInput:
            sql = sql + """\
            picture = FROM_BASE64(%(picture)s),
            """
        sql = sql + """\
        salt_value = %(salt_value)s
        where user_id = %(user_id)s
        """

        params = {'user_id': userID,'user_password': Encrypt(password),'first_name': first_name,'last_name': last_name,'picture': picture_base64,'salt_value': saltValue,'hash_value': encryptHashSHA512(password + saltValue)}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Update User เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@user_mysql.route("/user/deleteUserMySQL", methods=['POST'])
def deleteUserMySQL():
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
        paramList = ['user_id']
        paramCheckStringList = ['user_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        # userSkey = dataInput['user_skey']
        userID = dataInput['user_id']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from pc_user_def
        where user_id = %(user_id)s
        """
        params = {'user_id': userID}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid User " + userID

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        delete from pc_user_def
        where user_id = %(user_id)s
        """
        params = {'user_id': userID}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Delete User เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
