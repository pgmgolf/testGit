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

lab_order_manual_result = Blueprint('lab_order_manual_result', __name__)

@lab_order_manual_result.route("/labOrderManualResult/retrieveLabOrderManualResultMSSQL", methods=['POST'])
def retrieveLabOrderManualResultMSSQL():
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
        paramList = ['facility_cd','hn','from_received_date','to_received_date','category','category_status','patient_type_code','status_cancel','his_reject']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        facilityCode = dataInput['facility_cd']
        hn = dataInput['hn']
        fromReceivedDate = None
        toReceivedDate = None
        category = ''
        if dataInput['from_received_date'] != None:
            fromReceivedDate = datetime.datetime.fromisoformat(dataInput['from_received_date'].replace("Z", ""))
        if dataInput['to_received_date'] != None:
            toReceivedDate = datetime.datetime.fromisoformat(dataInput['to_received_date'].replace("Z", ""))
        if dataInput['category'] != None:
            category = ','.join(str(x) for x in dataInput['category'])
        patientTypeCode = dataInput['patient_type_code']
        categoryStatus = dataInput['category_status']
        statusCancel = dataInput['status_cancel']
        hisReject = dataInput['his_reject']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        select lis_lab_order.order_skey,lis_lab_order.order_id,lis_lab_order.received_date,lis_lab_order.hospital_lab_no,lis_lab_order.order_department,lis_logical_location.patient_type_code,
        lis_lab_order.lab_receive_number,lis_patient.hn,patho_prefix.prefix_desc + '' + lis_patient.firstname + ' ' + lis_patient.lastname as patient_name,tmp_category_status.category_status,
        patho_priority.priority_cd,patho_priority.priority_desc,patho_priority.color as bk_color,
        (Select Case min(Case When category_result_status = 'Cancel' then 1 when category_result_status = 'Pending' then 2 else 3 end)
        when 1 then 'Cancel' when 2 then 'Pending' else 'Approved' end from lis_lab_category where lis_lab_category.order_skey = lis_lab_order.order_skey
        """
        if statusCancel:
            if len(category) > 0:
                sql = sql + """\
                and lis_lab_category.category_skey in ({})
                """.format(category)
        sql = sql + """\
        ) as category_result_status,
        (select case when ROW_NUMBER() OVER(ORDER BY lis_lab_specimen_type.specimen_type_id) = 1 then '' else ' , ' end +lis_lab_specimen_type.specimen_type_id
        from lis_lab_specimen_type
        where lis_lab_specimen_type.order_skey = lis_lab_order.order_skey
        for xml path( '' )) as specimen_type_id_list,
        (select count(1) from (select specimen_type_id,model_skey from lis_lab_specimen_type_test_item
        where lis_lab_specimen_type_test_item.order_skey = lis_lab_order.order_skey and date_scanned is not null and analyzer_two_way = 1 group by specimen_type_id,model_skey) tmp) as scanned_tube,
        (select count(1) from (select specimen_type_id,model_skey from lis_lab_specimen_type_test_item
        where lis_lab_specimen_type_test_item.order_skey = lis_lab_order.order_skey and analyzer_two_way = 1 group by specimen_type_id,model_skey) tmp) as total_tube
        from lis_lab_order inner join lis_visit on
        lis_lab_order.visit_skey = lis_visit.visit_skey inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd inner join lis_logical_location on
        lis_lab_order.logical_location_cd = lis_logical_location.code inner join lis_patient_type on
        lis_logical_location.patient_type_code = lis_patient_type.code inner join patho_priority on
        lis_lab_order.priority_cd = patho_priority.priority_cd inner join lis_lab_order_item on
        lis_lab_order.order_skey = lis_lab_order_item.order_skey inner join lis_lab_order_test_item on
        lis_lab_order_item.order_skey = lis_lab_order_test_item.order_skey and
        lis_lab_order_item.order_item_skey = lis_lab_order_test_item.order_item_skey inner join lis_lab_test_item on
        lis_lab_order.order_skey = lis_lab_test_item.order_skey and
        lis_lab_order_test_item.test_item_skey = lis_lab_test_item.test_item_skey inner join lis_sub_category on
        lis_lab_test_item.sub_category_skey = lis_sub_category.sub_category_skey inner join lis_category on
        lis_sub_category.category_skey = lis_category.category_skey inner join lis_test_item on
        lis_lab_test_item.test_item_skey = lis_test_item.test_item_skey
        """
        if statusCancel:
            sql = sql + """\
            left outer join
            """
        else:
            sql = sql + """\
            inner join
            """
        sql = sql + """\
        (select order_skey,min(category_status) as category_status from lis_lab_category where (1 = 1)
        """
        if len(categoryStatus) > 0:
            sql = sql + """\
            and lis_lab_category.category_result_status = '{}'
            """.format(categoryStatus)
        if len(category) > 0:
            sql = sql + """\
            and lis_lab_category.category_skey in ({})
            """.format(category)
        sql = sql + """\
        group by order_skey) tmp_category_status on lis_lab_order.order_skey = tmp_category_status.order_skey
        where lis_lab_order_item.active = 1 and
        lis_lab_order_item.cancel = 0 and lis_lab_test_item.status <> 'CA' and
        """
        if statusCancel:
            sql = sql + """\
            lis_lab_order.status = 'CA' and
            """
        else:
            sql = sql + """\
            lis_lab_order.status <> 'CA' and
            lis_lab_order.lab_status in ('COLLECTION','RECEIVED','FIRSTAPPROVE','LASTAPPROVE','RL') and
            """
        if hisReject:
            sql = sql + """\
            lis_lab_order.hos_reject = 1 and
            """
        if getGlobalParamMSSQL('LIS_DISPLAY_LAB_REJECT_MANUAL_RESULT').upper() == 'N':
            sql = sql + """\
            (lis_lab_order.hos_reject = 0 or lis_lab_order.hos_reject is null) and
            """
        sql = sql + """\
        (lis_visit.facility_cd = %(facility_cd)s or 1 = case when %(facility_cd)s is null or len(%(facility_cd)s) < 1 then 1 else 2 end) and
        (lis_patient.hn like %(hn)s or 1 = case when %(hn)s is null or len(%(hn)s) < 1 then 1 else 2 end) and
        (dateadd(dd,0,datediff(dd,0,lis_lab_order.received_date)) >= dateadd(dd,0,datediff(dd,0,%(from_received_date)s)) or 1 = case when %(from_received_date)s is null then 1 else 2 end) and
        (dateadd(dd,0,datediff(dd,0,lis_lab_order.received_date)) <= dateadd(dd,0,datediff(dd,0,%(to_received_date)s)) or 1 = case when %(to_received_date)s is null then 1 else 2 end) and
        (lis_logical_location.patient_type_code = %(patient_type_code)s or 1 = case when %(patient_type_code)s is null or len(%(patient_type_code)s) < 1 then 1 else 2 end)
        """
        if not statusCancel:
            if len(category) > 0:
                sql = sql + """\
                and lis_category.category_skey in ({})
                """.format(category)
                if len(category.split(',')) > 1:
                    if len(categoryStatus) > 0:
                        sql = sql + """\
                        and lis_lab_order.lab_result_status like '{}'
                        """.format(categoryStatus)
            else:
                if len(categoryStatus) > 0:
                    sql = sql + """\
                    and lis_lab_order.lab_result_status like '{}'
                    """.format(categoryStatus)
        sql = sql + """\
        group by lis_lab_order.order_skey,lis_lab_order.order_id,lis_lab_order.received_date,lis_lab_order.hospital_lab_no,lis_lab_order.order_department,lis_logical_location.patient_type_code,
        lis_lab_order.lab_test_item_status,lis_lab_order.lab_receive_number,lis_patient.hn,patho_prefix.prefix_desc,patho_sex.sex_desc,
        patho_prefix.prefix_desc,lis_patient.firstname,lis_patient.lastname,tmp_category_status.category_status,
        patho_priority.priority_cd,patho_priority.priority_desc,patho_priority.color
        order by case when patho_priority.priority_cd = 'Urgent' then case tmp_category_status.category_status when 'C1' then 3 else 1 end else
        case tmp_category_status.category_status when 'C1' then 4 else 2 end end,
        case tmp_category_status.category_status when 'C3' then 1
        when 'C2' then 2
        when 'C1' then 3 end,lis_lab_order.order_id
        """

        params = {'facility_cd': facilityCode, 'hn': hn, 'from_received_date': fromReceivedDate, 'to_received_date': toReceivedDate, 'patient_type_code': patientTypeCode}
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

@lab_order_manual_result.route("/labOrderManualResult/retrieveDropDownMSSQL", methods=['POST'])
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
        CatogorySql = """\
        select category_skey,category_id,category_desc from lis_category
        """

        dropdownDict = {'paramsValue': {}, 'name': 'dropdown', 'table': 'dropdown', 'key':'code', 'sql':  dropdownSql, 'params': {}}
        CatogoryDict = {'paramsValue': {}, 'name': 'lis_category', 'table': 'lis_category', 'key':'category_skey', 'sql':  CatogorySql, 'params': {}}

        dropdownNode = Node(dropdownDict)
        CatogoryNode = Node(CatogoryDict)

        dropdownNode.add_child(CatogoryNode)

        dataDropDown, columnsDropDown = recur_tree(conn, 0, dropdownNode, dropdownNode)

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(dataDropDown,columnsDropDown))]
        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@lab_order_manual_result.route("/labOrderManualResult/retrieveLabOrderMSSQL", methods=['POST'])
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
        paramList = ['order_id']
        paramCheckStringList = ['order_id']

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
        lis_logical_location.description as logical_location_desc,lis_lab_order.report_type_cd,lis_lab_order.ignore_type,lis_lab_order.patient_rights_cd,
        lis_lab_order.form_name,lis_lab_order.request_by,lis_lab_order.sent_to_dept,lis_lab_order.department,lis_lab_order.order_department,
        lis_visit.visit_id,lis_visit.logical_location_cd,lis_visit.facility_cd,facility.facility_name,view_lis_visit_patient.birthday,
        view_lis_visit_patient.patient_fullname,patho_sex.sex_desc,view_lis_visit_patient.date_arrived_year,view_lis_visit_patient.date_arrived_month,view_lis_visit_patient.date_arrived_day,
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
        lis_lab_order.cust_skey = customer.cust_skey inner join lis_logical_location on
        lis_visit.logical_location_cd = lis_logical_location.code left outer join view_patho_physician as view_patho_physician_1 on
        lis_lab_order.physician_no_1 = view_patho_physician_1.physician_no left outer join view_patho_technician on
        lis_lab_order.technician_no = view_patho_technician.technician_no left outer join proj_header on
        lis_lab_order.proj_cd = proj_header.proj_cd
        where lis_lab_order.order_id = %(order_id)s
        """

        labOrderCategorySql = """\
        select lis_lab_order.order_skey,lis_lab_order.order_id,lis_category.category_skey,lis_category.category_id,lis_category.category_desc,
        lis_lab_category.category_status,'Y' as check_flag
        from lis_lab_order inner join lis_visit on
        lis_lab_order.visit_skey = lis_visit.visit_skey inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join lis_lab_test_item on
        lis_lab_order.order_skey = lis_lab_test_item.order_skey inner join lis_sub_category on
        lis_lab_test_item.sub_category_skey = lis_sub_category.sub_category_skey inner join lis_category on
        lis_sub_category.category_skey = lis_category.category_skey inner join lis_test_item on
        lis_lab_test_item.test_item_skey = lis_test_item.test_item_skey left outer join lis_lab_category on
        lis_lab_order.order_skey = lis_lab_category.order_skey and
        lis_category.category_skey = lis_lab_category.category_skey
        where lis_lab_order.order_skey = %(order_skey)s
        group by lis_lab_order.order_skey,lis_lab_order.order_id,lis_patient.patient_skey,lis_category.category_skey,lis_category.category_id,lis_category.category_desc,
        lis_lab_category.category_status
        """

        labOrderTestItemSql = """\
        select lis_visit.patient_skey,lis_lab_test_item.order_skey,lis_lab_test_item.test_item_skey,lis_lab_test_item.complete_flag,lis_lab_test_item.complete_date,lis_lab_test_item.vendor_skey,lis_lab_test_item.due_date,
        lis_lab_test_item.sent_date,lis_lab_test_item.job_doc_no,lis_lab_test_item.remark,lis_lab_test_item.status,lis_lab_test_item.sub_category_skey,lis_lab_test_item.due_date_outlab,lis_lab_test_item.required_all_result_item,
        lis_lab_test_item.sticker_cd,lis_lab_test_item.test_item_status,lis_lab_test_item.reject_flag,lis_lab_order.order_id,lis_test_item.test_item_id,lis_test_item.test_item_desc,lis_test_item.alias_id as test_item_alias_id,lis_test_item.differential_flag,lis_lab_test_item.reject_flag,
        lis_category.category_skey,lis_lab_category.category_status,lis_lab_test_item.test_item_status,vendor_master.name as vendor_name,case when hist > 0 then 'H' else '' end as history,'Y' as check_flag
        from lis_lab_order inner join lis_visit on
        lis_lab_order.visit_skey = lis_visit.visit_skey inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join lis_lab_test_item on
        lis_lab_order.order_skey = lis_lab_test_item.order_skey inner join lis_sub_category on
        lis_lab_test_item.sub_category_skey = lis_sub_category.sub_category_skey inner join lis_category on
        lis_sub_category.category_skey = lis_category.category_skey inner join lis_test_item on
        lis_lab_test_item.test_item_skey = lis_test_item.test_item_skey left outer join vendor_master on
        lis_lab_test_item.vendor_skey = vendor_master.vendor_skey left outer join lis_lab_category on
        lis_lab_order.order_skey = lis_lab_category.order_skey and
        lis_category.category_skey = lis_lab_category.category_skey OUTER APPLY
        (select distinct 1 as hist from lis_lab_order o inner join lis_visit v on
        o.visit_skey = v.visit_skey inner join lis_patient p on
        v.patient_skey = p.patient_skey inner join lis_lab_test_item t on
        o.order_skey = t.order_skey and
        p.patient_skey = lis_patient.patient_skey and
        t.test_item_skey = lis_lab_test_item.test_item_skey
        where o.date_created < lis_lab_order.date_created) tmp
        where lis_lab_order.order_skey = %(order_skey)s and
        lis_category.category_skey = %(category_skey)s
        """

        labOrderResultItemSql = """\
        select lis_visit.patient_skey,lis_lab_result_item.order_skey,lis_lab_result_item.result_item_skey,lis_lab_result_item.result_value,lis_lab_result_item.order_result_skey,lis_lab_result_item.result_type_cd,
        lis_lab_result_item.reference,lis_lab_result_item.comment,lis_lab_result_item.rerun,lis_lab_result_item.critical_alert_value,lis_lab_result_item.result_item_attr_skey,lis_lab_result_item.critical_alert_skey,
        lis_lab_result_item.comment_result_item_attr_skey,lis_lab_order.order_id,lis_category.category_skey,lis_lab_category.category_status,lis_test_item.test_item_skey,lis_test_item.test_item_desc,lis_test_item.alias_id as test_item_alias_id,
        lis_lab_test_item.vendor_skey,lis_lab_test_item.required_all_result_item,lis_result_item.result_item_id,lis_result_item.result_item_desc,lis_result_item.result_type,
        lis_result_item.uom,lis_uom.uom_desc,lis_result_item.formula,lis_result_item.decimal_digit,lis_test_item.method_code,lis_result_type.result_type_desc,lis_result_item.alias_id as result_item_alias_id,
        lis_result_type.color,lis_result_type.critical_alert,lis_result_form_header.result_form_skey,lis_result_form_header.result_form_id,'N' as delta_check,
        (select top 1 reference from lis_result_item_attr_flag
        where lis_result_item_attr_flag.result_item_skey = lis_lab_result_item.result_item_skey and
        lis_result_item_attr_flag.result_item_attr_skey = lis_lab_result_item.result_item_attr_skey and
        normal_flag = 1) as reference_normal,
        '' as result_value_prev,abnormal_flags,
        (select case when ROW_NUMBER() OVER(ORDER BY lis_lab_result_cbc_abnormal.abnormal) = 1 then '' else ' , ' end +lis_lab_result_cbc_abnormal.abnormal
        from lis_lab_result_cbc_abnormal
        where lis_lab_result_cbc_abnormal.order_skey = lis_lab_result_item.order_skey and
        lis_lab_result_cbc_abnormal.order_result_skey = lis_lab_result_item.order_result_skey
        for xml path( '' )) as abnormal_list
        from lis_lab_order inner join lis_visit on
        lis_lab_order.visit_skey = lis_visit.visit_skey inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join lis_lab_test_item on
        lis_lab_order.order_skey = lis_lab_test_item.order_skey inner join lis_lab_test_result_item on
        lis_lab_test_item.order_skey = lis_lab_test_result_item.order_skey and
        lis_lab_test_item.test_item_skey = lis_lab_test_result_item.test_item_skey inner join lis_test_item on
        lis_lab_test_item.test_item_skey = lis_test_item.test_item_skey inner join lis_sub_category on
        lis_lab_test_item.sub_category_skey = lis_sub_category.sub_category_skey inner join lis_category on
        lis_sub_category.category_skey = lis_category.category_skey inner join lis_lab_result_item on
        lis_lab_order.order_skey = lis_lab_result_item.order_skey and
        lis_lab_test_result_item.result_item_skey = lis_lab_result_item.result_item_skey inner join lis_result_item on
        lis_lab_result_item.result_item_skey = lis_result_item.result_item_skey left outer join lis_lab_result_value on
        lis_lab_result_item.order_skey = lis_lab_result_value.order_skey and
        lis_lab_result_item.order_result_skey = lis_lab_result_value.order_result_skey left outer join lis_result_type on
        lis_lab_result_item.result_type_cd = lis_result_type.result_type_cd left outer join lis_uom on
        lis_result_item.uom = lis_uom.uom left outer join lis_result_form_header on
        lis_result_item.result_form_skey = lis_result_form_header.result_form_skey left outer join lis_lab_category on
        lis_lab_order.order_skey = lis_lab_category.order_skey and
        lis_category.category_skey = lis_lab_category.category_skey
        where lis_lab_order.order_skey = %(order_skey)s and
        lis_category.category_skey = %(category_skey)s and
        display_manual_result = 1
        order by lis_lab_test_result_item.seq
        """

        labOrderDict = {'paramsValue': {}, 'name': 'lab_orders', 'table': 'lis_lab_order', 'key':'order_skey', 'sql':  labOrderSql, 'params':  {'order_id' : orderID}}
        labOrderCategoryDict = {'paramsValue': {}, 'name': 'lab_order_categorys', 'table': 'lab_order_category', 'key':'order_skey,category_skey', 'sql':  labOrderCategorySql, 'params':  {'order_skey' : 'order_skey'}}
        labOrderTestItemDict = {'paramsValue': {}, 'name': 'lis_lab_test_items', 'table': 'lis_lab_test_item', 'key':'order_skey,test_item_skey', 'sql':  labOrderTestItemSql, 'params':  {'order_skey' : 'order_skey','category_skey' : 'category_skey'},
        'selectedVDataTable': 'selected_lis_lab_test_items','searchVDataTable': 'search_lis_lab_test_items', 'paginationVDataTable' : {'name' : 'pagination_lis_lab_test_items', 'sortBy' : 'test_item_skey','rowsPerPage' : 20}}
        labOrderResultItemDict = {'paramsValue': {}, 'name': 'lis_lab_result_items', 'table': 'lis_lab_result_item', 'key':'order_skey,result_item_skey', 'sql':  labOrderResultItemSql, 'params':  {'order_skey' : 'order_skey','category_skey' : 'category_skey'}}

        labOrderNode = Node(labOrderDict)
        labOrderCategoryNode = Node(labOrderCategoryDict)
        labOrderTestItemNode = Node(labOrderTestItemDict)
        labOrderResultItemNode = Node(labOrderResultItemDict)

        labOrderNode.add_child(labOrderCategoryNode)
        labOrderCategoryNode.add_child(labOrderTestItemNode)
        labOrderCategoryNode.add_child(labOrderResultItemNode)

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

