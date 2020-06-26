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

nav_node_mssql = Blueprint('nav_node_mssql', __name__)

@nav_node_mssql.route("/navigation/retrieveNodeDefMSSQL", methods=['POST'])
def retrieveNodeDefMSSQL():
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

        nodeDefSql = """\
        select pn_node_def.*,pn_logical_win.win_skey,pc_window_def.win_name,
        case when node_type = 'L' then 'Logical Window' else 'Waypoint' end as node_type_desc
        from pn_node_def left outer join pn_logical_win on
        pn_node_def.node_skey = pn_logical_win.node_skey left outer join pc_window_def on
        pn_logical_win.win_skey = pc_window_def.win_skey
        where pn_node_def.app_skey = %(app_skey)s
        """

        logicalWindowSql = """\
        select pn_logical_win.*,pc_window_def.win_name from pn_logical_win left
        outer join pc_window_def on
        pn_logical_win.win_skey = pc_window_def.win_skey
        where pn_logical_win.app_skey = %(app_skey)s and
        pn_logical_win.node_skey = %(node_skey)s
        """

        nodelanguageSql = """\
        select newid() as uid,pn_node_language.app_skey,pn_node_language.node_skey,pn_node_language.language_skey,
    	pn_node_language.node_name,language_def.language_id,language_def.language_comment
    	from pn_node_def inner join pn_node_language on
        pn_node_def.node_skey = pn_node_language.node_skey inner join language_def on
        pn_node_language.language_skey = language_def.language_skey
        where pn_node_def.app_skey = %(app_skey)s and
        pn_node_def.node_skey = %(node_skey)s
        """

        nodeDefDict = {'name': 'node', 'table': 'pn_node_def', 'key':'app_skey,node_skey', 'sql': nodeDefSql, 'params': {'app_skey': 4}}
        logicalWindowDict = {'name': 'logical_window', 'table': 'pn_logical_win', 'key':'app_skey,win_skey', 'sql': logicalWindowSql, 'params': {'app_skey': 'app_skey', 'node_skey': 'node_skey'}}
        nodelanguageDict = {'name': 'node_language', 'table': 'pn_node_language', 'key':'app_skey,node_skey,language_skey', 'sql': nodelanguageSql, 'params': {'app_skey': 'app_skey', 'node_skey': 'node_skey'},
        'selectedVDataTable': 'selectedLanguage','searchVDataTable': 'searchLanguage', 'paginationVDataTable' : {'name' : 'paginationLanguageDict', 'sortBy' : 'language_comment','rowsPerPage' : 20}}

        nodeDefNode = Node(nodeDefDict)
        logicalWindowNode = Node(logicalWindowDict)
        nodelanguageNode = Node(nodelanguageDict)

        nodeDefNode.add_child(logicalWindowNode)
        nodeDefNode.add_child(nodelanguageNode)

        dataNodeDef, columnsNodeDef = recur_tree(conn, 0, nodeDefNode, nodeDefNode)

        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(dataNodeDef,columnsNodeDef))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_node_mssql.route("/navigation/addNodeDefMSSQL", methods=['POST'])
def addNodeDefMSSQL():
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
        paramList = ['app_skey','node_type','node_name']
        paramCheckStringList = ['node_type','node_name']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        nodeType = dataInput['node_type']
        nodeName = dataInput['node_name']
        winSkey = -1
        if 'win_skey' in dataInput:
            winSkey = dataInput['win_skey']

        if nodeType == 'L':
            paramList = ['win_skey'];

            msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
            if msgError != None:
                return jsonify(msgError);

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = "select count(1) from pn_node_def where node_name = %(node_name)s"
        params = {'node_name': nodeName}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows>0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Node already " + nodeName

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        nodeSkey = getNextSequenceMSSQL('pn_node_def','node_skey','node_skey')
        sql = """\
        insert into pn_node_def
        (node_skey,app_skey,node_type,node_name,separator_ind,create_user_id,create_date,maint_user_id,maint_date)
        values(%(node_skey)s,%(app_skey)s,%(node_type)s,%(node_name)s,0,%(user_id)s,getdate(),%(user_id)s,getdate())
        """
        params = {'node_skey': nodeSkey,'app_skey': appSkey,'node_type': nodeType,'node_name': nodeName,'user_id': userID}
        cursor.execute(sql,params)
        conn.commit()
        if nodeType == 'L':
            sql = """\
            insert into pn_logical_win
            (app_skey,node_skey,win_skey,menu_position,window_title,create_user_id,create_date,maint_user_id,maint_date)
            values(%(app_skey)s,%(node_skey)s,%(win_skey)s,0,%(window_title)s,%(user_id)s,getdate(),%(user_id)s,getdate())
            """
            params = {'app_skey': appSkey,'node_skey': nodeSkey,'win_skey': winSkey,'window_title': nodeName,'user_id': userID}
            cursor.execute(sql,params)
            conn.commit()

        cursor.close()
        conn.close()

        returnDataColumns = ['app_skey','node_skey','win_skey']
        returnData = [(appSkey,nodeSkey,winSkey)]
        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'สร้าง Node เรียบร้อย',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_node_mssql.route("/navigation/updateNodeDefMSSQL", methods=['POST'])
