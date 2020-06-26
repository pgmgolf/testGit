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

visit_mysql = Blueprint('visit_mysql', __name__)

@visit_mysql.route("/visit/addVisitMySQL", methods=['POST'])
def addVisitMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    userID = returnUserToken["data"]["user_id"]
    now = datetime.datetime.now()
    aryear = now.year
    armonth = now.month
    arday = now.day
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['patient_skey']
    paramCheckStringList = ['patient_skey']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    patientSkey = dataInput['patient_skey']
    note = dataInput['note']
    date_arrived = dataInput['date_arrived']
    facility_cd = dataInput['facility_cd']


    status = dataInput['status']
    # print(datetime.datetime.now().strftime('%Y%m%d'), 'datetime.datetime.now()')
    # print(date_arrived.strftime('%Y%m%d'), 'date_arrived')
    # if date_arrived.strftime('%Y%m%d') > datetime.datetime.now().strftime('%Y%m%d'):
    #     status = 'PE'

    Priority = dataInput['Priority']
    initialSymptoms = dataInput['initialSymptoms']
    bodyWeight = dataInput['bodyWeight']
    bodyHeight = dataInput['bodyHeight']
    bodyTemperature = dataInput['bodyTemperature']
    systolic = dataInput['systolic']
    diastolic = dataInput['diastolic']
    pulse = dataInput['pulse']
    respiratoryRate = dataInput['respiratoryRate']
    spo2 = dataInput['spo2']

    visit_skey = getNextSequenceMySQL('lis_visit','lis_visit','visit_skey')
    visit_id = getSequenceNumberMySQL('lis_visit','',aryear,armonth,arday,'0000','00','00','00','Y','Y','Y','','','-')

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_visit where visit_id like %s"
    cursor.execute(sql,visit_id)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Visit Id already " + visit_id
        visitId = ''
        visitSkey = ''
        errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
        errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
        return jsonify(toJsonOne(errData,errColumns))

    if not bodyWeight:
        bodyWeight = None
    else:
        if not bodyWeight.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Body Weight is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not bodyHeight:
        bodyHeight = None
    else:
        if not bodyHeight.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Body Height is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not bodyTemperature:
        bodyTemperature = None
    else:
        if not bodyTemperature.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Body Temperature is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not systolic:
        systolic = None
    else:
        if not systolic.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Systolic is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not diastolic:
        diastolic = None
    else:
        if not diastolic.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Diastolic is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not pulse:
        pulse = None
    else:
        if not pulse.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Pulse is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not respiratoryRate:
        respiratoryRate = None
    else:
        if not respiratoryRate.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Respiratory Rate is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not spo2:
        spo2 = None
    else:
        if not spo2.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "SpO2 is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))



    sql = """\
    insert into lis_visit
    (visit_skey, visit_id, patient_skey, logical_location_cd,
    physician_no, date_arrived, status, date_created, user_created,
    date_changed, user_changed, facility_cd, hospital_visit_id, register, oqueue, note,
    priority_cd, initial_symptoms, body_weight, body_height, body_temperature,
    systolic, diastolic, pulse, respiratory_rate, spo2)
    values(%(visit_skey)s,%(visit_id)s,%(patient_skey)s,'N/A',
    null,%(date_arrived)s,%(status)s,NOW(), %(userID)s,
    NOW(), %(userID)s, %(facility_cd)s, null, null, null, %(note)s,
    %(Priority)s, %(initialSymptoms)s, %(bodyWeight)s, %(bodyHeight)s, %(bodyTemperature)s,
    %(systolic)s, %(diastolic)s, %(pulse)s ,%(respiratoryRate)s, %(spo2)s)
    """
    params = {'visit_skey': visit_skey,'visit_id': visit_id,
    'patient_skey': patientSkey,'date_arrived': date_arrived, 'status': status,
    'userID': userID, 'facility_cd': facility_cd, 'note': note,
    'Priority': Priority, 'initialSymptoms': initialSymptoms, 'bodyWeight': bodyWeight,
    'bodyHeight': bodyHeight, 'bodyTemperature': bodyTemperature,
    'systolic': systolic, 'diastolic': diastolic, 'pulse': pulse, 'respiratoryRate': respiratoryRate,
    'spo2': spo2}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()
    visitId = visit_id
    visitSkey = visit_skey
    displayColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
    displayData = [(isSuccess,reasonCode,'สร้าง visit เรียบร้อย',visitId,visitSkey)]

    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/addEpisodeMySQL", methods=['POST'])
def addEpisodeMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    userID = returnUserToken["data"]["user_id"]
    now = datetime.datetime.now()
    aryear = now.year
    armonth = now.month
    arday = now.day

    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['visit_skey']
    paramCheckStringList = ['visit_skey']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    visit_skey = dataInput['visit_skey']
    appointment_date = dataInput['appointment_date']
    clinic_skey = dataInput['clinic_skey']
    physician_no = dataInput['physician_no']
    patient_rights_cd = dataInput['patient_rights_cd']
    status = dataInput['status']
    duration = dataInput['duration']
    remark = dataInput['remark']

    ep_skey = getNextSequenceMySQL('episode','episode','ep_skey')
    ep_id = getSequenceNumberMySQL('episode','',aryear,armonth,arday,'0000','00','00','00','Y','Y','Y','','','-')
    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from episode where ep_id like %s"
    cursor.execute(sql,ep_id)
    (number_of_rows,)=cursor.fetchone()
    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "ep Id already " + ep_id

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    insert into episode
    (ep_skey, ep_id, visit_skey, appointment_date,
    clinic_skey, physician_no, patient_rights_cd, status, date_created, user_created,
    date_changed, user_changed, duration, remark)
    values(%(ep_skey)s,%(ep_id)s,%(visit_skey)s,%(appointment_date)s,
    %(clinic_skey)s,%(physician_no)s,%(patient_rights_cd)s,%(status)s,NOW(), %(userID)s,
    NOW(), %(userID)s, %(duration)s, %(remark)s)
    """
    params = {'ep_skey': ep_skey,'ep_id': ep_id,
    'visit_skey': visit_skey,'appointment_date': appointment_date, 'clinic_skey': clinic_skey,
    'physician_no': physician_no,'patient_rights_cd': patient_rights_cd,
    'status': status,'userID': userID,'duration': duration,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()
    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้าง Episode เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/updateVisitMySQL", methods=['POST'])
def updateVisitMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);
    userID = returnUserToken["data"]["user_id"]
    now = datetime.datetime.now()
    aryear = now.year
    armonth = now.month
    arday = now.day
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['visit_skey']
    paramCheckStringList = ['visit_skey']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    visit_skey = dataInput['visit_skey']
    note = dataInput['note']
    date_arrived = dataInput['date_arrived']
    facility_cd = dataInput['facility_cd']
    Priority = dataInput['Priority']
    initialSymptoms = dataInput['initialSymptoms']
    bodyWeight = dataInput['bodyWeight']
    bodyHeight = dataInput['bodyHeight']
    bodyTemperature = dataInput['bodyTemperature']
    systolic = dataInput['systolic']
    diastolic = dataInput['diastolic']
    pulse = dataInput['pulse']
    respiratoryRate = dataInput['respiratoryRate']
    spo2 = dataInput['spo2']
    statusOpd = dataInput['statusOpd']
    # appointmentDate = dataInput['appointmentDate']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_visit where visit_skey = %s"
    cursor.execute(sql,visit_skey)
    (number_of_rows,)=cursor.fetchone()
    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid visit " + str(visit_skey)

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_visit set facility_cd = %(facility_cd)s, note = %(note)s, priority_cd = %(Priority)s,
    initial_symptoms = %(initialSymptoms)s, body_weight = %(bodyWeight)s, body_height = %(bodyHeight)s,
    body_temperature = %(bodyTemperature)s, systolic = %(systolic)s, diastolic = %(diastolic)s,
    pulse = %(pulse)s, respiratory_rate = %(respiratoryRate)s, spo2 = %(spo2)s,
    date_arrived = %(date_arrived)s,
    date_changed = NOW(), user_changed = %(userID)s,
    lis_visit.status = %(statusOpd)s
    where visit_skey = %(visit_skey)s
    """
    params = {'visit_skey': visit_skey,
    'date_arrived': date_arrived,
    'userID': userID, 'facility_cd': facility_cd, 'note': note,
    'Priority': Priority, 'initialSymptoms': initialSymptoms, 'bodyWeight': bodyWeight,
    'bodyHeight': bodyHeight, 'bodyTemperature': bodyTemperature,
    'systolic': systolic, 'diastolic': diastolic, 'pulse': pulse, 'respiratoryRate': respiratoryRate,
    'spo2': spo2, 'statusOpd': statusOpd}
    cursor.execute(sql,params)

    if statusOpd == 'AV':
        sql = """\
        update episode set
        status =  %(status)s, appointment_date = CONCAT(SUBSTRING(%(date_arrived)s, 1, INSTR(%(date_arrived)s,'T') - 1),' ', TIME(appointment_date)),
        date_changed = NOW(), user_changed = %(userID)s
        where status in ('PE','OP') and visit_skey = %(visit_skey)s
        """

        params = {'visit_skey': visit_skey,
        'status': statusOpd,'userID': userID,'date_arrived': date_arrived,}
        cursor.execute(sql,params)


    conn.commit()
    cursor.close()
    conn.close()
    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไข visit เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/updateEpisodeMySQL", methods=['POST'])
def updateEpisodeMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    userID = returnUserToken["data"]["user_id"]
    now = datetime.datetime.now()
    aryear = now.year
    armonth = now.month
    arday = now.day

    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['visit_skey']
    paramCheckStringList = ['visit_skey']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    visit_skey = dataInput['visit_skey']
    ep_skey = dataInput['ep_skey']
    physician_no = dataInput['physician_no']
    clinic_skey = dataInput['clinic_skey']
    appointment_date = dataInput['appointment_date']
    patient_rights_cd = dataInput['patient_rights_cd']
    status = dataInput['status']
    duration = dataInput['duration']
    remark = dataInput['remark']
    print(remark, '===================d')


    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from episode where ep_skey = %s"
    cursor.execute(sql,ep_skey)
    (number_of_rows,)=cursor.fetchone()
    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Ep " + str(ep_skey)

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update episode set appointment_date =  %(appointment_date)s, clinic_skey =  %(clinic_skey)s,
    physician_no =  %(physician_no)s, patient_rights_cd =  %(patient_rights_cd)s,
    status =  %(status)s, duration =  %(duration)s, remark =  %(remark)s,
    date_changed = NOW(), user_changed = %(userID)s
    where ep_skey = %(ep_skey)s
    """

    params = {'ep_skey': ep_skey,
    'appointment_date': appointment_date, 'clinic_skey': clinic_skey,
    'physician_no': physician_no,'patient_rights_cd': patient_rights_cd,
    'status': status,'userID': userID,'duration': duration,'remark': remark}
    cursor.execute(sql,params)
    print(params, '========')
    conn.commit()
    cursor.close()
    conn.close()
    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูล Episode เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/addVisitAndEpisodeMySQL", methods=['POST'])
def addVisitAndEpisodeMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    userID = returnUserToken["data"]["user_id"]
    now = datetime.datetime.now()
    aryear = now.year
    armonth = now.month
    arday = now.day
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['patient_skey']
    paramCheckStringList = ['patient_skey']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    patientSkey = dataInput['patient_skey']
    note = dataInput['note']
    date_arrived = dataInput['date_arrived']
    facility_cd = dataInput['facility_cd']
    status = dataInput['status']
    # print(datetime.datetime.now().strftime('%Y%m%d'), 'datetime.datetime.now()')
    # print(datetime.strptime(date_arrived, '%b %d %Y %I:%M%p'), 'date_arrived')
    #
    # if datetime.strptime(date_arrived, '%b %d %Y %I:%M%p').strftime('%Y%m%d') > datetime.datetime.now().strftime('%Y%m%d'):
    #     status = 'PE'
    Priority = dataInput['Priority']
    initialSymptoms = dataInput['initialSymptoms']
    bodyWeight = dataInput['bodyWeight']
    bodyHeight = dataInput['bodyHeight']
    bodyTemperature = dataInput['bodyTemperature']
    systolic = dataInput['systolic']
    diastolic = dataInput['diastolic']
    pulse = dataInput['pulse']
    respiratoryRate = dataInput['respiratoryRate']
    spo2 = dataInput['spo2']

    visit_skey = getNextSequenceMySQL('lis_visit','lis_visit','visit_skey')
    visit_id = getSequenceNumberMySQL('lis_visit','',aryear,armonth,arday,'0000','00','00','00','Y','Y','Y','','','-')
    ep_skey = getNextSequenceMySQL('episode','episode','ep_skey')
    ep_id = getSequenceNumberMySQL('episode','',aryear,armonth,arday,'0000','00','00','00','Y','Y','Y','','','-')
    appointment_date = dataInput['appointment_date']
    clinic_skey = dataInput['clinic_skey']
    physician_no = dataInput['physician_no']
    patient_rights_cd = dataInput['patient_rights_cd']
    statusEp = dataInput['statusEp']
    duration = dataInput['duration']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_visit where visit_id like %s"
    cursor.execute(sql,visit_id)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Visit Id already " + visit_id
        visitId = ''
        visitSkey = ''
        errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
        errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
        return jsonify(toJsonOne(errData,errColumns))

    if not bodyWeight:
        bodyWeight = None
    else:
        if not bodyWeight.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Body Weight is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not bodyHeight:
        bodyHeight = None
    else:
        if not bodyHeight.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Body Height is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not bodyTemperature:
        bodyTemperature = None
    else:
        if not bodyTemperature.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Body Temperature is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not systolic:
        systolic = None
    else:
        if not systolic.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Systolic is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not diastolic:
        diastolic = None
    else:
        if not diastolic.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Diastolic is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not pulse:
        pulse = None
    else:
        if not pulse.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Pulse is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not respiratoryRate:
        respiratoryRate = None
    else:
        if not respiratoryRate.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "Respiratory Rate is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))
    if not spo2:
        spo2 = None
    else:
        if not spo2.isnumeric():
            isSuccess = False
            reasonCode = 500
            reasonText = "SpO2 is not type Float!"
            visitId = ''
            visitSkey = ''
            errColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
            errData = [(isSuccess,reasonCode,reasonText,visitId,visitSkey)]
            return jsonify(toJsonOne(errData,errColumns))



    sql = """\
    insert into lis_visit
    (visit_skey, visit_id, patient_skey, logical_location_cd,
    physician_no, date_arrived, status, date_created, user_created,
    date_changed, user_changed, facility_cd, hospital_visit_id, register, oqueue, note,
    priority_cd, initial_symptoms, body_weight, body_height, body_temperature,
    systolic, diastolic, pulse, respiratory_rate, spo2)
    values(%(visit_skey)s,%(visit_id)s,%(patient_skey)s,'N/A',
    null,%(date_arrived)s,%(status)s,NOW(), %(userID)s,
    NOW(), %(userID)s, %(facility_cd)s, null, null, null, %(note)s,
    %(Priority)s, %(initialSymptoms)s, %(bodyWeight)s, %(bodyHeight)s, %(bodyTemperature)s,
    %(systolic)s, %(diastolic)s, %(pulse)s ,%(respiratoryRate)s, %(spo2)s)
    """
    params = {'visit_skey': visit_skey,'visit_id': visit_id,
    'patient_skey': patientSkey,'date_arrived': date_arrived, 'status': status,
    'userID': userID, 'facility_cd': facility_cd, 'note': note,
    'Priority': Priority, 'initialSymptoms': initialSymptoms, 'bodyWeight': bodyWeight,
    'bodyHeight': bodyHeight, 'bodyTemperature': bodyTemperature,
    'systolic': systolic, 'diastolic': diastolic, 'pulse': pulse, 'respiratoryRate': respiratoryRate,
    'spo2': spo2}
    cursor.execute(sql,params)
    sql = """\
    insert into episode
    (ep_skey, ep_id, visit_skey, appointment_date,
    clinic_skey, physician_no, patient_rights_cd, status, date_created, user_created,
    date_changed, user_changed, duration, remark)
    values(%(ep_skey)s,%(ep_id)s,%(visit_skey)s,%(appointment_date)s,
    %(clinic_skey)s,%(physician_no)s,%(patient_rights_cd)s,%(status)s,NOW(), %(userID)s,
    NOW(), %(userID)s, %(duration)s, %(remark)s)
    """
    params = {'ep_skey': ep_skey,'ep_id': ep_id,
    'visit_skey': visit_skey,'appointment_date': appointment_date, 'clinic_skey': clinic_skey,
    'physician_no': physician_no,'patient_rights_cd': patient_rights_cd,
    'status': statusEp,'userID': userID,'duration': duration,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()
    visitId = visit_id
    visitSkey = visit_skey
    displayColumns = ['isSuccess','reasonCode','reasonText','visitId','visitSkey']
    displayData = [(isSuccess,reasonCode,'สร้าง visit เรียบร้อย',visitId,visitSkey)]

    return jsonify(toJsonOne(displayData,displayColumns))


@visit_mysql.route("/visit/getPhysicianMySQL", methods=['POST'])
def getPhysician ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select physician_no,
    CONCAT(COALESCE(employee.first_name,''),' ',COALESCE(employee.middle_name,''),' ',COALESCE(employee.last_name,'')) AS fullName
    from patho_physician
    inner join employee on patho_physician.employee_no = employee.employee_no
    """
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@visit_mysql.route("/visit/getPhysicianAppointmentMySQL", methods=['POST'])
def getPhysicianAppointment ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    physicianNo = dataInput['physicianNo']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select physician_no,
        CONCAT(COALESCE(employee.first_name,''),' ',COALESCE(employee.middle_name,''),' ',COALESCE(employee.last_name,'')) AS name,
        to_base64(picture) as picture_base64,
        '' as value,
    	 'ว่าง' as calories,
        'ว่าง' as fat,
        'จองแล้ว' as carbs,
        '' as protein,
        '' as sodium,
        '' as calcium
    from patho_physician
    inner join employee on patho_physician.employee_no = employee.employee_no
    inner join pc_user_def on pc_user_def.employee_no = employee.employee_no
    where patho_physician.physician_no = %(physicianNo)s
    """
    params = {'physicianNo': physicianNo}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/getTimeSlotMySQL", methods=['POST'])
def getTimeSlot ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    dateTimeSlot = dataInput['dateTimeSlot']
    physicianNo = dataInput['physicianNo']


    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select T.date, CAST(T.FromTime as CHAR(5)) as FromTime, CAST(T.ToTime as CHAR(5)) as ToTime,
    CONCAT(COALESCE(CAST(T.FromTime as CHAR(5)),''),' - ',COALESCE(CAST(T.ToTime as CHAR(5)),'')) as FromToTime,
    (case when exists
        (
        		select 1 from episode E
        		inner join timeslot_physician P on E.physician_no = P.physician_no
        		where E.physician_no = %(physicianNo)s and P.timeslot_skey = T.timeslot_skey
        )
		  then
			 (case when exists
		        (
		            select 1 from episode A
		            where physician_no = %(physicianNo)s and
		            DATE_FORMAT(A.appointment_date,'%%Y-%%m-%%d') = T.date and
		            STR_TO_DATE(DATE_FORMAT(A.appointment_date,'%%H:%%i'), '%%H:%%i:%%p') < T.ToTime and
		            DATE_ADD(STR_TO_DATE(DATE_FORMAT(A.appointment_date,'%%H:%%i'), '%%H:%%i:%%p'), INTERVAL A.duration minute) > T.FromTime
		        )
		        then
                    'จอง'
                else 'ว่าง' end)
          else
		  	 (case when exists
		  	 	(
		  	 		select 1 from timeslot_physician PP where physician_no = %(physicianNo)s and PP.timeslot_skey = T.timeslot_skey
		  	 	)
		  	  then 'ว่าง'
              else ''
              end)
		  end) as Available,
          (select
		  count(1)
		  from episode A
        where physician_no = %(physicianNo)s and
        DATE_FORMAT(A.appointment_date,'%%Y-%%m-%%d') = T.date and
        STR_TO_DATE(DATE_FORMAT(A.appointment_date,'%%H:%%i'), '%%H:%%i:%%p') < T.ToTime and
        DATE_ADD(STR_TO_DATE(DATE_FORMAT(A.appointment_date,'%%H:%%i'), '%%H:%%i:%%p'), INTERVAL A.duration minute) > T.FromTime) as allocate_count
    from TimeSlot T
    where T.date = %(dateTimeSlot)s
    order by T.FromTime
    """
    params = {'dateTimeSlot': dateTimeSlot, 'physicianNo': physicianNo}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/getTimeSlotFromTimeMySQL", methods=['POST'])
