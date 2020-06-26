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

schedule_resource_mssql = Blueprint('schedule_resource_mssql', __name__)

@schedule_resource_mssql.route("/labOrder/retrieveScheduleMSSQL", methods=['POST'])
def retrieveScheduleMSSQL():
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

        dataSql = """\
        select 1 as code
        """
        ScheduleSql = """\
        exec sp_schedule_resource
        """
        resourceSql = """\
        select resource_id as id,resource_name as name from sch_resource_mstr
        """

        dataDict = {'paramsValue': {}, 'name': 'data', 'table': 'dropdown', 'key':'code', 'sql':  dataSql, 'params': {}}
        ScheduleDict = {'paramsValue': {}, 'name': 'schedule', 'table': 'schedule', 'key':'code', 'sql':  ScheduleSql, 'params': {}}
        resourceDict = {'paramsValue': {}, 'name': 'resource', 'table': 'resource', 'key':'code', 'sql':  resourceSql, 'params': {}}

        dataNode = Node(dataDict)
        ScheduleNode = Node(ScheduleDict)
        resourceNode = Node(resourceDict)

        dataNode.add_child(ScheduleNode)
        dataNode.add_child(resourceNode)

        dataDropDown, columnsDropDown = recur_tree(conn, 0, dataNode, dataNode)

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(dataDropDown,columnsDropDown))]
        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@schedule_resource_mssql.route("/labOrder/saveScheduleMSSQL", methods=['POST'])
def saveScheduleMSSQL():
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
        paramList = ['scheduleResource']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        scheduleResource = dataInput.get("scheduleResource", "")

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()

        for schedule in scheduleResource:
            prodRoutingID = schedule['id']
            resourceID = schedule['resource']
            startDate = datetime.datetime.fromisoformat(schedule['start'].replace("T", " "))
            endDate = datetime.datetime.fromisoformat(schedule['end'].replace("T", " "))
            startedFlag = schedule['started_flag']

            if not startedFlag or startedFlag == None:
                sql = """\
                update sch_prod_routing
                set allocated_resource_id = %(allocated_resource_id)s,
                proc_start_time = %(proc_start_time)s,
                proc_end_time = %(proc_end_time)s
                where prod_routing_id = %(prod_routing_id)s
                """
                params = {'prod_routing_id': prodRoutingID,'allocated_resource_id': resourceID,'proc_start_time': startDate,'proc_end_time': endDate}
                cursor.execute(sql,params)
            else:
                sql = """\
                update sch_prod_routing
                set actual_resource_id = %(actual_resource_id)s,
                actual_proc_start_time = %(actual_proc_start_time)s,
                midbatch_time = %(midbatch_time)s
                where prod_routing_id = %(prod_routing_id)s
                """
                params = {'prod_routing_id': prodRoutingID,'actual_resource_id': resourceID,'actual_proc_start_time': startDate,'midbatch_time': endDate}
                cursor.execute(sql,params)

            # print('start',startDate)
            # print('end',schedule['end'])
            # print('op_no',schedule['op_no'])
            # print('op_name',schedule['op_name'])
            # print('resource',schedule['resource'])
            # print('resource_name',schedule['resource_name'])
            # print('order_no',schedule['text'])

        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'บันทึก Schedule Resource เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
