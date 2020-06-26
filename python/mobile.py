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

mobile = Blueprint('mobile', __name__)

@mobile.route("/mobile/GetUserInfo", methods=['POST'])
def GetUserInfo():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['User','Password']
        paramCheckStringList = ['User','Password']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        UserID = dataInput['User']
        password = dataInput['Password']

        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """\
        select pc_user_def.user_skey,pc_user_def.user_id,pc_user_def.first_name,pc_user_def.middle_name,pc_user_def.last_name,pc_user_def.ssn,pc_user_def.employee_no,
        pc_user_def.profile_skey,pc_user_def.active_flag,pc_user_def.mfg_requisitioner,pc_user_def.facility_cd,pc_user_def.fin_default_co,pc_user_def.user_password,
        pc_user_def.cust_skey,pc_user_def.email,pc_user_def.patient_skey,customer.name as cust_name,
        to_base64(picture) as user_pic_base64,%(ip_address)s as ip_address
        from pc_user_def left outer join customer on
        pc_user_def.cust_skey = customer.cust_skey
        where pc_user_def.user_id = %(user_id)s
        """

        params = {'user_id': UserID,'ip_address': request.remote_addr}
        cursor.execute(sql,params)
        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = toJson(data,columns)

        if len(data) == 0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Not Found User " + UserID

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        userPassword = Decrypt(result[0]["user_password"])

        if password != userPassword:
            isSuccess = False
            reasonCode = 500
            reasonText = "Password wrong for User " + UserID

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(data,columns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@mobile.route("/mobile/GetCustomer", methods=['POST'])
def GetCustomer():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        # dataInput = request.json
        # paramList = []
        # paramCheckStringList = []
        #
        # msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        # if msgError != None:
        #     return jsonify(msgError);

        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """\
        select cust_no,name as cust_name from customer
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

@mobile.route("/mobile/GetClinic", methods=['POST'])
def GetClinic():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """\
        select clinic_skey,clinic_id,clinic_name,clinic_desc from clinic_master
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

@mobile.route("/mobile/findVisitEpisode", methods=['POST'])
def findVisitEpisode():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['date_arrived_from','date_arrived_to','clinic_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        dateArrivedFrom = dataInput['date_arrived_from']
        dateArrivedTo = dataInput['date_arrived_to']
        clinicSkey = dataInput['clinic_skey']

        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """\
        select lis_visit.visit_skey,lis_visit.visit_id,lis_visit.date_arrived,episode.ep_skey,episode.ep_id,episode.physician_no,employee.first_name,employee.middle_name,employee.last_name,
        view_visit_patient.birthday,view_visit_patient.patient_fullname,patho_sex.sex_desc,
        concat(employee.first_name,' ',employee.last_name) as physician_name,
        view_visit_patient.date_arrived_year,view_visit_patient.date_arrived_month,view_visit_patient.date_arrived_day,
        clinic_master.clinic_skey,clinic_master.clinic_id,clinic_master.clinic_name,clinic_master.clinic_desc,
        clinic_master.icon
        from lis_visit inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join view_visit_patient on
        lis_visit.visit_skey = view_visit_patient.visit_skey and
        lis_patient.patient_skey = view_visit_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join patho_physician on
        episode.physician_no = patho_physician.physician_no left outer join employee on
        patho_physician.employee_no = employee.employee_no inner join clinic_master on
        episode.clinic_skey = clinic_master.clinic_skey
        where date(lis_visit.date_arrived) >= %(date_arrived_from)s and
        date(lis_visit.date_arrived) <= %(date_arrived_to)s and
        episode.clinic_skey = %(clinic_skey)s
        """
        print(dateArrivedFrom)
        print(dateArrivedTo)
        print(clinicSkey)
        params = {'date_arrived_from': dateArrivedFrom, 'date_arrived_to': dateArrivedTo, 'clinic_skey': clinicSkey}
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

@mobile.route("/mobile/retrieveVisitEpisode", methods=['POST'])
def retrieveVisitEpisode():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['ep_id']
        paramCheckStringList = ['ep_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        episodeID = dataInput['ep_id']

        conn = mysql.connect()
        cursor = conn.cursor()

        episodeSql = """\
        select lis_visit.visit_skey,lis_visit.visit_id,lis_visit.date_arrived,episode.ep_skey,episode.ep_id,episode.physician_no,employee.first_name,employee.middle_name,employee.last_name,
        view_visit_patient.birthday,view_visit_patient.patient_fullname,patho_sex.sex_desc,
        to_base64(lis_patient.picture) as patient_picture_base64,
        concat(employee.first_name,' ',employee.last_name) as physician_name,
        date_arrived_year,date_arrived_month,date_arrived_day,
        to_base64(employee.emp_img) as physician_picture_base64,
        clinic_master.clinic_skey,clinic_master.clinic_id,clinic_master.clinic_name,clinic_master.clinic_desc,
        clinic_master.icon
        from lis_visit inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join view_visit_patient on
        lis_visit.visit_skey = view_visit_patient.visit_skey and
        lis_patient.patient_skey = view_visit_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join patho_physician on
        episode.physician_no = patho_physician.physician_no left outer join employee on
        patho_physician.employee_no = employee.employee_no inner join clinic_master on
        episode.clinic_skey = clinic_master.clinic_skey
        where episode.ep_id = %(ep_id)s
        """

        attachmentSql = """\
        select lis_visit.visit_skey,episode.ep_skey,ep_attachment.ep_att_skey,
        to_base64(ep_attachment.att_data) as ep_attachment_base64,ep_attachment.att_filename,
        ep_attachment.att_type,ep_attachment.remark,false as select_flag
        from lis_visit inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join patho_physician on
        episode.physician_no = patho_physician.physician_no left outer join employee on
        patho_physician.employee_no = employee.employee_no inner join clinic_master on
        episode.clinic_skey = clinic_master.clinic_skey inner join ep_attachment on
        episode.ep_skey = ep_attachment.ep_skey
        where episode.ep_skey = %(ep_skey)s
        """

        episodeDict = {'paramsValue': {}, 'name': 'episodes', 'table': 'episode', 'key':'ep_skey', 'sql':  episodeSql, 'params':  {'visit_skey': -1,'ep_id' : episodeID}}
        attachmentDict = {'paramsValue': {}, 'name': 'attachments', 'table': 'ep_attachment', 'key':'ep_att_skey', 'sql':  attachmentSql, 'params':  {'ep_skey' : -1}}

        episodeNode = Node(episodeDict)
        attachmentNode = Node(attachmentDict)

        episodeNode.add_child(attachmentNode)

        dataVisit, columnsVisit = recur_tree(conn, 0, episodeNode, episodeNode)

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(dataVisit,columnsVisit))]

        return jsonify(toJsonOne(displayData,displayColumns))

        # params = {'ep_id': epID}
        # cursor.execute(sql,params)
        # data = cursor.fetchall()
        # columns = [column[0] for column in cursor.description]
        # result = toJson(data,columns)

        # if len(data) == 0:
        #     isSuccess = False
        #     reasonCode = 500
        #     reasonText = "Not Found Ep ID. " + epID
        #
        #     errColumns = ['isSuccess','reasonCode','reasonText']
        #     errData = [(isSuccess,reasonCode,reasonText)]
        #
        #     return jsonify(toJsonOne(errData,errColumns))
        #
        # displayColumns = ['isSuccess','data']
        # displayData = [(isSuccess,toJson(data,columns))]
        #
        # return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@mobile.route("/mobile/insertOrUpdateEpisodeAttachmentMySQL", methods=['POST'])
def insertOrUpdateEpisodeAttachmentMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        # returnUserToken = getUserToken(request.headers.get('Authorization'))
        # if not returnUserToken["isSuccess"]:
        #     return jsonify(returnUserToken);

        # userID = returnUserToken["data"]["user_id"]

        userID = "root"

        dataInput = request.json
        paramList = ['att_base64','att_filename','att_type','remark']
        paramCheckStringList = ['att_base64','att_filename','att_type']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        visitSkey = dataInput['visit_skey']
        episodeSkey = dataInput['ep_skey']
        episodeAttachSkey = dataInput['ep_att_skey']
        attachBase64 = dataInput['att_base64']
        attachFileName = dataInput['att_filename']
        attachType = dataInput['att_type']
        remark = dataInput['remark']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from lis_visit inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join ep_attachment on
        episode.ep_skey = ep_attachment.ep_skey
        where lis_visit.visit_skey = %(visit_skey)s and
        episode.ep_skey like %(ep_skey)s and
        ep_attachment.ep_att_skey like %(ep_att_skey)s
        """
        params = {'visit_skey': visitSkey,'ep_skey' : episodeSkey,'ep_att_skey' :episodeAttachSkey}
        cursor.execute(sql,params)

        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            episodeAttachSkey = getNextSequenceMySQL('ep_attachment','ep_attachment','ep_att_skey')
            sql = """\
            insert into ep_attachment
            (ep_att_skey,ep_skey,att_data,att_filename,att_type,remark,date_created,user_created,date_changed,user_changed)
            values(%(ep_att_skey)s,%(ep_skey)s,FROM_BASE64(%(att_data)s),%(att_filename)s,%(att_type)s,%(remark)s,now(),%(user_created)s,now(),%(user_changed)s)
            """
            params = {'ep_att_skey': episodeAttachSkey,'ep_skey': episodeSkey,'att_data': attachBase64,'att_filename': attachFileName
            ,'att_type': attachType,'remark': remark,'user_created': userID,'user_changed': userID}
            cursor.execute(sql,params)
            conn.commit()
        else:
            sql = """\
            update ep_attachment
            set att_data = FROM_BASE64(%(att_data)s),
            att_filename = %(att_filename)s,
            att_type = %(att_type)s,
            remark = %(remark)s,
            user_changed = now(),
            user_changed = %(user_changed)s
            where ep_attachment.ep_skey like %(ep_skey)s and
            ep_attachment.ep_att_skey like %(ep_att_skey)s
            """
            params = {'ep_att_skey': episodeAttachSkey,'ep_skey': episodeSkey,'att_data': attachBase64,'att_filename': attachFileName
            ,'att_type': attachType,'remark': remark,'user_created': userID,'user_changed': userID}
            cursor.execute(sql,params)
            conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'บันทึกวินิจฉัยเรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@mobile.route("/mobile/deleteEpisodeAttachmentMySQL", methods=['POST'])
def deleteEpisodeAttachmentMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        # returnUserToken = getUserToken(request.headers.get('Authorization'))
        # if not returnUserToken["isSuccess"]:
        #     return jsonify(returnUserToken);

        # userID = returnUserToken["data"]["user_id"]

        userID = "root"

        dataInput = request.json
        paramList = ['visit_skey','ep_skey','ep_att_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        visitSkey = dataInput['visit_skey']
        episodeSkey = dataInput['ep_skey']
        episodeAttachSkey = dataInput['ep_att_skey']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from lis_visit inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join ep_attachment on
        episode.ep_skey = ep_attachment.ep_skey
        where lis_visit.visit_skey = %(visit_skey)s and
        episode.ep_skey like %(ep_skey)s and
        ep_attachment.ep_att_skey like %(ep_att_skey)s
        """
        params = {'visit_skey': visitSkey,'ep_skey' : episodeSkey,'ep_att_skey' :episodeAttachSkey}
        cursor.execute(sql,params)

        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Not Found EP skey " + str(episodeSkey) + " EP Attachment Skey " + str(episodeAttachSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))
        else:
            sql = """\
            delete from ep_attachment
            where ep_attachment.ep_skey like %(ep_skey)s and
            ep_attachment.ep_att_skey like %(ep_att_skey)s
            """
            params = {'ep_att_skey': episodeAttachSkey,'ep_skey': episodeSkey}
            cursor.execute(sql,params)
            conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'บันทึกวินิจฉัยเรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
