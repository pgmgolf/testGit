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

web_order = Blueprint('web_order', __name__)


@web_order.route("/web_order/addPatientWebOrder", methods=['POST'])
def addPatientWebOrder():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""
        print('golf GGGGGGGGGGGGGGGGGGGGGGGGGG')
        dataInput = request.json
        paramList = ['user_name','first_name','last_name','birth_date','mobile_no','sex_code','agree_condition_flag']
        paramCheckStringList = ['user_name','anonymous_name','first_name','last_name','mobile_no','sex_code']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);
        lineUserID = dataInput["line_user_id"]
        userName = dataInput['user_name']
        anonymousName = dataInput['anonymous_name']
        firstName = dataInput['first_name']
        lastName = dataInput['last_name']
        sexCode = dataInput['sex_code']
        mobileNo = dataInput['mobile_no']
        eMail = dataInput['eMail']
        birthDate = dataInput['birth_date']
        newPassword = dataInput['new_password']
        agreeConditionFlag = dataInput['agree_condition_flag']
        questionnaire1 = dataInput['questionnaire1']
        questionnaire2 = dataInput['questionnaire2']
        questionnaire3 = dataInput['questionnaire3']
        questionnaire4 = dataInput['questionnaire4']
        questionnaire5 = dataInput['questionnaire5']
        lineUserID = dataInput["line_user_id"]

        newPasswordEncrypt = Encrypt(newPassword)
        saltValue = randomStringDigits(20)
        hashValue = encryptHashSHA512(newPassword + saltValue)

        if agreeConditionFlag == False:
            isSuccess = False
            reasonCode = 500
            reasonText = "Error01"
            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]
            msgError = toJsonOne(data,columns)
            return jsonify(msgError)


        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from pc_user_def
        where user_id like %(user_name)s
        """
        params = {'user_name': userName}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows>0:
            isSuccess = False
            reasonCode = 500
            reasonText = userName + " เบอร์โทรศัพท์นี้เคยใช้ลงทะเบียนแล้ว (Mobile no. already.) "

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))
        winSkey = 1

        sql = """\
        EXEC sp_lis_lab_web_order_reg @user_id = %(user_id)s,
        @firstname=%(first_name)s,
        @lastname=%(last_name)s,
        @sex=%(sex)s,
        @birthday=%(birthday)s,
        @id_card='',
        @local_phone=%(local_phone)s,
        @email=%(email)s,
        @date_arrived=%(date_arrived)s,
        @passwordPatient=%(password_patient)s,
        @passwordPatientEncrypt=%(password_patient_encrypt)s,
        @saltValue=%(salt_value)s,
        @hashValue=%(hash_value)s,
        @check_id_card='N',
        @visit='N',
        @collection='N',
        @specimenReceive='N',
        @questionnaire1 = %(questionnaire1)s,
        @questionnaire2 = %(questionnaire2)s,
        @questionnaire3 = %(questionnaire3)s,
        @questionnaire4 = %(questionnaire4)s,
        @questionnaire5 = %(questionnaire5)s,
        @line_user_id=%(line_user_id)s
        ;
        """
        params = {'user_id': userName,
        'first_name': firstName,
        'last_name': lastName,
        'sex': sexCode,
        'birthday': birthDate,
        'local_phone': mobileNo,
        'email': eMail,
        'date_arrived': datetime.datetime.now(),
        'password_patient': newPassword,
        'password_patient_encrypt': newPasswordEncrypt,
        'salt_value': saltValue,
        'hash_value': hashValue,
        'questionnaire1': questionnaire1,
        'questionnaire2': questionnaire2,
        'questionnaire3': questionnaire3,
        'questionnaire4': questionnaire4,
        'questionnaire5': questionnaire5,
        'line_user_id': lineUserID
        }
        cursor.execute(sql,params)
        conn.commit()

        ''' data = cursor.fetchall()
        print("#####################################################")
        print(data)
        print("#####################################################")
        columns = [column[0] for column in cursor.description]

        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(data,columns))]
        return jsonify(toJsonOne(displayData,displayColumns)) '''



        returnDataColumns = ['app_skey','win_skey']
        returnData = [(userName,winSkey)]

        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'Register Complete.',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
@web_order.route("/web_order/retrieveAppointment", methods=['POST'])
def retrieveAppointment():
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
        paramList = ['temp']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        temp = dataInput['temp']
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_lis_web_appointment_retrieve @type = %(type)s, @user_id = %(user_id)s
        """
        params = {'type': 'header', 'user_id': userID}
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
@web_order.route("/web_order/retrieveAppointmentDetail", methods=['POST'])
def retrieveAppointmentDetail():
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
        paramList = ['app_id']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appointmentId = dataInput['app_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_lis_web_appointment_retrieve @type = %(type)s, @user_id = %(user_id)s, @appointment_id = %(appointment_id)s
        """
        params = {'type': 'detail', 'user_id': userID, 'appointment_id': appointmentId}
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
@web_order.route("/web_order/retrieveSlotTime", methods=['POST'])
def retrieveSlotTime():
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
        paramList = ['appointment_date']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appointmentDate = dataInput['appointment_date']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_lis_web_app_slot_time @appointment_date = %(appointment_date)s
        """
        params = {'appointment_date': appointmentDate}
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
@web_order.route("/web_order/addAppointmentSlot", methods=['POST'])
def addAppointmentSlot():
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
        paramList = ['slot_date', 'slot_time']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        slotDate = dataInput['slot_date']
        slotTime = dataInput['slot_time']
        appointmentDate = slotDate + " " + slotTime
        print(appointmentDate)
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()


        sql = """\
        select count(1) from lis_web_appointment a
        inner join pc_user_def b on a.patient_skey = b.patient_skey
        where user_id = %(user_id)s and status = 'OP';
        """
        params = {'user_id': userID}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows>0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Duplicate2"
            # reasonText = "คุณได้ทำการนัดหมายวันเวลานี้แล้ว (Appointment date is Duplicate.) "

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        select count(1) from lis_web_appointment a
        inner join pc_user_def b on a.patient_skey = b.patient_skey
        where user_id = %(user_id)s and
        appointment_date = %(appointment_date)s and status = 'OP';
        """
        params = {'user_id': userID, 'appointment_date': appointmentDate}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows>0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Duplicate1"
            # reasonText = "คุณได้ทำการนัดหมายวันเวลานี้แล้ว (Appointment date is Duplicate.) "

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))
        
        sql = """\
        EXEC sp_lis_web_app_slot_time_upd @user_id = %(user_id)s, @appointment_date = %(appointment_date)s;
        """
        params = {'user_id': userID, 'appointment_date': appointmentDate}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        conn.commit()
        cursor.close()
        ''' displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(data,columns))] '''
        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'Appointment Complete.', toJson(data,columns))]

        print(data)
        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,e.message if hasattr(e, 'message') else str(e))]
        return jsonify(toJsonOne(errData,errColumns))

@web_order.route("/web_order/cancelAppointmentSlot", methods=['POST'])
def cancelAppointmentSlot():
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
        paramList = ['appointment_id']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appointmentId = dataInput['appointment_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        update lis_web_appointment set status = 'CA', date_changed = %(date_changed)s, user_changed = %(user_id)s
        where appointment_id =  %(appointment_id)s;
        """
        params = {'user_id': userID, 'appointment_id': appointmentId, 'date_changed': now}
        cursor.execute(sql,params)

        conn.commit()
        cursor.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Cancel appointment complete.')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,e.message if hasattr(e, 'message') else str(e))]
        return jsonify(toJsonOne(errData,errColumns))

@web_order.route("/web_order/retrieveAppointmentOrderEntry", methods=['POST'])
def retrieveAppointmentOrderEntry():
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
        paramList = ['flagDate']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        flagDate = dataInput['flagDate']
        dateFrom = dataInput['dateFrom']
        dateTo = dataInput['dateTo']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_lis_web_order_entry_retrieve @type = %(type)s, @user_id = %(user_id)s,
        @flag_date = %(flagDate)s, @date_from = %(date_from)s, @date_to = %(date_to)s
        """
        params = {'type': 'header', 'user_id': userID, 'flagDate': flagDate,
        'date_from': dateFrom, 'date_to': dateTo}
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
@web_order.route("/web_order/retrieveAppointmentOrderEntryDetail", methods=['POST'])
def retrieveAppointmentOrderEntryDetail():
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
        paramList = ['app_id']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appointmentId = dataInput['app_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_lis_web_order_entry_retrieve @type = %(type)s, @user_id = %(user_id)s, @appointment_id = %(appointment_id)s
        """
        params = {'type': 'detail', 'user_id': userID, 'appointment_id': appointmentId}
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
