
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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from db_config import *
from common import *

user_mssql = Blueprint('user_mssql', __name__)

@user_mssql.route("/getUserWithImageMSSQL", methods=['POST'])
def getUserWithImageMSSQL():
    dataInput = request.json
    userID = dataInput['user_id']

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
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

@user_mssql.route("/user/validateUserMSSQL", methods=['POST'])
def validateUserMSSQL():
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

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
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

        if result[0]["salt_value"] is None:
            result[0]["salt_value"]  = ""

        if result[0]["hash_value"] is None:
            result[0]["hash_value"]  = ""

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

@user_mssql.route("/user/getUserInfoMSSQL", methods=['POST'])
def getUserInfoMSSQL():
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

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        sql = """\
        select user_skey,user_id,a.first_name,a.last_name,user_password,facility_cd,salt_value,hash_value,
        CAST(N'' AS XML).value('xs:base64Binary(xs:hexBinary(sql:column("a.picture")))','VARCHAR(MAX)') as picture_base64,
        b.sex,b.phone,b.email,
        convert(nvarchar,year(b.birthday)) + '-' + convert(nvarchar,month(b.birthday)) + '-' + convert(nvarchar,day(b.birthday)) birthday
        from pc_user_def a
        left join lis_patient b on a.patient_skey = b.patient_skey
        where user_id = %(user_id)s
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

        # indexPicture = columns.index('picture')
        # newData = []

        # for row in data:
        #     listRow = list(row)
        #     if row[indexPicture] != None:
        #         listRow.append(base64.encodestring(row[indexPicture]).decode('ascii'))
        #     else:
        #         listRow.append(None)
        #
        #     if 'picture_base64' not in columns:
        #         columns.append('picture_base64')
        #     del listRow[indexPicture]
        #     newData.append(listRow)
        #
        # del columns[indexPicture]

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJsonOne(data,columns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@user_mssql.route("/user/retrieveUserMSSQL", methods=['POST'])
def retrieveUserMSSQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        select user_skey,user_id,a.first_name,a.last_name,user_password,facility_cd,salt_value,hash_value,
        CAST(N'' AS XML).value('xs:base64Binary(xs:hexBinary(sql:column("a.picture")))','VARCHAR(MAX)') as picture_base64
        ,isnull(b.phone,'a.phone') phone, isnull(b.email,a.email) email,
        b.birthday,b.sex
        from pc_user_def a
        left join lis_patient b on a.patient_skey = b.patient_skey
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

@user_mssql.route("/user/addUserMSSQL", methods=['POST'])
def addUserMSSQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""
        print('---------------------Golf---------------')
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
        phone = dataInput['phone']
        email = dataInput['email']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        print(mssql_database)
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
        userSkey = getNextSequenceMSSQL('pc_user_def','pc_user_def','user_skey')
        sql = """\
        insert into pc_user_def
        (user_skey,user_id,first_name,last_name,user_password,salt_value,hash_value,phone,email)
        values(%(user_skey)s,%(user_id)s,%(first_name)s,%(last_name)s,%(user_password)s,%(salt_value)s,%(hash_value)s,%(phone)s,%(email)s)
        """
        params = {'user_skey': userSkey,
            'user_id': userID,
            'user_password': Encrypt(password),
            'first_name': first_name,
            'last_name': last_name,
            'salt_value': saltValue,
            'hash_value': encryptHashSHA512(password + saltValue),
            'phone': phone,
            'email': email}
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

@user_mssql.route("/user/updateUserMSSQL", methods=['POST'])
def updateUserMSSQL():
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
        paramList = ['user_id','first_name','last_name','phone']
        paramCheckStringList = ['user_id','first_name','last_name','phone']
        paramCheckNumberList = ['user_skey']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        # userSkey = dataInput['user_skey']
        userID = dataInput['user_id']
        first_name = dataInput['first_name']
        last_name = dataInput['last_name']
        phone = dataInput['phone']
        email = dataInput['email']
        sex = dataInput['sex']
        birthday = dataInput['birthday']
        if 'password' in dataInput:
            password = dataInput['password']
        else:
            password = ''
        if 'picture_base64' in dataInput:
            picture_base64 = dataInput['picture_base64']
        else:
            picture_base64 = ''

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
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
        phone = %(phone)s,
        email = %(email)s,
        """
        if len(password) > 0:
            sql = sql + """\
            user_password = %(user_password)s,
            hash_value = %(hash_value)s,
            """

        if 'picture_base64' in dataInput:
            print('2.11111111')
            sql = sql + """\
            picture = %(picture)s,
            """
        sql = sql + """\
        salt_value = %(salt_value)s
        where user_id = %(user_id)s
        """

        params = {'user_id': userID,
            'user_password': Encrypt(password),
            'first_name': first_name,
            'last_name': last_name,
            'picture': base64.b64decode(picture_base64),
            'salt_value': saltValue,
            'hash_value': encryptHashSHA512(password + saltValue),
            'phone': phone,'email': email,}
        cursor.execute(sql,params)

        sql = """\
        update lis_patient
        set birthday = %(birthday)s,
        sex = %(sex)s,
        phone = %(phone)s,
        email = %(email)s,
        firstname = %(first_name)s,
        lastname = %(last_name)s
        from pc_user_def a inner join lis_patient b on a.patient_skey = b.patient_skey
        where user_id = %(user_id)s
        """

        params = {'user_id': userID,'birthday': birthday,'sex': sex,'phone': phone,'email': email,'first_name': first_name,'last_name': last_name,}
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

