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

physician_mysql = Blueprint('physician_mysql', __name__)

@physician_mysql.route("/physician/retrievePhysicianMySQL", methods=['POST'])
def retrievePhysician ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    physicianNo = dataInput['physicianNo']
    userID = returnUserToken["data"]["user_id"]
    if not physicianNo:
        physicianNo = '%'


    conn = mysql.connect()
    cursor = conn.cursor()

    sql = """\
    select 1 from patho_physician
    inner join pc_user_def on patho_physician.employee_no = pc_user_def.employee_no
    where user_id = %(userID)s
    """
    params = {'userID': userID}
    cursor.execute(sql,params)

    row = cursor.fetchone()
    if row == None:
        physicianNo = '%'
        sql = """\
        select '' as physician_no, '' as employee_no, 'ไม่ระบุ' as physician_name,null as physician_picture_base64
        UNION ALL
        select patho_physician.physician_no, patho_physician.employee_no,
            CONCAT(COALESCE(employee.first_name,''),' ',COALESCE(employee.middle_name,''),' ',COALESCE(employee.last_name,'')) AS physician_name,
            to_base64(picture) as physician_picture_base64
        from patho_physician
        inner join employee on patho_physician.employee_no = employee.employee_no
        inner join pc_user_def on pc_user_def.employee_no = employee.employee_no
        where patho_physician.physician_no like %(physicianNo)s
        """
    else:
        physicianNo = userID
        sql = """\
        select patho_physician.physician_no, patho_physician.employee_no,
            CONCAT(COALESCE(employee.first_name,''),' ',COALESCE(employee.middle_name,''),' ',COALESCE(employee.last_name,'')) AS physician_name,
            to_base64(picture) as physician_picture_base64
        from patho_physician
        inner join employee on patho_physician.employee_no = employee.employee_no
        inner join pc_user_def on pc_user_def.employee_no = employee.employee_no
        where patho_physician.physician_no like %(physicianNo)s
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

@physician_mysql.route("/physician/retrievePhysicianPatientMySQL", methods=['POST'])
def retrievePhysicianPatient ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    physicianNo = dataInput['physicianNo']
    appointmentDate = dataInput['appointmentDate']

    if not physicianNo:
        physicianNo = '%'

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select CONCAT(COALESCE(patho_prefix.prefix_desc,''),' ',COALESCE(patient.firstname,''),' ',COALESCE(patient.middle_name,''),' ',COALESCE(patient.lastname,'')) AS patient_name,
    hn, appointment_date, episode.status, DATE_FORMAT(appointment_date,'%%H:%%i') as appointment_time,
    episode.ep_skey,episode.ep_id, lis_visit.visit_skey, lis_visit.visit_id,
    CONCAT(COALESCE(employee.first_name,''),' ',COALESCE(employee.middle_name,''),' ',COALESCE(employee.last_name,'')) AS physician_name, clinic_name,
     patient.patient_id, TRUNCATE((DATEDIFF(CURRENT_DATE, DATE_FORMAT(patient.birthday,'%%Y-%%m-%%d'))/365),0) AS age,patho_sex.sex_desc as sex,
     DATE_FORMAT(birthday,'%%Y-%%m-%%d') as birthday,
     lis_blood_abo.description as bloodAboDesc,
     lis_occupation.description as occupationDesc, patient.allergy, patient.disease,patient.nationality, patient.race,
     lis_visit.initial_symptoms, patho_priority.priority_desc,
     lis_visit.body_weight, lis_visit.body_height, lis_visit.body_temperature, lis_visit.systolic,
     lis_visit.diastolic, lis_visit.pulse, lis_visit.respiratory_rate, lis_visit.spo2
    from lis_visit
    inner join episode on lis_visit.visit_skey = episode.visit_skey
    inner join lis_patient patient on lis_visit.patient_skey = patient.patient_skey
    inner join patho_prefix on patho_prefix.prefix_cd = patient.prefix
    inner join patho_physician on episode.physician_no = patho_physician.physician_no
    inner join employee on patho_physician.employee_no = employee.employee_no
    inner join clinic_master on episode.clinic_skey = clinic_master.clinic_skey
    inner join patho_sex on patient.sex = patho_sex.sex_cd
    left join lis_occupation on patient.occupation_cd = lis_occupation.code
    left join lis_blood_abo on patient.blood_abo_cd = lis_blood_abo.code
    left join patho_priority on lis_visit.priority_cd = patho_priority.priority_cd
    where episode.physician_no like %(physicianNo)s and DATE_FORMAT(appointment_date,'%%Y-%%m-%%d') = %(appointmentDate)s
    and episode.status <> 'PE'
    order by appointment_date,episode.ep_skey
    """

    params = {'physicianNo': physicianNo, 'appointmentDate': appointmentDate}
    cursor.execute(sql,params)
    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]
    return jsonify(toJsonOne(displayData,displayColumns))
