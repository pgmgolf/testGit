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

visit_episode_mysql = Blueprint('visit_episode_mysql', __name__)

@visit_episode_mysql.route("/visitEpisode/retrieveVisitEpisodeMySQL", methods=['POST'])
def retrieveVisitEpisodeMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        # returnUserToken = getUserToken(request.headers.get('Authorization'))
        # if not returnUserToken["isSuccess"]:
        #     return jsonify(returnUserToken);
        #
        # userID = returnUserToken["data"]["user_id"]

        dataInput = request.json
        paramList = ['visit_id','ep_id']
        paramCheckStringList = ['visit_id','ep_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        visitID = dataInput['visit_id']
        episodeID = dataInput['ep_id']

        conn = mysql.connect()
        cursor = conn.cursor()

        visitSql = """\
        select lis_visit.visit_skey,lis_visit.visit_id,lis_patient.patient_skey,lis_patient.patient_id,
        lis_patient.firstname,lis_patient.middle_name,lis_patient.lastname,patho_sex.sex_desc,patho_prefix.prefix_desc,
        lis_patient.hn,lis_patient.phone,lis_patient.birthday,lis_patient.id_card,lis_patient.passport_id,
        to_base64(lis_patient.picture) as patient_picture_base64
        from lis_visit inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd
        where lis_visit.visit_id = %(visit_id)s
        """

        episodeSql = """\
        select lis_visit.visit_skey,episode.ep_skey,episode.ep_id,episode.physician_no,employee.first_name,employee.middle_name,employee.last_name,
        concat(employee.first_name,' ',employee.last_name) as physician_name,
        to_base64(employee.emp_img) as physician_picture_base64,
        clinic_master.clinic_skey,clinic_master.clinic_id,clinic_master.clinic_name,clinic_master.clinic_desc,
        clinic_master.icon
        from lis_visit inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join patho_physician on
        episode.physician_no = patho_physician.physician_no left outer join employee on
        patho_physician.employee_no = employee.employee_no inner join clinic_master on
        episode.clinic_skey = clinic_master.clinic_skey
        where lis_visit.visit_skey = %(visit_skey)s and
        episode.ep_id like %(ep_id)s
        """

        labOrderSql = """\
        select lis_visit.visit_skey,episode.ep_skey,lis_lab_order.order_skey,lis_lab_order.order_id
        from lis_visit inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join patho_physician on
        episode.physician_no = patho_physician.physician_no left outer join employee on
        patho_physician.employee_no = employee.employee_no inner join clinic_master on
        episode.clinic_skey = clinic_master.clinic_skey inner join lis_lab_order on
        episode.ep_skey = lis_lab_order.ep_skey
        where episode.ep_skey = %(ep_skey)s
        """

        diagnoseSql = """\
        select lis_visit.visit_skey,episode.ep_skey,ep_diagnose.ep_dx_skey,ep_diagnose.resource_no,ep_diagnose.resource_desc,ep_diagnose.uom_selling,ep_diagnose.uom_factor,
        ep_diagnose.price,ep_diagnose.qty,ep_diagnose.vat_rate,ep_diagnose.include_tax
        from lis_visit inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join patho_physician on
        episode.physician_no = patho_physician.physician_no left outer join employee on
        patho_physician.employee_no = employee.employee_no inner join clinic_master on
        episode.clinic_skey = clinic_master.clinic_skey inner join ep_diagnose on
        episode.ep_skey = ep_diagnose.ep_skey
        where episode.ep_skey = %(ep_skey)s
        """

        procedureSql = """\
        select lis_visit.visit_skey,episode.ep_skey,ep_procedure.ep_proc_skey,ep_procedure.resource_no,ep_procedure.resource_desc,ep_procedure.uom_selling,ep_procedure.uom_factor,
        ep_procedure.price,ep_procedure.qty,ep_procedure.vat_rate,ep_procedure.include_tax
        from lis_visit inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join patho_physician on
        episode.physician_no = patho_physician.physician_no left outer join employee on
        patho_physician.employee_no = employee.employee_no inner join clinic_master on
        episode.clinic_skey = clinic_master.clinic_skey inner join ep_procedure on
        episode.ep_skey = ep_procedure.ep_skey
        where episode.ep_skey = %(ep_skey)s
        """

        prescriptionSql = """\
        select lis_visit.visit_skey,episode.ep_skey,ep_prescription.ep_rx_skey,ep_prescription.resource_no,ep_prescription.resource_desc,ep_prescription.uom_selling,ep_prescription.uom_factor,
        ep_prescription.price,ep_prescription.qty,ep_prescription.vat_rate,ep_prescription.include_tax
        from lis_visit inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join patho_physician on
        episode.physician_no = patho_physician.physician_no left outer join employee on
        patho_physician.employee_no = employee.employee_no inner join clinic_master on
        episode.clinic_skey = clinic_master.clinic_skey inner join ep_prescription on
        episode.ep_skey = ep_prescription.ep_skey
        where episode.ep_skey = %(ep_skey)s
        """

        attachmentSql = """\
        select lis_visit.visit_skey,episode.ep_skey,ep_attachment.ep_att_skey,
        to_base64(ep_attachment.att_data) as ep_attachment_base64,ep_attachment.att_filename,
        ep_attachment.att_type,ep_attachment.remark,0 as edit_flag
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

        labTestItemSql = """\
        select lis_lab_test_item.*,lis_test_item.test_item_id,lis_test_item.test_item_desc,vendor_master.name as vendor_name,
        lis_test_item.model_skey,lis_analyzer_model.analyzer_two_way
        from lis_lab_order inner join lis_lab_test_item on
        lis_lab_order.order_skey = lis_lab_test_item.order_skey inner join lis_test_item on
        lis_lab_test_item.test_item_skey = lis_test_item.test_item_skey left outer join vendor_master on
        lis_lab_test_item.vendor_skey = vendor_master.vendor_skey left outer join lis_analyzer_model on
        lis_test_item.model_skey = lis_analyzer_model.model_skey
        where lis_lab_order.order_skey = %(order_skey)s
        """

        labResultItemSql = """\
        select lis_result_item.result_item_id,lis_result_item.result_item_desc
        from lis_lab_order inner join lis_lab_result_item On
        lis_lab_order.order_skey = lis_lab_result_item.order_skey inner join lis_result_item On
        lis_lab_result_item.result_item_skey = lis_result_item.result_item_skey
        where lis_lab_order.order_skey = %(order_skey)s
        """

        visitDict = {'paramsValue': {}, 'name': 'visits', 'table': 'lis_visit', 'key':'visit_skey', 'sql': visitSql, 'params': {'visit_id': visitID}}
        episodeDict = {'paramsValue': {}, 'name': 'episodes', 'table': 'episode', 'key':'ep_skey', 'sql':  episodeSql, 'params':  {'visit_skey': 'visit_skey','ep_id' : episodeID}}
        labOrderDict = {'paramsValue': {}, 'name': 'lab_orders', 'table': 'lab_order', 'key':'order_skey', 'sql':  labOrderSql, 'params':  {'ep_skey' : 'ep_skey'}}
        diagnoseDict = {'paramsValue': {}, 'name': 'diagnoses', 'table': 'ep_diagnose', 'key':'ep_dx_skey', 'sql':  diagnoseSql, 'params':  {'ep_skey' : 'ep_skey'}}
        procedureDict = {'paramsValue': {}, 'name': 'procedures', 'table': 'ep_procedure', 'key':'ep_proc_skey', 'sql':  procedureSql, 'params':  {'ep_skey' : 'ep_skey'}}
        prescriptionDict = {'paramsValue': {}, 'name': 'prescriptions', 'table': 'ep_prescription', 'key':'ep_rx_skey', 'sql':  prescriptionSql, 'params':  {'ep_skey' : 'ep_skey'}}
        attachmentDict = {'paramsValue': {}, 'name': 'attachments', 'table': 'ep_attachment', 'key':'ep_att_skey', 'sql':  attachmentSql, 'params':  {'ep_skey' : 'ep_skey'}}
        labTestItemDict = {'paramsValue': {}, 'name': 'lab_test_items', 'table': 'lis_lab_test_item', 'key':'order_skey,test_item_skey', 'sql':  labTestItemSql, 'params':  {'order_skey' : 'order_skey'}}
        labResultItemDict = {'paramsValue': {}, 'name': 'lab_result_items', 'table': 'lis_lab_order_test_item', 'key':'order_skey,order_line_skey', 'sql':  labResultItemSql, 'params':  {'order_skey' : 'order_skey'}}

        visitNode = Node(visitDict)
        episodeNode = Node(episodeDict)
        labOrderNode = Node(labOrderDict)
        diagnoseNode = Node(diagnoseDict)
        procedureNode = Node(procedureDict)
        prescriptionNode = Node(prescriptionDict)
        attachmentNode = Node(attachmentDict)
        labTestItemNode = Node(labTestItemDict)
        labResultItemNode = Node(labResultItemDict)

        visitNode.add_child(episodeNode)
        episodeNode.add_child(labOrderNode)
        episodeNode.add_child(diagnoseNode)
        episodeNode.add_child(procedureNode)
        episodeNode.add_child(prescriptionNode)
        episodeNode.add_child(attachmentNode)

        labOrderNode.add_child(labTestItemNode)
        labOrderNode.add_child(labResultItemNode)

        dataVisit, columnsVisit = recur_tree(conn, 0, visitNode, visitNode)

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(dataVisit,columnsVisit))]
        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
