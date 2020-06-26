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

nav_window_sercurity_mssql = Blueprint('nav_window_sercurity_mssql', __name__)

@nav_window_sercurity_mssql.route("/navigation/retrieveComponentObjectSecurityMSSQL", methods=['POST'])
def retrieveComponentObjectSecurityMSSQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

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
    select pn_node_def.node_skey,pc_window_def.win_skey,pn_node_def.node_name,pc_window_def.window_comment,
	case when pc_window_def.win_skey is null then 'wp' else 'lw' end as object_type,
    case when pc_window_def.win_skey is null then 'Waypoint' else 'Window' end as object_comment
    from pn_node_def left outer join pn_logical_win on
    pn_node_def.app_skey = pn_logical_win.app_skey and
    pn_node_def.node_skey = pn_logical_win.node_skey left outer join pc_window_def on
    pn_logical_win.app_skey = pc_window_def.app_skey and
    pn_logical_win.win_skey = pc_window_def.win_skey
    where pn_node_def.app_skey = %(app_skey)s and
    pn_node_def.node_skey = %(node_skey)s
    """
    params = {'app_skey': appSkey, 'node_skey': nodeSkey}
    number_of_rows = cursor.execute(sql,params)

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid App Skey " + str(appSkey) + " Node Skey " + str(nodeSkey)

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))
    else:
        (nodeSkey,winSkey,nodeName,windowComment,objectType,objectComment)=cursor.fetchone()
        sql = """\
        select count(1)
        from pl_object_def
        where app_skey = %(app_skey)s and
        node_skey = %(node_skey)s
        """
        params = {'app_skey': appSkey, 'node_skey': nodeSkey}
        cursor.execute(sql,params)
        (number_of_rows,)=cursor.fetchone()
        if number_of_rows==0:
            objectSkey = getNextSequenceMSSQL('pl_object_def','object_skey','object_skey')
            sql = """\
            insert into pl_object_def
            (object_skey,node_skey,object_type,object_comment,app_skey,object_name,access_ind,create_user_id,create_date,maint_user_id,maint_date)
            values(%(object_skey)s,%(node_skey)s,%(object_type)s,%(object_comment)s,%(app_skey)s,%(object_name)s,0,SUSER_NAME(),getdate(),SUSER_NAME(),getdate())
            """
            params = {'object_skey': objectSkey,'node_skey': nodeSkey,'object_type': objectType,'object_comment': objectComment,'app_skey': appSkey,'object_name':nodeName if objectType == 'wp' else windowComment}
            cursor.execute(sql,params)
            conn.commit()

        sql = """\
        select *
        from pl_object_def
        where app_skey = %(app_skey)s and
        node_skey = %(node_skey)s
        """
        params = {'app_skey': appSkey, 'node_skey': nodeSkey}
        number_of_rows = cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        conn.commit()
        cursor.close()
        displayColumns = ['isSuccess','data']
        displayData = [(isSuccess,toJson(data,columns))]

        return jsonify(toJsonOne(displayData,displayColumns))

@nav_window_sercurity_mssql.route("/navigation/updateNodeObjectMSSQL", methods=['POST'])
def updateNodeObjectMSSQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['object_skey','access_ind']
    paramCheckStringList = []

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    objectSkey = dataInput['object_skey']
    accessInd = dataInput['access_ind']

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = """\
    select count(1)
    from pl_object_def
    where object_skey = %(object_skey)s
    """
    params = {'object_skey': objectSkey}
    cursor.execute(sql,params)
    (number_of_rows,)=cursor.fetchone()
    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Object Skey " + str(objectSkey)

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update pl_object_def
    set access_ind = %(access_ind)s
    where object_skey = %(object_skey)s
    """
    params = {'object_skey': objectSkey, 'access_ind': accessInd}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'Update Access Object เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))
