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
from dateutil.parser import parse
import re
import random
import io
import base64
import jwt
import time

from db_config import *
from common import *

import lis_lab_order_item_mssql
import lis_lab_test_item_mssql

lab_order_mssql = Blueprint('lab_order_mssql', __name__)

@lab_order_mssql.route("/labOrder/retrieveLabOrderMSSQL", methods=['POST'])
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

        dataInput = request.json
        paramList = []
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderID = dataInput.get("order_id", "")

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        labOrderSql = """\
        select lis_lab_order.order_skey,lis_lab_order.order_id,lis_lab_order.visit_skey,lis_lab_order.status,lis_lab_order.priority_cd,lis_lab_order.admission_no,
        FORMAT(lis_lab_order.collection_date, 'yyyy-MM-dd HH:mm:ss') as collection_date,
        FORMAT(lis_lab_order.received_date, 'yyyy-MM-dd HH:mm:ss') as received_date,
        lis_lab_order.cust_skey,customer.cust_no,customer.name as cust_name,lis_lab_order.proj_cd,proj_header.proj_desc,lis_lab_order.physician_no_1,
        lis_lab_order.anonymous,lis_lab_order.hospital_lab_no,lis_lab_order.customer_type_skey,lis_lab_order.iqc_job_no,lis_lab_order.iqc_lot_no,
        lis_lab_order.logical_location_cd,lis_lab_order.report_type_cd,lis_lab_order.ignore_type,lis_lab_order.patient_rights_cd,lis_visit.visit_id,
        lis_visit.facility_cd,facility.facility_name,view_lis_visit_patient.birthday,view_lis_visit_patient.patient_fullname,patho_sex.sex_desc,
        view_lis_visit_patient.date_arrived_year,view_lis_visit_patient.date_arrived_month,view_lis_visit_patient.date_arrived_day,
        view_patho_physician_1.first_name + ' ' + view_patho_physician_1.last_name as patho_physician_name_1,
        view_patho_technician.first_name + ' ' + view_patho_technician.last_name as technician_name,
        lis_patient.patient_skey,lis_patient.patient_id,lis_patient.firstname,lis_patient.middle_name,lis_patient.lastname,patho_sex.sex_desc,patho_prefix.prefix_desc,
        lis_patient.hn,lis_patient.phone,lis_patient.birthday,lis_patient.id_card,lis_patient.passport_id,
        CAST(N'' AS XML).value('xs:base64Binary(xs:hexBinary(sql:column("picture")))','VARCHAR(MAX)') as patient_picture_base64
        from lis_lab_order inner join lis_visit on
        lis_lab_order.visit_skey = lis_visit.visit_skey inner join facility on
        lis_visit.facility_cd = facility.facility_cd inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join view_lis_visit_patient on
        lis_visit.visit_skey = view_lis_visit_patient.visit_skey and
        lis_patient.patient_skey = view_lis_visit_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join customer on
        lis_lab_order.cust_skey = customer.cust_skey left outer join view_patho_physician as view_patho_physician_1 on
        lis_lab_order.physician_no_1 = view_patho_physician_1.physician_no left outer join view_patho_technician on
        lis_lab_order.technician_no = view_patho_technician.technician_no left outer join proj_header on
        lis_lab_order.proj_cd = proj_header.proj_cd
        where lis_lab_order.order_id = %(order_id)s
        """

        labRoutingSql = """\
        select lis_lab_routing.order_skey,lis_lab_routing.routing_seq,lis_lab_routing.active,
        lis_routing.routing_desc,lis_routing.logical_location_code,lis_logical_location.description as logical_location_desc
        from lis_lab_order inner join lis_lab_routing on
        lis_lab_order.order_skey = lis_lab_routing.order_skey inner join lis_routing on
        lis_lab_routing.routing_seq = lis_routing.routing_seq inner join lis_logical_location on
        lis_routing.logical_location_code = lis_logical_location.code
        where lis_lab_order.order_skey = %(order_skey)s
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
        lis_lab_test_item.vendor_skey,FORMAT(lis_lab_test_item.due_date, 'yyyy-MM-dd HH:mm:ss fff') as due_date,lis_lab_test_item.sent_date,lis_lab_test_item.job_doc_no,lis_lab_test_item.remark,
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

        labPricingSql = """\
        select lis_lab_pricing.order_skey,lis_lab_pricing.line_no,lis_lab_pricing.resource_no,lis_lab_pricing.price,lis_lab_pricing.qty,
        lis_lab_pricing.disc_pct,lis_lab_pricing.disc_amount,resource.description as resource_desc,uom.uom_desc
        from lis_lab_order inner join lis_lab_pricing on
        lis_lab_order.order_skey = lis_lab_pricing.order_skey inner join resource on
        lis_lab_pricing.resource_no = resource.resource_no inner join uom on
        resource.uom = uom.uom
        where lis_lab_order.order_skey = %(order_skey)s
        """

        labSpecimenTypeSql = """\
        select newid() as uid,lis_lab_specimen_type.order_skey,lis_lab_specimen_type.specimen_type_id,lis_lab_specimen_type.specimen_type_cd,
        lis_specimen_type.specimen_type_desc,lis_specimen_type.container_type
        from lis_lab_order inner join lis_lab_specimen_type on
        lis_lab_order.order_skey = lis_lab_specimen_type.order_skey inner join lis_specimen_type on
        lis_lab_specimen_type.specimen_type_cd = lis_specimen_type.specimen_type_cd
        where lis_lab_order.order_skey = %(order_skey)s
        """

        labSpecimenTypeTestItemSql = """\
        select newid() as uid,lis_lab_specimen_type_test_item.order_skey,lis_lab_specimen_type_test_item.specimen_type_id,lis_lab_specimen_type_test_item.test_item_skey,
        lis_lab_specimen_type_test_item.date_scanned,lis_lab_specimen_type_test_item.model_skey,lis_lab_specimen_type_test_item.analyzer_two_way,
        lis_test_item.test_item_id,lis_test_item.test_item_desc,lis_specimen_type.specimen_type_desc
        from lis_lab_order inner join lis_lab_specimen_type on
        lis_lab_order.order_skey = lis_lab_specimen_type.order_skey inner join lis_lab_specimen_type_test_item on
        lis_lab_specimen_type.order_skey = lis_lab_specimen_type_test_item.order_skey and
        lis_lab_specimen_type.specimen_type_id = lis_lab_specimen_type_test_item.specimen_type_id inner join lis_test_item on
        lis_lab_specimen_type_test_item.test_item_skey = lis_test_item.test_item_skey inner join lis_specimen_type on
        lis_lab_specimen_type.specimen_type_cd = lis_specimen_type.specimen_type_cd
        where lis_lab_order.order_skey = %(order_skey)s and
        lis_lab_specimen_type.specimen_type_id = %(specimen_type_id)s
        """

        labOrderDict = {'hasRow': True, 'paramsValue': {}, 'name': 'lab_orders', 'table': 'lis_lab_order', 'key':'order_skey', 'sql':  labOrderSql, 'params':  {'order_id' : orderID}}
        labRoutingDict = {'paramsValue': {}, 'name': 'lab_routings', 'table': 'lis_lab_routing', 'key':'order_skey,routing_seq', 'sql':  labRoutingSql, 'params':  {'order_skey' : 'order_skey'}}
        labOrderItemDict = {'paramsValue': {}, 'name': 'lab_order_items', 'table': 'lis_order_lab_item', 'key':'order_skey,order_item_skey', 'sql':  labOrderItemSql, 'params':  {'order_skey' : 'order_skey'}}
        labOrderTestItemDict = {'paramsValue': {}, 'name': 'lab_order_test_items', 'table': 'lis_order_lab_test_item', 'key':'order_skey,order_item_skey,test_item_skey', 'sql':  labOrderTestItemSql, 'params':  {'order_skey' : 'order_skey'}}
        labTestItemDict = {'paramsValue': {}, 'name': 'lab_test_items', 'table': 'lis_lab_test_item', 'key':'order_skey,test_item_skey', 'sql':  labTestItemSql, 'params':  {'order_skey' : 'order_skey'}}
        labResultItemDict = {'paramsValue': {}, 'name': 'lab_result_items', 'table': 'lis_lab_order_test_item', 'key':'order_skey,order_line_skey', 'sql':  labResultItemSql, 'params':  {'order_skey' : 'order_skey'}}
        labPricingDict = {'paramsValue': {}, 'name': 'lis_lab_pricings', 'table': 'lis_lab_pricing', 'key':'order_skey,line_no', 'sql':  labPricingSql, 'params':  {'order_skey' : 'order_skey'}}
        labSpecimenTypeDict = {'paramsValue': {}, 'name': 'lis_lab_specimen_types', 'table': 'lis_lab_specimen_type', 'key':'order_skey,specimen_type_id', 'sql':  labSpecimenTypeSql, 'params':  {'order_skey' : 'order_skey'}}
        labSpecimenTypeTestItemDict = {'paramsValue': {}, 'name': 'lis_lab_specimen_type_test_items', 'table': 'lis_lab_specimen_type_test_item', 'key':'order_skey,specimen_type_id,test_item_skey', 'sql':  labSpecimenTypeTestItemSql, 'params':  {'order_skey' : 'order_skey', 'specimen_type_id' : 'specimen_type_id'}}

        labOrderNode = Node(labOrderDict)
        labRoutingNode = Node(labRoutingDict)
        labOrderItemNode = Node(labOrderItemDict)
        labOrderTestItemNode = Node(labOrderTestItemDict)
        labTestItemNode = Node(labTestItemDict)
        labResultItemNode = Node(labResultItemDict)
        labPricingNode = Node(labPricingDict)
        labSpecimenTypeNode = Node(labSpecimenTypeDict)
        labSpecimenTypeTestItemNode = Node(labSpecimenTypeTestItemDict)

        labOrderNode.add_child(labRoutingNode)
        labOrderNode.add_child(labOrderItemNode)
        labOrderNode.add_child(labOrderTestItemNode)
        labOrderNode.add_child(labTestItemNode)
        labOrderNode.add_child(labResultItemNode)
        labOrderNode.add_child(labPricingNode)
        labOrderNode.add_child(labSpecimenTypeNode)
        labSpecimenTypeNode.add_child(labSpecimenTypeTestItemNode)

        datalabOrder, columnslabOrder = recur_tree(conn, 0, labOrderNode, labOrderNode)

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(datalabOrder,columnslabOrder))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.StandardError as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,pymssqlCustomExceptionMessage(e))]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@lab_order_mssql.route("/labOrder/retrieveDropDownMSSQL", methods=['POST'])
def retrieveDropDown():
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

        dropdownSql = """\
        select 1 as code
        """
        patientRightsSql = """\
        select convert(nvarchar,null) as code,convert(nvarchar,'') as description
        union
        select code,description from lis_patient_rights
        """
        reportTypeSql = """\
        select code,description from lis_report_type
        """
        customerTypeSql = """\
        select customer_type_skey,customer_type,description from r_customer_type
        """
        labStatusSql = """\
        select code,description,color from lis_r_lab_status
        """
        testItemStatusSql = """\
        select code,description from lis_r_test_item_status
        """
        pathoPrioritySql = """\
        select priority_cd,priority_desc,hooper,color from patho_priority
        """
        logicalLocationSql = """\
        select code,description,patient_type_code from lis_logical_location
        """
        subCategorySql = """\
        select sub_category_skey,category_skey,sub_category_id,sub_category_desc,remark from lis_sub_category
        """
        specimenStickerSql = """\
        select sticker_cd,sticker_desc,print_qty from lis_specimen_sticker
        """
        analyzerModelSql = """\
        select model_skey,model_cd,model_desc from lis_analyzer_model
        """

        dropdownDict = {'paramsValue': {}, 'name': 'dropdown', 'table': 'dropdown', 'key':'code', 'sql':  dropdownSql, 'params': {}}
        patientRightsDict = {'paramsValue': {}, 'name': 'lis_patient_rights', 'table': 'lis_patient_rights', 'key':'code', 'sql':  patientRightsSql, 'params': {}}
        reportTypeDict = {'paramsValue': {}, 'name': 'lis_report_type', 'table': 'lis_report_type', 'key':'code', 'sql':  reportTypeSql, 'params': {}}
        customerTypeDict = {'paramsValue': {}, 'name': 'r_customer_type', 'table': 'r_customer_type', 'key':'customer_type_skey', 'sql':  customerTypeSql, 'params': {}}
        labStatusDict = {'paramsValue': {}, 'name': 'lis_r_lab_status', 'table': 'lis_r_lab_status', 'key':'code', 'sql':  labStatusSql, 'params': {}}
        testItemStatusDict = {'paramsValue': {}, 'name': 'lis_r_test_item_status', 'table': 'lis_r_test_item_status', 'key':'code', 'sql':  testItemStatusSql, 'params': {}}
        pathoPriorityDict = {'paramsValue': {}, 'name': 'patho_priority', 'table': 'patho_priority', 'key':'priority_cd', 'sql':  pathoPrioritySql, 'params': {}}
        logicalLocationDict = {'paramsValue': {}, 'name': 'lis_logical_location', 'table': 'lis_logical_location', 'key':'code', 'sql':  logicalLocationSql, 'params': {}}
        subCategoryDict = {'paramsValue': {}, 'name': 'lis_sub_category', 'table': 'lis_sub_category', 'key':'sub_category_skey', 'sql':  subCategorySql, 'params': {}}
        specimenStickerDict = {'paramsValue': {}, 'name': 'lis_specimen_sticker', 'table': 'lis_specimen_sticker', 'key':'sticker_cd', 'sql':  specimenStickerSql, 'params': {}}
        analyzerModelDict = {'paramsValue': {}, 'name': 'lis_analyzer_model', 'table': 'lis_analyzer_model', 'key':'model_skey', 'sql':  analyzerModelSql, 'params': {}}

        dropdownNode = Node(dropdownDict)
        patientRightsNode = Node(patientRightsDict)
        reportTypeNode = Node(reportTypeDict)
        customerTypeNode = Node(customerTypeDict)
        labStatusNode = Node(labStatusDict)
        testItemStatusNode = Node(testItemStatusDict)
        pathoPriorityNode = Node(pathoPriorityDict)
        logicalLocationNode = Node(logicalLocationDict)
        subCategoryNode = Node(subCategoryDict)
        specimenStickerNode = Node(specimenStickerDict)
        analyzerModelNode = Node(analyzerModelDict)

        dropdownNode.add_child(patientRightsNode)
        dropdownNode.add_child(reportTypeNode)
        dropdownNode.add_child(customerTypeNode)
        dropdownNode.add_child(labStatusNode)
        dropdownNode.add_child(testItemStatusNode)
        dropdownNode.add_child(pathoPriorityNode)
        dropdownNode.add_child(logicalLocationNode)
        dropdownNode.add_child(subCategoryNode)
        dropdownNode.add_child(specimenStickerNode)
        dropdownNode.add_child(analyzerModelNode)

        dataDropDown, columnsDropDown = recur_tree(conn, 0, dropdownNode, dropdownNode)

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(dataDropDown,columnsDropDown))]
        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.StandardError as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,pymssqlCustomExceptionMessage(e))]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@lab_order_mssql.route("/labOrder/saveLabOrderMSSQL", methods=['POST'])
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

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        conn.autocommit(False)

        labOrder = dataInput['labOrder']

        orderSkey = labOrder['labOrderData'].get("order_skey", -1)
        orderID = labOrder['labOrderData'].get("order_id", '')

        if labOrder['labOrderData'].get("edit_flag", 0) == 1:
            orderSkey = getNextSequenceMSSQL('lis_lab_order','order_skey','order_skey')
            orderID = getSequenceNumberMSSQL('LIS_LAB_ORDER','',now.year,now.month,now.day,'00000','00','00','00','Y','Y','Y','','','')
            insertLabOrderHeaderMSSQL(conn,labOrder['labOrderData'],orderSkey,orderID)

            cursor = conn.cursor()
            sql = """\
            EXEC sp_lis_lab_order_load_routing @order_id = %(order_id)s;
            """
            params = {'order_id': orderID}
            cursor.execute(sql,params)
        elif labOrder['labOrderData'].get("edit_flag", 0) == 2:
            updateLabOrderHeaderMSSQL(conn,labOrder['labOrderData'])

        for lab_order_item in labOrder['labOrderData']['lab_order_items_delete']:
            lis_lab_order_item_mssql.deleteLabOrderItemMSSQL(conn,lab_order_item)

        for lab_order_item in list(filter(lambda x: x['edit_flag'] == 1, labOrder['labOrderData']['lab_order_items'])):
            lis_lab_order_item_mssql.insertLabOrderItemMSSQL(conn,lab_order_item)

        for lab_order_item in list(filter(lambda x: x['edit_flag'] == 2, labOrder['labOrderData']['lab_order_items'])):
            lis_lab_order_item_mssql.updateLabOrderItemMSSQL(conn,lab_order_item)

        for lab_test_item in list(filter(lambda x: x['edit_flag'] == 2, labOrder['labOrderData']['lab_test_items'])):
            lis_lab_test_item_mssql.updateLabTestItemMSSQL(conn,lab_test_item)

        # for lab_order_item in labOrder['deleteData']['orderItem']:
        #     lis_lab_order_item_mssql.deleteLabOrderItemMySQL(conn,lab_order_item)

        conn.commit()

        print('commit')

        returnDataColumns = ['order_skey','order_id']
        returnData = [(orderSkey,orderID)]

        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'บันทึก Lab Order เรียบร้อย',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.StandardError as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,pymssqlCustomExceptionMessage(e))]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        conn.rollback()

        print('rollback')

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

def insertLabOrderHeaderMSSQL(conn,labOrder,orderSkey,orderID):
    try:
        now = datetime.datetime.now()

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        # orderSkey = getNextSequenceMSSQL('lis_lab_order','order_skey','order_skey')
        # orderID = getSequenceNumberMSSQL('LIS_LAB_ORDER','',now.year,now.month,now.day,'00000','00','00','00','Y','Y','Y','','','')
        visitSkey = labOrder.get("visit_skey", None)
        priorityCode = labOrder.get("priority_cd", '')
        status = labOrder.get("status", '')
        custSkey = labOrder.get("cust_skey", None)
        currentSpecimenType = labOrder.get("current_specimen_type", 0)
        reportTypeCode = labOrder.get("report_type_cd", 0)

        # collectionDate = datetime.datetime.strptime(labOrder.get("collection_date", '2000-01-01'), '%Y-%m-%d %H:%M:%S')
        # receivedDate = datetime.datetime.strptime(labOrder.get("received_date", '2000-01-01'), '%Y-%m-%d %H:%M:%S')
        collectionDate = parse(labOrder.get("collection_date", '2000-01-01'))
        receivedDate = parse(labOrder.get("received_date", '2000-01-01'))
        physicianNo = labOrder.get("physician_no_1", '')
        logicalLocationCode = labOrder.get("logical_location_cd", '')

        cursor = conn.cursor()
        sql = """\
        insert into lis_lab_order
        (order_skey,order_id,visit_skey,priority_cd,status,cust_skey,current_specimen_type,report_type_cd,collection_date,received_date,physician_no_1,logical_location_cd,date_created,user_created,date_changed,user_changed)
        values(%(order_skey)s,%(order_id)s,%(visit_skey)s,%(priority_cd)s,%(status)s,%(cust_skey)s,%(current_specimen_type)s,%(report_type_cd)s,%(collection_date)s,%(received_date)s,%(physician_no_1)s,%(logical_location_cd)s,%(date_created)s,%(user_created)s,%(date_changed)s,%(user_changed)s)
        """
        params = {'order_skey': orderSkey,'order_id': orderID,'visit_skey': visitSkey,'priority_cd': priorityCode,
        'status': status,'cust_skey': custSkey,'current_specimen_type': currentSpecimenType,'report_type_cd': reportTypeCode,
        'collection_date': collectionDate,'received_date': receivedDate,'physician_no_1': physicianNo,
        'logical_location_cd': logicalLocationCode,'date_created': now,'user_created': userID,
        'date_changed': now,'user_changed': userID}

        cursor.execute(sql,params)
    except Exception as e:
        raise e

def updateLabOrderHeaderMSSQL(conn,labOrder):
    try:
        now = datetime.datetime.now()

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        orderSkey = labOrder.get("order_skey", -1)
        orderID = labOrder.get("order_id", '')
        visitSkey = labOrder.get("visit_skey", -1)
        priorityCode = labOrder.get("priority_cd", '')
        status = labOrder.get("status", '')
        custSkey = labOrder.get("cust_skey", -1)
        currentSpecimenType = labOrder.get("current_specimen_type", 0)
        reportTypeCode = labOrder.get("report_type_cd", 0)

        # collectionDate = datetime.datetime.strptime(labOrder.get("collection_date", '2000-01-01'), '%Y-%m-%d %H:%M:%S')
        # receivedDate = datetime.datetime.strptime(labOrder.get("received_date", '2000-01-01'), '%Y-%m-%d %H:%M:%S')
        collectionDate = parse(labOrder.get("collection_date", '2000-01-01'))
        receivedDate = parse(labOrder.get("received_date", '2000-01-01'))
        physicianNo = labOrder.get("physician_no_1", '')
        logicalLocationCode = labOrder.get("logical_location_cd", '')

        cursor = conn.cursor()
        sql = """\
        update lis_lab_order
        set visit_skey = %(visit_skey)s,
        priority_cd = %(priority_cd)s,
        status = %(status)s,
        cust_skey = %(cust_skey)s,
        current_specimen_type = %(current_specimen_type)s,
        report_type_cd = %(report_type_cd)s,
        collection_date = %(collection_date)s,
        received_date = %(received_date)s,
        physician_no_1 = %(physician_no_1)s,
        logical_location_cd = %(logical_location_cd)s,
        date_changed = %(date_changed)s,
        user_changed = %(user_changed)s
        where order_skey = %(order_skey)s
        """
        params = {'order_skey': orderSkey,'order_id': orderID,'visit_skey': visitSkey,'priority_cd': priorityCode,
        'status': status,'cust_skey': custSkey,'current_specimen_type': currentSpecimenType,'report_type_cd': reportTypeCode,
        'collection_date': collectionDate,'received_date': receivedDate,'physician_no_1': physicianNo,
        'logical_location_cd': logicalLocationCode,'date_created': now,'user_created': userID,
        'date_changed': now,'user_changed': userID}

        cursor.execute(sql,params)
    except Exception as e:
        raise e

@lab_order_mssql.route("/labOrder/openLabOrderMSSQL", methods=['POST'])
def openLabOrderMSSQL():
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
        paramList = ['order_id']
        paramCheckStringList = ['order_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderID = dataInput['order_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        conn.autocommit(False)

        sql = """\
        EXEC sp_lis_lab_order_open @order_id = %(order_id)s
        """
        params = {'order_id': orderID}
        cursor.execute(sql,params)

        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Open Order เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.StandardError as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,pymssqlCustomExceptionMessage(e))]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        conn.rollback()

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@lab_order_mssql.route("/labOrder/cancelLabOrderMSSQL", methods=['POST'])
def cancelLabOrderMSSQL():
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
        paramList = ['order_id']
        paramCheckStringList = ['order_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderID = dataInput['order_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        conn.autocommit(False)

        sql = """\
        EXEC sp_lis_lab_order_cancel @order_id = %(order_id)s
        """
        params = {'order_id': orderID}
        cursor.execute(sql,params)

        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Cancel Order เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.StandardError as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,pymssqlCustomExceptionMessage(e))]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        conn.rollback()

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@lab_order_mssql.route("/labOrder/releasedLabOrderMSSQL", methods=['POST'])
def releasedLabOrderMSSQL():
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
        paramList = ['order_id']
        paramCheckStringList = ['order_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderID = dataInput['order_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        conn.autocommit(False)

        sql = """\
        EXEC sp_lis_lab_order_release @order_id = %(order_id)s
        """
        params = {'order_id': orderID}
        cursor.execute(sql,params)

        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Released Order เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.StandardError as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,pymssqlCustomExceptionMessage(e))]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        conn.rollback()

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@lab_order_mssql.route("/labOrder/calcPriceLabOrderMSSQL", methods=['POST'])
def calcPriceLabOrderMSSQL():
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
        paramList = ['order_id']
        paramCheckStringList = ['order_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderID = dataInput['order_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        conn.autocommit(False)

        sql = """\
        EXEC sp_lis_lab_order_calc_price @order_id = %(order_id)s
        """
        params = {'order_id': orderID}
        cursor.execute(sql,params)

        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Calculate Price เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.StandardError as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,pymssqlCustomExceptionMessage(e))]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        conn.rollback()

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@lab_order_mssql.route("/labOrder/calcAttributeLabOrderMSSQL", methods=['POST'])
def calcAttributeLabOrderMSSQL():
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
        paramList = ['order_id']
        paramCheckStringList = ['order_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderID = dataInput['order_id']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        conn.autocommit(False)

        sql = """\
        EXEC sp_lis_lab_order_calc_attr @order_id = %(order_id)s
        """
        params = {'order_id': orderID}
        cursor.execute(sql,params)

        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Calculate Attribute เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.StandardError as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,pymssqlCustomExceptionMessage(e))]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        conn.rollback()

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
