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

browse_mssql = Blueprint('browse_mssql', __name__)

@browse_mssql.route("/browse/retrieveLabOrderMSSQL", methods=['POST'])
def retrieveLabOrderMSSQL():
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
        select lis_lab_order.order_skey,lis_lab_order.order_id,lis_visit.visit_id,lis_patient.patient_id,
        patho_prefix.prefix_desc + ' ' + lis_patient.firstname + ' ' + lis_patient.lastname as patient_name
        from lis_lab_order inner join lis_visit on
        lis_lab_order.visit_skey =  lis_visit.visit_skey inner join lis_patient on
        lis_visit.patient_skey =  lis_patient.patient_skey  inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd
        where dateadd(dd,0,datediff(dd,0,lis_lab_order.date_created)) between '2019-01-01' and '2019-12-31'
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

@browse_mssql.route("/browse/retrieveVisitMSSQL", methods=['POST'])
def retrieveVisitMSSQL():
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
        select top 100 view_lis_visit_patient.visit_skey,view_lis_visit_patient.visit_id,view_lis_visit_patient.facility_cd,view_lis_visit_patient.date_arrived,
        view_lis_visit_patient.patient_skey,view_lis_visit_patient.patient_id,view_lis_visit_patient.firstname,view_lis_visit_patient.middle_name,
        view_lis_visit_patient.lastname,view_lis_visit_patient.birthday,view_lis_visit_patient.hn,view_lis_visit_patient.id_card,view_lis_visit_patient.passport_id,
        view_lis_visit_patient.logical_location_cd,view_lis_visit_patient.status,view_lis_visit_patient.prefix_cd,view_lis_visit_patient.prefix_desc,
        view_lis_visit_patient.sex_cd,view_lis_visit_patient.sex_desc,view_lis_visit_patient.patient_fullname,view_lis_visit_patient.date_arrived_year,
        view_lis_visit_patient.date_arrived_month,view_lis_visit_patient.date_arrived_day,facility.facility_name,
        CAST(N'' AS XML).value('xs:base64Binary(xs:hexBinary(sql:column("lis_patient.picture")))','VARCHAR(MAX)') as patient_picture_base64
        from view_lis_visit_patient inner join lis_patient on
        view_lis_visit_patient.patient_skey = lis_patient.patient_skey inner join facility on
        view_lis_visit_patient.facility_cd = facility.facility_cd
        """
        # where view_lis_visit_patient.visit_id like '%V13-00000%'
        cursor.execute(sql)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        conn.commit()
        cursor.close()

        # arr = []
        # arr.append(['' for x in columns])

        displayColumns = ['isSuccess','data']
        # displayData = [(isSuccess,toJson([['' for x in columns]],columns))]
        displayData = [(isSuccess,toJson(data,columns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@browse_mssql.route("/browse/retrieveCustomerMSSQL", methods=['POST'])
def retrieveCustomerMSSQL():
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
        select cust_skey,cust_no,name as cust_name from customer
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

@browse_mssql.route("/browse/retrieveFacilityMSSQL", methods=['POST'])
def retrieveFacilityMSSQL():
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
        select facility_cd,facility_name from facility
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

@browse_mssql.route("/browse/retrievePhysicianMSSQL", methods=['POST'])
def retrievePhysicianMSSQL():
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
        select physician_no,employee_no,first_name,last_name,first_name + ' ' + last_name as physician_name
        from view_patho_physician
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
