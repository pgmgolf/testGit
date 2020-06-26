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

import lis_lab_order_item_mysql

lab_order_mysql = Blueprint('lab_order_mysql', __name__)

@lab_order_mysql.route("/labOrder/retrieveLabOrderMySQL", methods=['POST'])
def retrieveLabOrderMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['order_id']
        paramCheckStringList = ['order_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderID = dataInput['order_id']

        conn = mysql.connect()
        cursor = conn.cursor()

        labOrderSql = """\
        select lis_lab_order.order_skey,lis_lab_order.order_id,lis_lab_order.status,lis_lab_order.priority_cd,lis_lab_order.admission_no,
        lis_lab_order.anonymous,lis_lab_order.collection_date,lis_lab_order.received_date,lis_lab_order.proj_cd,lis_lab_order.hospital_lab_no,
        lis_lab_order.customer_type_skey,lis_lab_order.iqc_job_no,lis_lab_order.iqc_lot_no,lis_lab_order.logical_location_cd,
        lis_lab_order.report_type_cd,lis_lab_order.ignore_type,lis_lab_order.patient_rights_cd,lis_visit.visit_id,lis_visit.facility_cd,facility.facility_name,
        view_visit_patient.birthday,view_visit_patient.patient_fullname,patho_sex.sex_desc,
        view_visit_patient.date_arrived_year,view_visit_patient.date_arrived_month,view_visit_patient.date_arrived_day,
        view_patho_physician_1.first_name + ' ' + view_patho_physician_1.last_name as patho_physician_name_1,
        view_patho_technician.first_name + ' ' + view_patho_technician.last_name as technician_name,
        lis_patient.patient_skey,lis_patient.patient_id,lis_patient.firstname,lis_patient.middle_name,lis_patient.lastname,patho_sex.sex_desc,patho_prefix.prefix_desc,
        lis_patient.hn,lis_patient.phone,lis_patient.birthday,lis_patient.id_card,lis_patient.passport_id,to_base64(lis_patient.picture) as patient_picture_base64,
        customer.cust_no,customer.name as cust_name,proj_header.proj_desc
        from lis_lab_order inner join lis_visit on
        lis_lab_order.visit_skey = lis_visit.visit_skey inner join facility on
        lis_visit.facility_cd = facility.facility_cd inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join view_visit_patient on
        lis_visit.visit_skey = view_visit_patient.visit_skey and
        lis_patient.patient_skey = view_visit_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join customer on
        lis_lab_order.cust_skey = customer.cust_skey left outer join view_patho_physician as view_patho_physician_1 on
        lis_lab_order.physician_no_1 = view_patho_physician_1.physician_no left outer join view_patho_technician on
        lis_lab_order.technician_no = view_patho_technician.technician_no left outer join proj_header on
        lis_lab_order.proj_cd = proj_header.proj_cd
        where lis_lab_order.order_id = %(order_id)s
        """

        labOrderItemSql = """\
        select lis_lab_order_item.order_skey,lis_lab_order_item.order_item_skey,lis_order_item.order_item_id,lis_order_item.order_item_desc,
        lis_lab_order_item.x,lis_lab_order_item.y,lis_lab_order_item.active,lis_lab_order_item.cancel,lis_lab_order_item.note,0 as edit_flag
        from lis_lab_order inner join lis_lab_order_item on
        lis_lab_order.order_skey = lis_lab_order_item.order_skey inner join lis_order_item on
        lis_lab_order_item.order_item_skey = lis_order_item.order_item_skey
        where lis_lab_order.order_skey = %(order_skey)s
        """

        labOrderTestItemSql = """\
        select lis_lab_order_test_item.order_skey,lis_lab_order_test_item.order_item_skey,lis_lab_order_test_item.test_item_skey,
        lis_test_item.test_item_id,lis_test_item.test_item_desc,lis_test_item.model_skey,lis_analyzer_model.analyzer_two_way,0 as edit_flag
        from lis_lab_order inner join lis_lab_order_item on
        lis_lab_order.order_skey = lis_lab_order_item.order_skey inner join lis_lab_order_test_item on
        lis_lab_order_item.order_skey = lis_lab_order_test_item.order_skey and
        lis_lab_order_item.order_item_skey = lis_lab_order_test_item.order_item_skey inner join lis_test_item on
        lis_lab_order_test_item.test_item_skey = lis_test_item.test_item_skey left outer join lis_analyzer_model on
        lis_test_item.model_skey = lis_analyzer_model.model_skey
        where lis_lab_order.order_skey = %(order_skey)s
        """

        labTestItemSql = """\
        select lis_lab_test_item.order_skey,lis_lab_test_item.test_item_skey,lis_lab_test_item.complete_flag,lis_lab_test_item.complete_date,
        lis_lab_test_item.vendor_skey,lis_lab_test_item.due_date,lis_lab_test_item.sent_date,lis_lab_test_item.job_doc_no,lis_lab_test_item.remark,
        lis_lab_test_item.status,lis_lab_test_item.sub_category_skey,lis_lab_test_item.due_date_outlab,lis_lab_test_item.required_all_result_item,
        lis_lab_test_item.sticker_cd,lis_lab_test_item.test_item_status,lis_lab_test_item.reject_flag,
        lis_test_item.test_item_id,lis_test_item.test_item_desc,vendor_master.name as vendor_name,
        lis_test_item.model_skey,lis_analyzer_model.analyzer_two_way,0 as edit_flag
        from lis_lab_order inner join lis_lab_test_item on
        lis_lab_order.order_skey = lis_lab_test_item.order_skey inner join lis_test_item on
        lis_lab_test_item.test_item_skey = lis_test_item.test_item_skey left outer join vendor_master on
        lis_lab_test_item.vendor_skey = vendor_master.vendor_skey left outer join lis_analyzer_model on
        lis_test_item.model_skey = lis_analyzer_model.model_skey
        where lis_lab_order.order_skey = %(order_skey)s
        """

        labResultItemSql = """\
        select lis_lab_test_result_item.order_skey,lis_lab_test_result_item.test_item_skey,lis_lab_test_result_item.result_item_skey,lis_lab_test_result_item.seq,lis_lab_test_result_item.remark,
        lis_lab_test_result_item.analyze,lis_lab_test_result_item.display_report,lis_lab_test_result_item.differential_flag,lis_lab_test_result_item.display_manual_result,lis_lab_test_result_item.require,
        lis_test_item.test_item_id,lis_test_item.test_item_desc,lis_result_item.result_item_id,lis_result_item.result_item_desc,0 as edit_flag
        from lis_lab_order inner join lis_lab_test_result_item On
        lis_lab_order.order_skey = lis_lab_test_result_item.order_skey inner join lis_test_item On
        lis_lab_test_result_item.test_item_skey = lis_test_item.test_item_skey inner join lis_result_item On
        lis_lab_test_result_item.result_item_skey = lis_result_item.result_item_skey
        where lis_lab_order.order_skey = %(order_skey)s
        """

        labOrderDict = {'paramsValue': {}, 'name': 'lab_orders', 'table': 'lab_order', 'key':'order_skey', 'sql':  labOrderSql, 'params':  {'order_id' : orderID}}
        labOrderItemDict = {'paramsValue': {}, 'name': 'lab_order_items', 'table': 'lis_order_lab_item', 'key':'order_skey,order_item_skey', 'sql':  labOrderItemSql, 'params':  {'order_skey' : 'order_skey'}}
        labOrderTestItemDict = {'paramsValue': {}, 'name': 'lab_order_test_items', 'table': 'lis_order_lab_test_item', 'key':'order_skey,order_item_skey,test_item_skey', 'sql':  labOrderTestItemSql, 'params':  {'order_skey' : 'order_skey'}}
        labTestItemDict = {'paramsValue': {}, 'name': 'lab_test_items', 'table': 'lis_lab_test_item', 'key':'order_skey,test_item_skey', 'sql':  labTestItemSql, 'params':  {'order_skey' : 'order_skey'}}
        labResultItemDict = {'paramsValue': {}, 'name': 'lab_result_items', 'table': 'lis_lab_order_test_item', 'key':'order_skey,order_line_skey', 'sql':  labResultItemSql, 'params':  {'order_skey' : 'order_skey'}}

        labOrderNode = Node(labOrderDict)
        labOrderItemNode = Node(labOrderItemDict)
        labOrderTestItemNode = Node(labOrderTestItemDict)
        labTestItemNode = Node(labTestItemDict)
        labResultItemNode = Node(labResultItemDict)

        labOrderNode.add_child(labOrderItemNode)
        labOrderNode.add_child(labOrderTestItemNode)
        labOrderNode.add_child(labTestItemNode)
        labOrderNode.add_child(labResultItemNode)

        datalabOrder, columnslabOrder = recur_tree(conn, 0, labOrderNode, labOrderNode)

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(datalabOrder,columnslabOrder))]
        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@lab_order_mysql.route("/labOrder/saveLabOrderMySQL", methods=['POST'])
def saveLabOrderMySQL():
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
        paramList = ['labOrder']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        conn = mysql.connect()
        conn.autocommit(False)

        labOrder = dataInput['labOrder']

        for lab_order_item in labOrder['labOrderData']['lab_order_items_delete']:
            lis_lab_order_item_mysql.deleteLabOrderItemMySQL(conn,lab_order_item)

        for lab_order_item in list(filter(lambda x: x['edit_flag'] == 1, labOrder['labOrderData']['lab_order_items'])):
            lis_lab_order_item_mysql.insertLabOrderItemMySQL(conn,lab_order_item)

        for lab_order_item in list(filter(lambda x: x['edit_flag'] == 2, labOrder['labOrderData']['lab_order_items'])):
            lis_lab_order_item_mysql.updateLabOrderItemMySQL(conn,lab_order_item)

        # for lab_order_item in labOrder['deleteData']['orderItem']:
        #     lis_lab_order_item_mysql.deleteLabOrderItemMySQL(conn,lab_order_item)

        conn.commit()

        print('commit')

        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'บันทึกวินิจฉัยเรียบร้อย','Success')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.OperationalError as e:
        print(str(e))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        conn.rollback()

        print('rollback')

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
