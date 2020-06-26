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

from db_config import *
from common import *

nav_route_mysql = Blueprint('nav_route_mysql', __name__)

@nav_route_mysql.route("/navigation/retrieveNodeRouteMySQL", methods=['POST'])
def retrieveNodeRouteMySQL():
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
        paramList = ['app_name']
        paramCheckStringList = ['app_name']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appName = dataInput['app_name']

        conn = mysql.connect()
        cursor = conn.cursor()
        args = [appName]
        cursor.callproc('sp_route_maint_sel', args)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
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

@nav_route_mysql.route("/navigation/addNodeRouteMySQL", methods=['POST'])
def addNodeRouteMySQL():
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
        paramList = ['app_skey','from_node_skey','to_node']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        fromNodeSkey = dataInput['from_node_skey']
        toNode = dataInput['to_node']
        conn = mysql.connect()
        cursor = conn.cursor()
        for toNode in toNode:
            if fromNodeSkey == toNode['node_skey']:
                continue
            sql = """\
            select count(1) from pn_node_route
            where app_skey = %(app_skey)s and
            from_node_skey = %(from_node_skey)s and
            to_node_skey = %(to_node_skey)s
            """
            params = {'app_skey': appSkey, 'from_node_skey': fromNodeSkey, 'to_node_skey': toNode['node_skey']}
            cursor.execute(sql,params)
            (number_of_rows,)=cursor.fetchone()

            if number_of_rows==0:
                sql = """\
                select coalesce(max(sort_seq),0) + 1 as max_sort_seq from pn_node_route
                where app_skey = %(app_skey)s and
                from_node_skey = %(from_node_skey)s
                """
                params = {'app_skey': appSkey, 'from_node_skey': fromNodeSkey}
                cursor.execute(sql,params)
                (max_sort_seq,)=cursor.fetchone()

                sql = """\
                insert into pn_node_route
                (app_skey,from_node_skey,to_node_skey,sort_seq,create_user_id,create_date,maint_user_id,maint_date)
                values(%(app_skey)s,%(from_node_skey)s,%(to_node_skey)s,%(sort_seq)s,%(user_id)s,now(),%(user_id)s,now())
                """
                params = {'app_skey': appSkey,'from_node_skey': fromNodeSkey,'to_node_skey': toNode['node_skey'],'sort_seq': max_sort_seq,'user_id': userID}
                cursor.execute(sql,params)
                conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Add Node Route เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_route_mysql.route("/navigation/updateNodeRouteMySQL", methods=['POST'])
def updateNodeRouteMySQL():
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
        paramList = ['app_skey','route_from_node']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        routeFromNode = dataInput['route_from_node']
        conn = mysql.connect()
        cursor = conn.cursor()
        for fromNode in routeFromNode:
            sql = """\
            select count(1) from pn_node_route
            where app_skey = %(app_skey)s and
            from_node_skey = %(from_node_skey)s and
            to_node_skey = %(to_node_skey)s
            """
            params = {'app_skey': appSkey, 'from_node_skey': fromNode['from_node_skey'], 'to_node_skey': fromNode['to_node_skey']}
            cursor.execute(sql,params)
            (number_of_rows,)=cursor.fetchone()

            if number_of_rows==0:
                sql = """\
                insert into pn_node_route
                (app_skey,from_node_skey,to_node_skey,sort_seq,create_user_id,create_date,maint_user_id,maint_date)
                values(%(app_skey)s,%(from_node_skey)s,%(to_node_skey)s,%(sort_seq)s,%(user_id)s,now(),%(user_id)s,now())
                """
                params = {'app_skey': appSkey,'from_node_skey': fromNode['from_node_skey'],'to_node_skey': fromNode['to_node_skey'],'sort_seq': fromNode['sort_seq'],'user_id': userID}
                cursor.execute(sql,params)
                conn.commit()
            else:
                sql = """\
                update pn_node_route
                set sort_seq = %(sort_seq)s,
                maint_user_id = %(user_id)s,
                maint_date = now()
                where app_skey = %(app_skey)s and
                from_node_skey = %(from_node_skey)s and
                to_node_skey = %(to_node_skey)s
                """
                params = {'app_skey': appSkey, 'from_node_skey': fromNode['from_node_skey'], 'to_node_skey': fromNode['to_node_skey'], 'sort_seq': fromNode['sort_seq'], 'user_id': userID}
                cursor.execute(sql,params)
                conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Add Node Route เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_route_mysql.route("/navigation/updateNodeRouteDragTargetMySQL", methods=['POST'])
def updateNodeRouteDragTargetMySQL():
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
        paramList = ['app_skey','drag_from_node_skey','drag_to_node_skey','target_from_node_skey','target_to_node_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        dragFromNodeSkey = dataInput['drag_from_node_skey']
        dragToNodeSkey = dataInput['drag_to_node_skey']
        targetFromNodeSkey = dataInput['target_from_node_skey']
        targetToNodeSkey = dataInput['target_to_node_skey']

        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """\
        select count(1),node_type from pn_node_def
        where app_skey = %(app_skey)s and
        node_skey = %(node_skey)s
        """
        params = {'app_skey': appSkey, 'node_skey': targetToNodeSkey}
        cursor.execute(sql,params)
        (number_of_rows,nodeType)=cursor.fetchone()

        if (number_of_rows==0 or nodeType != 'W') and targetToNodeSkey != 0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Cannot Drag to Node Type Logical Window"

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        update pn_node_route
        set from_node_skey = %(target_from_node_skey)s,
        maint_user_id = %(user_id)s,
        maint_date = now()
        where app_skey = %(app_skey)s and
        from_node_skey = %(drag_from_node_skey)s and
        to_node_skey = %(drag_to_node_skey)s
        """
        params = {'app_skey': appSkey, 'drag_from_node_skey': dragFromNodeSkey, 'drag_to_node_skey': dragToNodeSkey, 'target_from_node_skey': targetToNodeSkey, 'user_id': userID }
        cursor.execute(sql,params)
        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Drag Node Route เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_route_mysql.route("/navigation/deleteNodeRouteMySQL", methods=['POST'])
def deleteNodeRouteMySQL():
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
        paramList = ['app_skey','from_node_skey','to_node_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        fromNodeSkey = dataInput['from_node_skey']
        toNodeSkey = dataInput['to_node_skey']
        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """\
        delete from pn_node_route
        where app_skey = %(app_skey)s and
        from_node_skey = %(from_node_skey)s and
        to_node_skey = %(to_node_skey)s
        """
        params = {'app_skey': appSkey, 'from_node_skey': fromNodeSkey, 'to_node_skey': toNodeSkey}
        cursor.execute(sql,params)
        conn.commit()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Delete Node Route เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_route_mysql.route("/navigation/retrieveNodeRouteFromNodeMySQL", methods=['POST'])
def retrieveNodeRouteFromNodeMySQL():
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
        paramList = ['app_skey','from_node_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        fromNodeSkey = dataInput['from_node_skey']

        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """\
        select pn_node_route.*,pn_node_def.node_name
        from pn_node_route inner join pn_node_def on
        pn_node_route.to_node_skey = pn_node_def.node_skey
        where pn_node_route.app_skey = %(app_skey)s and
        pn_node_route.from_node_skey = %(from_node_skey)s
        """
        params = {'app_skey': appSkey, 'from_node_skey': fromNodeSkey}
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