def updateNodeDefMSSQL():
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
        paramList = ['app_skey','node_skey','node_type','node_name']
        paramCheckStringList = ['node_type','node_name']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        nodeSkey = dataInput['node_skey']
        nodeType = dataInput['node_type']
        nodeName = dataInput['node_name']
        winSkey = -1
        if 'win_skey' in dataInput:
            winSkey = dataInput['win_skey']

        if nodeType == 'L':
            paramList = ['win_skey'];

            msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
            if msgError != None:
                return jsonify(msgError);

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        select count(1) from pn_node_def
        where app_skey = %(app_skey)s and
        node_skey = %(node_skey)s
        """
        params = {'app_skey': appSkey, 'node_skey': nodeSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid App Skey " +  str(appSkey) + " Node Skey " + str(nodeSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        update pn_node_def
        set node_type = %(node_type)s,
        node_name = %(node_name)s
        where app_skey = %(app_skey)s and
        node_skey = %(node_skey)s
        """
        params = {'app_skey': appSkey, 'node_skey': nodeSkey,'node_type': nodeType,'node_name': nodeName}
        cursor.execute(sql,params)
        conn.commit()

        if nodeType == 'L':
            sql = """\
            select count(1) from pn_logical_win
            where app_skey = %(app_skey)s and
            node_skey = %(node_skey)s
            """
            params = {'app_skey': appSkey, 'node_skey': nodeSkey}
            cursor.execute(sql,params)
            (number_of_rows,)=cursor.fetchone()

            if number_of_rows==0:
                sql = """\
                insert into pn_logical_win
                (app_skey,node_skey,win_skey,menu_position,window_title,create_user_id,create_date,maint_user_id,maint_date)
                values(%(app_skey)s,%(node_skey)s,%(win_skey)s,0,%(window_title)s,%(user_id)s,getdate(),%(user_id)s,getdate())
                """
                params = {'app_skey': appSkey,'node_skey': nodeSkey,'win_skey': winSkey,'window_title': nodeName,'user_id': userID}
                cursor.execute(sql,params)
                conn.commit()
            else:
                sql = """\
                update pn_logical_win
                set window_title = %(window_title)s,
                maint_user_id = %(user_id)s,
                maint_date = getdate()
                where app_skey = %(app_skey)s and
                node_skey = %(node_skey)s and
                win_skey = %(win_skey)s
                """
                params = {'app_skey': appSkey,'node_skey': nodeSkey,'win_skey': winSkey,'window_title': nodeName,'user_id': userID}
                cursor.execute(sql,params)
                conn.commit()
        else:
            sql = """\
            delete from pn_logical_win
            where app_skey = %(app_skey)s and
            node_skey = %(node_skey)s and
            win_skey = %(win_skey)s
            """
            params = {'app_skey': appSkey,'node_skey': nodeSkey,'win_skey': winSkey}
            cursor.execute(sql,params)
            conn.commit()

        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Update Component เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@nav_node_mssql.route("/navigation/deleteNodeDefMSSQL", methods=['POST'])
def deleteNodeDefMSSQL():
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
        paramList = ['app_skey','node_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appSkey = dataInput['app_skey']
        nodeSkey = dataInput['node_skey']

        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
        cursor = conn.cursor()
        sql = """\
        select count(1) from pn_node_def
        where app_skey = %(app_skey)s and node_skey = %(node_skey)s
        """
        params = {'app_skey': appSkey, 'node_skey': nodeSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid App Skey " +  str(appSkey) + " Node Skey " + str(nodeSkey)

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        sql = """\
        delete from pn_logical_win
        where app_skey = %(app_skey)s and node_skey = %(node_skey)s
        """
        params = {'app_skey': appSkey, 'node_skey': nodeSkey}
        cursor.execute(sql,params)
        conn.commit()

        sql = """\
        delete from pn_node_def
        where app_skey = %(app_skey)s and node_skey = %(node_skey)s
        """
        params = {'app_skey': appSkey, 'node_skey': nodeSkey}
        cursor.execute(sql,params)
        conn.commit()

        cursor.close()
        conn.close()

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'Delete Node เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