@lab_order_manual_result.route("/labOrderManualResult/updateResultValueMSSQL", methods=['POST'])
def updateResultValueMSSQL():
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
        paramList = ['order_skey','result_item_skey','result_value']
        paramCheckStringList = ['result_value']
        paramCheckNumberList = ['order_skey','result_item_skey']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderSkey = dataInput['order_skey']
        resultItemSkey = dataInput['result_item_skey']
        resultValue = dataInput['result_value']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        sql = """\
        EXEC sp_lis_lab_update_result_value @order_skey = %(order_skey)s,@result_item_skey = %(result_item_skey)s,@result_value = %(result_value)s;
        """
        params = {'order_skey': orderSkey, 'result_item_skey': resultItemSkey, 'result_value': resultValue}
        cursor.execute(sql,params)
        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Update Result Value เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@lab_order_manual_result.route("/labOrderManualResult/labApproveMSSQL", methods=['POST'])
def labApproveMSSQL():
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

        levelSeq = dataInput['level_seq']
        orderSkey = dataInput['order_skey']
        testItem = dataInput['test_item']
        testItemSkeyList = [test_item['test_item_skey'] for test_item in testItem]
        testItemSkeyList = str(testItemSkeyList).strip('[]')

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        sql = """\
        EXEC sp_lis_lab_approve @level_seq = %(level_seq)s,@order_skey = %(order_skey)s,@category_skey = %(category_skey)s,@test_item_skey_list = %(test_item_skey_list)s,@user = %(user)s;
        """
        params = {'level_seq': levelSeq,'order_skey': orderSkey,'category_skey': 1,'test_item_skey_list': testItemSkeyList,'user': userID}
        cursor.execute(sql,params)
        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Approve เรียบร้อย')]

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

@lab_order_manual_result.route("/labOrderManualResult/labCancelApproveMSSQL", methods=['POST'])
def labCancelApproveMSSQL():
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

        orderSkey = dataInput['order_skey']
        testItem = dataInput['test_item']
        reason = dataInput['reason']
        testItemSkeyList = [test_item['test_item_skey'] for test_item in testItem]
        testItemSkeyList = str(testItemSkeyList).strip('[]')

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        EXEC sp_lis_lab_cancel_approve @order_skey = %(order_skey)s,@category_skey = %(category_skey)s,@test_item_skey_list = %(test_item_skey_list)s,@user = %(user)s,@reason = %(reason)s;
        """
        params = {'order_skey': orderSkey,'category_skey': 1,'test_item_skey_list': testItemSkeyList,'user': userID,'reason': reason}
        cursor.execute(sql,params)
        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Cancel Approve เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except pymssql.Error as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        print(2222,e,type(e))
        errData = [(isSuccess,reasonCode,pymssqlCustomExceptionMessage(e))]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500
        print(type(e))

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