@user_mssql.route("/user/deleteUserMSSQL", methods=['POST'])
def deleteUserMSSQL():
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

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
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

@user_mssql.route("/user/updateFromLineUserIDMSSQL", methods=['POST'])
def updateFromLineUserIDMSSQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['user_id','line_user_id']
        paramCheckStringList = ['user_id','line_user_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        # userSkey = dataInput['user_skey']
        userID = dataInput['user_id']
        lineUserID = dataInput['line_user_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
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

        sql = """\
        update pc_user_def
        set line_user_id = null
        where line_user_id = %(line_user_id)s
        """

        params = {'user_id': userID,'line_user_id': lineUserID}
        cursor.execute(sql,params)

        sql = """\
        update pc_user_def
        set line_user_id = %(line_user_id)s
        where user_id = %(user_id)s
        """

        params = {'user_id': userID,'line_user_id': lineUserID}
        cursor.execute(sql,params)
        conn.commit()
        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Update User Line ID เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@user_mssql.route("/user/getUserByLineUserIDMSSQL", methods=['POST'])
def getUserByLineUserIDMSSQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['line_user_id']
        paramCheckStringList = ['line_user_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        lineUserID = dataInput['line_user_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        select user_skey,user_id,first_name,last_name
        from pc_user_def
        where line_user_id = %(line_user_id)s
        """
        params = {'line_user_id': lineUserID}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
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

@user_mssql.route("/user/getUserInfoEmail", methods=['POST'])
def getUserInfoEmail():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['user_id']
        paramCheckStringList = ['user_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        userID = dataInput['user_id']
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        sql = """\
        select a.email, a.first_name + '  ' + isnull(a.last_name,'') as patientname from pc_user_def a
        left join lis_patient b on a.patient_skey = b.patient_skey
        where user_id = %(user_id)s
        """
        params = {'user_id': userID}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        cursor.close()

        if len(data) == 0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid User"

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

@user_mssql.route("/user/sendMailForgotPassword", methods=['POST'])
def sendMailForgotPassword():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['user_id']
        paramCheckStringList = ['user_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        userID = dataInput['user_id']
        mailto = dataInput['email']
        base64Parm = dataInput['base64Parm']
        patientName = dataInput['patientName']
        lang = dataInput['lang']
        print(mailto)

        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()

        sender_email = 'info@innotechlab.co.th'
        sender_password = '1nnt@12345'

        server.login(sender_email, sender_password)

        # subject = 'เปลี่ยนรหัสผ่านในระบบ Innotechlab Web Order COVID-19'
        # message = 'Subject: {}\n\n{}'.format(subject, 'msg')
        # server.sendmail(sender_email,mailto,message)


        msg = MIMEMultipart('alternative')
        print(lang, 'lang')
        if lang == 'th':
            msg['Subject'] = 'เปลี่ยนรหัสผ่านในระบบ Innotechlab Web Order COVID-19'
            msg['From'] = sender_email
            msg['To'] = mailto
            # Create the body of the message (a plain-text and an HTML version).
            text = "เรียน คุณ {}\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org/{}".format(userID, 'msg')
            html = """\
            <html>
            <head></head>
            <body>
                <p>เรียน คุณ {}<br><br>
                Username ของคุณคือ {} หากต้องการตั้งค่ารหัสผ่านใหม่ คลิก<a href="https://www.innotechlab.co.th/Covid-19/ForgotPassword?{}">ที่นี่</a> หรือคัดลอกลิงค์ข้างล่างนี้ในบราวเซอร์ของคุณ<br>
                https://www.innotechlab.co.th/Covid-19/ForgotPassword?{}
                </p>
            </body>
            </html>
            """
        else:
            msg['Subject'] = 'Change password Innotechlab Web Order COVID-19'
            msg['From'] = sender_email
            msg['To'] = mailto
            # Create the body of the message (a plain-text and an HTML version).
            text = "Dear {}\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org/{}".format(userID, 'msg')
            html = """\
            <html>
            <head></head>
            <body>
                <p>Dear {}<br><br>
                User name is {} if you change password click <a href="https://www.innotechlab.co.th/Covid-19/ForgotPassword?{}">here</a> Or copy the link below to your browser<br>
                https://www.innotechlab.co.th/Covid-19/ForgotPassword?{}
                </p>
            </body>
            </html>
            """

        html = html.format(patientName, userID, 'prop1=' + base64Parm, 'prop1=' + base64Parm)

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)
        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
        server.sendmail(sender_email, mailto, msg.as_string())



        server.quit()
        print('Success: Email sent')

        data = 'Y'
        columns = 'Success'
        if len(data) == 0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid User"

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJsonOne(data,columns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        print('Failed: Email sent')
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@user_mssql.route("/user/updateForgetPassowrd", methods=['POST'])
def updateForgetPassowrd():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""


        dataInput = request.json
        paramList = ['user_id']
        paramCheckStringList = ['user_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        # userSkey = dataInput['user_skey']
        userID = dataInput['user_id']
        if 'password' in dataInput:
            password = dataInput['password']
        else:
            password = ''

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
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
        set
        """
        if len(password) > 0:
            sql = sql + """\
            user_password = %(user_password)s,
            hash_value = %(hash_value)s,
            """
        sql = sql + """\
        salt_value = %(salt_value)s
        where user_id = %(user_id)s
        """

        params = {'user_id': userID,
            'user_password': Encrypt(password),
            'salt_value': saltValue,
            'hash_value': encryptHashSHA512(password + saltValue),}
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