def getTimeSlotFromTime ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    dateTimeSlot = dataInput['dateTimeSlot']
    physicianNo = dataInput['physicianNo']
    epSkey = dataInput['epSkey']

    conn = mysql.connect()
    cursor = conn.cursor()

    sql = """\
    select CAST(T.FromTime as CHAR(5)) as FromTime, CAST(T.ToTime as CHAR(5)) as ToTime
        from TimeSlot T
        inner join timeslot_physician P on T.timeslot_skey = P.timeslot_skey
        where P.physician_no = %(physicianNo)s and T.date = %(dateTimeSlot)s
        order by T.FromTime
    """

    params = {'dateTimeSlot': dateTimeSlot, 'physicianNo': physicianNo, 'epSkey': epSkey}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@visit_mysql.route("/visit/getClinicMySQL", methods=['POST'])
def getClinic ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select clinic_skey, clinic_name
    from clinic_master
    order by clinic_skey
    """
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@visit_mysql.route("/visit/getPriorityMySQL", methods=['POST'])
def getPriority ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select priority_cd, priority_desc,hooper from patho_priority order by hooper
    """
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))


@visit_mysql.route("/visit/retrieveEpisodeMySQL", methods=['POST'])
def retrieveEpisodeMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    visitSkey = dataInput['visitSkey']

    if not visitSkey:
        visitSkey = '%'

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select ep_skey, ep_id, visit_skey, appointment_date, episode.clinic_skey, episode.physician_no, patient_rights_cd, episode.status,
    episode.date_created, episode.user_created, episode.date_changed, episode.user_changed,episode.status as statusEpisode,
    clinic_master.clinic_name,
    CONCAT(COALESCE(employee.first_name,''),' ',COALESCE(employee.middle_name,''),' ',COALESCE(employee.last_name,'')) AS fullName,
    episode.physician_no as physician, episode.clinic_skey as clinic, episode.patient_rights_cd as paymentPlanEp,
    DATE_FORMAT(episode.appointment_date,'%%H:%%i') as timeClinic, episode.duration, episode.remark,
    (CASE episode.status
    WHEN 'PE' THEN 'Pending'
    WHEN 'OP' THEN 'Open'
    WHEN 'CA' THEN 'Cancel'
    WHEN 'AV' THEN 'Arrived'
    WHEN 'PC' THEN 'Process'
    WHEN 'DC' THEN 'Discharge'
    WHEN 'DP' THEN 'Departed '
    END) as statusEpisodeDesc
    from episode
    inner join patho_physician on patho_physician.physician_no = episode.physician_no
    inner join employee on patho_physician.employee_no = employee.employee_no
    left join clinic_master on episode.clinic_skey = clinic_master.clinic_skey
    where visit_skey = %(visitSkey)s
    order by episode.ep_skey
    """
    params = {'visitSkey': visitSkey}
    cursor.execute(sql,params)


    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/retrieveVisitMySQL", methods=['POST'])
def retrieveVisitMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    visitSkey = dataInput['visitSkey']
    dateArrived = dataInput['date_arrived']

    if not visitSkey:
        visitSkey = '%'

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select v.patient_skey, patient.patient_id, v.visit_skey,v.status as statusOpd, v.visit_id,anonymous_name, anonymous_flag,
     DATE_FORMAT(v.date_created,'%%d/%%m/%%Y') as date_created,patient.date_created as dateCreated,
    CONCAT(COALESCE(patho_prefix.prefix_desc,''),' ',COALESCE(patient.firstname,''),' ',COALESCE(patient.middle_name,''),' ',COALESCE(patient.lastname,'')) AS fullName,
    COALESCE(patient.id_card,patient.passport_id) AS id,
    patient.hn,
    TRUNCATE((DATEDIFF(CURRENT_DATE, DATE_FORMAT(birthday,'%%Y-%%m-%%d'))/365),0) AS ageInYears,
    DATE_FORMAT(v.date_arrived,'%%Y-%%m-%%d') date_arrived_string,
    DATE_FORMAT(v.date_arrived,'%%d/%%m/%%Y') date_arrived_display,
    v.date_arrived,
    patient.allergy as allergic, patient.disease as congenital_disease, v.initial_symptoms,
     v.body_weight, v.body_height, v.body_temperature, v.systolic,
     v.diastolic, v.pulse, v.respiratory_rate, v.spo2, v.priority_cd, pp.priority_desc, v.note,
     to_base64(picture) as picture_base64,
     sex.sex_desc as sex,
     DATE_FORMAT(birthday,'%%Y-%%m-%%d') as birthday,
     patient.status,
     (CASE v.status
     WHEN 'PE' THEN 'Pending'
     WHEN 'OP' THEN 'Open'
     WHEN 'CA' THEN 'Cancel'
     WHEN 'AV' THEN 'Arrived'
     WHEN 'PC' THEN 'Process'
     WHEN 'DC' THEN 'Discharge'
     WHEN 'MD' THEN 'Med Discharge'
     END) as statusDesc,
     v.facility_cd, v.status as statusOpd,patient.payment_plan_cd,
     patient.prefix, patho_prefix.prefix_desc, patient.firstname, patient.middle_name, patient.lastname, id_card, passport_id,lis_payment_plan.description as paymentPlanDesc,
     patient.race, patient.nationality,patient.email,
     address.street_1,address.street_2,address.street_3,address.street_4,address.city,
     address.state,r_state_province.name as provinceDesc,
     address.country_skey, r_country.description as countryDesc,
     address.zip_postal_code, patient.phone,
     patient_relation.patient_relation_skey,
     patient_relation.prefix as prefixRelation,  prefix_relation.prefix_desc as PrefixDescRelation,
     patient_relation.firstname as firstNameRelation, patient_relation.middle_name as middleNameRelation, patient_relation.lastname as LastNameRelation,
     patient_relation.sex as sexRelation , sex_relation.sex_desc as sexDescRelation,
     patient_relation.relation_cd, relation.description as relationDesc,
     addressRelation.street_1 as street1Relation,addressRelation.street_2 as street2Relation,
     addressRelation.city as cityRelation,addressRelation.state as stateRelation,
     addressRelation.country_skey as CountryRelation,addressRelation.zip_postal_code as zipCodeRelation,addressRelation.local_phone as localPhoneRelation,
     r_state_provinceRelation.name as provinceRelationDesc,r_countryRelation.description as countryRelationDesc
     from lis_visit v
     inner join lis_patient patient on v.patient_skey = patient.patient_skey
     inner join patho_prefix on patho_prefix.prefix_cd = patient.prefix
     inner join patho_sex as sex on sex.sex_cd = patient.sex
     left join patho_priority pp on v.priority_cd = pp.priority_cd
     left join lis_payment_plan on patient.payment_plan_cd = lis_payment_plan.code
     left join lis_patient_address on lis_patient_address.patient_skey = patient.patient_skey
    left join address on lis_patient_address.address_skey = address.address_skey
    left join r_state_province on address.state = r_state_province.state_province_skey
    left join r_country on address.country_skey = r_country.country_skey
    left join lis_religion on patient.religion_cd = lis_religion.code
    left join lis_graduate on patient.graduate_cd = lis_graduate.code
    left join lis_blood_abo on patient.blood_abo_cd = lis_blood_abo.code
    left join lis_blood_rh on patient.blood_rh_cd = lis_blood_rh.code
    left join lis_occupation on patient.occupation_cd = lis_occupation.code
    left join lis_relationship_status on patient.relationship_cd = lis_relationship_status.code
    left join lis_patient_relation as patient_relation on patient.patient_skey = patient_relation.patient_skey
    left join patho_prefix prefix_relation on patient_relation.prefix = prefix_relation.prefix_cd
    left join patho_sex as sex_relation on patient_relation.sex = sex_relation.sex_cd
    left join relation on patient_relation.relation_cd = relation.code
    left join address addressRelation on patient_relation.address_skey = addressRelation.address_skey
    left join r_state_province as r_state_provinceRelation on addressRelation.state = r_state_provinceRelation.state_province_skey
    left join r_country as r_countryRelation on addressRelation.country_skey = r_countryRelation.country_skey
    where v.visit_skey like  %(visitSkey)s and v.status <> 'PE'
    and DATE_FORMAT(v.date_arrived,'%%Y-%%m-%%d') like  %(dateArrived)s
     order by visit_skey
    """
     # where v.visit_skey like  %(visitSkey)s
    params = {'visitSkey': visitSkey, 'dateArrived': dateArrived}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()

    indexVisitSkey = columns.index('visit_skey')
    newData = []

    for row in data:
        listRow = list(row)

        sql = """\
        select episode.ep_id, DATE_FORMAT(episode.appointment_date,'%%d/%%m/%%Y') as appointment_date, clinic_master.clinic_name,
         DATE_FORMAT(appointment_date,'%%H:%%i') as appointment_time,
         CONCAT(COALESCE(employee.first_name,''),' ',COALESCE(employee.middle_name,''),' ',COALESCE(employee.last_name,'')) AS physician_name
          ,(CASE episode.status
          WHEN 'PE' THEN 'Pending'
          WHEN 'OP' THEN 'Open'
          WHEN 'CA' THEN 'Cancel'
          WHEN 'AV' THEN 'Arrived'
          WHEN 'PC' THEN 'Process'
          WHEN 'DC' THEN 'Discharge'
          WHEN 'DP' THEN 'Departed '
          END) as statusEpisodeDesc
        from episode
        inner join clinic_master on clinic_master.clinic_skey = episode.clinic_skey
        inner join patho_physician on episode.physician_no = patho_physician.physician_no
        inner join employee on patho_physician.employee_no = employee.employee_no
        where episode.visit_skey = %s
        """
        cursorLogicalWindow = conn.cursor()
        cursorLogicalWindow.execute(sql,row[indexVisitSkey])

        dataLogicalWindow = cursorLogicalWindow.fetchall()
        columnsLogicalWindow = [column[0] for column in cursorLogicalWindow.description]
        episode = toJson(dataLogicalWindow,columnsLogicalWindow)
        if 'episode' not in columns:
            columns.append('episode')
        listRow.append(episode)
        newData.append(listRow)
        cursorLogicalWindow.close()

    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(newData,columns))]
    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/updateEpStatusMySQL", methods=['POST'])
def updateEpStatusMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['ep_skey']
    paramCheckStringList = ['ep_skey']

    # payload = getUserToken(request.headers.get('Authorization'))
    # userID = payload['user_id']

    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    userID = returnUserToken["data"]["user_id"]

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    ep_skey = dataInput['ep_skey']
    status = dataInput['status']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from episode where ep_skey like %s"
    cursor.execute(sql,ep_skey)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid EP " + str(ep_skey)

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update episode set status =  %(status)s,
    date_changed = NOW(), user_changed = %(userID)s
    where ep_skey = %(ep_skey)s
    """
    params = {'ep_skey': ep_skey,'status': status,'userID': userID}
    cursor.execute(sql,params)

    if (status == "PC") or (status == "DC"):
        sql = """\
        update lis_visit set status = %(status)s,date_changed = NOW(), user_changed = %(userID)s
        where visit_skey in
        (select episode.visit_skey from episode where ep_skey = %(ep_skey)s)
        """
        params = {'ep_skey': ep_skey,'status': status,'userID': userID}
        cursor.execute(sql,params)

    # if status == "PC":
    #     print('Easy')
    # elif status == "PC":
    #     print('Medium')
    # elif level == '3':
    #     print('Hard')
    # elif level == '4':
    #     print('Expert')
    # else:
    #     print('Invalid level selected')

    conn.commit()
    cursor.close()
    conn.close()

    # print(session['message'])
    if status == "OP":
        statusDesc = "Open"
    elif status == "AV":
        statusDesc = "Arrived"
    elif status == "PC":
        statusDesc = "Process"
    elif status == "DP":
        statusDesc = "Departed"
    elif status == "DC":
        statusDesc = "Discharge"
    elif status == "CA":
        statusDesc = "Cancel"


    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขสถานะเป็น : ' + statusDesc)]

    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/retrieveVisitAppointmentMySQL", methods=['POST'])
def retrieveVisitAppointmentMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    patientSkey = dataInput['patientSkey']
    dateArrived = dataInput['date_arrived']
    #
    if not patientSkey:
        patientSkey = '%'
    if not dateArrived:
        dateArrived = '%'

    conn = mysql.connect()
    cursor = conn.cursor()

    sql = """\
    select lis_visit.patient_skey, patient.patient_id, lis_visit.visit_skey, lis_visit.visit_id,anonymous_name, anonymous_flag,
     DATE_FORMAT(lis_visit.date_created,'%%d/%%m/%%Y') as date_created,patient.date_created as dateCreated,
    CONCAT(COALESCE(patho_prefix.prefix_desc,''),' ',COALESCE(patient.firstname,''),' ',COALESCE(patient.middle_name,''),' ',COALESCE(patient.lastname,'')) AS fullName,
    COALESCE(patient.id_card,patient.passport_id) AS id,
    patient.hn,
    TRUNCATE((DATEDIFF(CURRENT_DATE, DATE_FORMAT(birthday,'%%Y-%%m-%%d'))/365),0) AS ageInYears,
    DATE_FORMAT(lis_visit.date_arrived,'%%Y-%%m-%%d') date_arrived_string,
    lis_visit.date_arrived, DATE_FORMAT(lis_visit.date_arrived,'%%d/%%m/%%Y') date_arrivedFormat,
    patient.allergy as allergic, patient.disease as congenital_disease, lis_visit.initial_symptoms,
     lis_visit.body_weight, lis_visit.body_height, lis_visit.body_temperature, lis_visit.systolic,
     lis_visit.diastolic, lis_visit.pulse, lis_visit.respiratory_rate, lis_visit.spo2, lis_visit.priority_cd, pp.priority_desc, lis_visit.note,
     to_base64(picture) as picture_base64,
     sex.sex_desc as sex,
     DATE_FORMAT(birthday,'%%Y-%%m-%%d') as birthday,
     patient.status patientStatus,
     (CASE lis_visit.status
     WHEN 'PE' THEN 'Pending'
     WHEN 'OP' THEN 'Open'
     WHEN 'CA' THEN 'Cancel'
     WHEN 'AV' THEN 'Arrived'
     WHEN 'PC' THEN 'Process'
     WHEN 'DC' THEN 'Discharge'
     WHEN 'MD' THEN 'Med Discharge'
     END) as statusDesc,
     lis_visit.facility_cd, lis_visit.status as statusOpd,patient.payment_plan_cd,
     patient.prefix, patho_prefix.prefix_desc, patient.firstname, patient.middle_name, patient.lastname, id_card, passport_id,lis_payment_plan.description as paymentPlanDesc,
     patient.race, patient.nationality,patient.email,
     address.street_1,address.street_2,address.street_3,address.street_4,address.city,
     address.state,r_state_province.name as provinceDesc,
     address.country_skey, r_country.description as countryDesc,
     address.zip_postal_code, patient.phone,
     patient_relation.patient_relation_skey,
     patient_relation.prefix as prefixRelation,  prefix_relation.prefix_desc as PrefixDescRelation,
     patient_relation.firstname as firstNameRelation, patient_relation.middle_name as middleNameRelation, patient_relation.lastname as LastNameRelation,
     patient_relation.sex as sexRelation , sex_relation.sex_desc as sexDescRelation,
     patient_relation.relation_cd, relation.description as relationDesc,
     addressRelation.street_1 as street1Relation,addressRelation.street_2 as street2Relation,
     addressRelation.city as cityRelation,addressRelation.state as stateRelation,
     addressRelation.country_skey as CountryRelation,addressRelation.zip_postal_code as zipCodeRelation,addressRelation.local_phone as localPhoneRelation,
     r_state_provinceRelation.name as provinceRelationDesc,r_countryRelation.description as countryRelationDesc,
     lis_visit.status as visitStatus
     from lis_visit
     inner join lis_patient patient on lis_visit.patient_skey = patient.patient_skey
     inner join patho_prefix on patho_prefix.prefix_cd = patient.prefix
     inner join patho_sex as sex on sex.sex_cd = patient.sex
     left join patho_priority pp on lis_visit.priority_cd = pp.priority_cd
     left join lis_payment_plan on patient.payment_plan_cd = lis_payment_plan.code
     left join lis_patient_address on lis_patient_address.patient_skey = patient.patient_skey
    left join address on lis_patient_address.address_skey = address.address_skey
    left join r_state_province on address.state = r_state_province.state_province_skey
    left join r_country on address.country_skey = r_country.country_skey
    left join lis_religion on patient.religion_cd = lis_religion.code
    left join lis_graduate on patient.graduate_cd = lis_graduate.code
    left join lis_blood_abo on patient.blood_abo_cd = lis_blood_abo.code
    left join lis_blood_rh on patient.blood_rh_cd = lis_blood_rh.code
    left join lis_occupation on patient.occupation_cd = lis_occupation.code
    left join lis_relationship_status on patient.relationship_cd = lis_relationship_status.code
    left join lis_patient_relation as patient_relation on patient.patient_skey = patient_relation.patient_skey
    left join patho_prefix prefix_relation on patient_relation.prefix = prefix_relation.prefix_cd
    left join patho_sex as sex_relation on patient_relation.sex = sex_relation.sex_cd
    left join relation on patient_relation.relation_cd = relation.code
    left join address addressRelation on patient_relation.address_skey = addressRelation.address_skey
    left join r_state_province as r_state_provinceRelation on addressRelation.state = r_state_provinceRelation.state_province_skey
    left join r_country as r_countryRelation on addressRelation.country_skey = r_countryRelation.country_skey
    where lis_visit.status = 'PE'
    and lis_visit.patient_skey like %(patientSkey)s
    and DATE_FORMAT(lis_visit.date_arrived,'%%Y-%%m-%%d') like  %(dateArrived)s
    """
    params = {'patientSkey': patientSkey, 'dateArrived': dateArrived}
    cursor.execute(sql,params)
    # cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()

    indexVisitSkey = columns.index('visit_skey')
    newData = []

    for row in data:
        listRow = list(row)

        sql = """\
        select episode.ep_id, DATE_FORMAT(episode.appointment_date,'%%d/%%m/%%Y') as appointment_date, clinic_master.clinic_name,
         DATE_FORMAT(appointment_date,'%%H:%%i') as appointment_time,
         CONCAT(COALESCE(employee.first_name,''),' ',COALESCE(employee.middle_name,''),' ',COALESCE(employee.last_name,'')) AS physician_name
         ,(CASE episode.status
         WHEN 'PE' THEN 'Pending'
         WHEN 'OP' THEN 'Open'
         WHEN 'CA' THEN 'Cancel'
         WHEN 'AV' THEN 'Arrived'
         WHEN 'PC' THEN 'Process'
         WHEN 'DC' THEN 'Discharge'
         WHEN 'DP' THEN 'Departed '
         END) as statusEpisodeDesc
        from episode
        inner join clinic_master on clinic_master.clinic_skey = episode.clinic_skey
        inner join patho_physician on episode.physician_no = patho_physician.physician_no
        inner join employee on patho_physician.employee_no = employee.employee_no
        where episode.visit_skey = %s
        """
        cursorLogicalWindow = conn.cursor()
        cursorLogicalWindow.execute(sql,row[indexVisitSkey])

        dataLogicalWindow = cursorLogicalWindow.fetchall()
        columnsLogicalWindow = [column[0] for column in cursorLogicalWindow.description]
        episode = toJson(dataLogicalWindow,columnsLogicalWindow)
        if 'episode' not in columns:
            columns.append('episode')
        listRow.append(episode)
        newData.append(listRow)
        cursorLogicalWindow.close()

    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(newData,columns))]
    return jsonify(toJsonOne(displayData,displayColumns))

@visit_mysql.route("/visit/getCountVisitMySQL", methods=['POST'])
def getCountVisit ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) as countVisit from lis_visit"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@visit_mysql.route("/visit/getStatVisitPhysicianMySQL", methods=['POST'])
def getStatVisitPhysician ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    # if not returnUserToken["isSuccess"]:
    #     return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()


    sql = """\
    select count(1) as value,
    employee.employee_no AS name
    from episode
    inner join patho_physician on episode.physician_no = patho_physician.physician_no
    inner join employee on patho_physician.employee_no = employee.employee_no
    group by employee.employee_no
    """
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@visit_mysql.route("/visit/getStatVisitPhysicianMonthMySQL", methods=['POST'])
def getStatVisitPhysicianMonth ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()

# select 'Jan' as month, 1127 as 'visit qty', 922 as qty
# union
# select 'Feb' as month, 475 as 'visit qty', 343 as qty
# union
# select 'Mar' as month, 319 as 'visit qty', 343 as qty
# union
# select 'Jun' as month, 974 as 'visit qty', 454 as qty
# union
# select 'Jul' as month, 231 as 'visit qty', 222 as qty
# union
# select 'Aug' as month, 280 as 'visit qty', 232 as qty


    sql = """\
    select e.physician_no
        ,count(1) as 'จำนวนคนไข้'
        ,IFNULL((select count(1)
        	from episode s
        	where status = 'DC'
        	group by s.physician_no
        	having s.physician_no = e.physician_no),0) as 'จำนวนคนไข้ที่รับบริการแล้ว'
        from episode e group by e.physician_no
    """
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))
