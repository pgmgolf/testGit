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

episode_attachment_mysql = Blueprint('episode_attachment_mysql', __name__)

@episode_attachment_mysql.route("/episodeAttachment/insertOrUpdateEpisodeAttachmentMySQL", methods=['POST'])
def insertOrUpdateEpisodeAttachmentMySQL():
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

        returnDataColumns = ['ep_att_skey','ep_skey']
        returnData = [(episodeAttachSkey,episodeSkey)]

        displayColumns = ['isSuccess','reasonCode','reasonText','data']
        displayData = [(isSuccess,reasonCode,'บันทึกวินิจฉัยเรียบร้อย',toJsonOne(returnData,returnDataColumns))]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@episode_attachment_mysql.route("/episodeAttachment/deleteEpisodeAttachmentMySQL", methods=['POST'])
def deleteEpisodeAttachmentMySQL():
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
