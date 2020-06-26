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

episode_prescription_mysql = Blueprint('episode_prescription_mysql', __name__)

@episode_prescription_mysql.route("/episodePrescription/retrievePrescriptionMySQL", methods=['POST'])
def retrievePrescriptionMySQL():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select resource.resource_no,resource.description as resource_desc,
        COALESCE(tmp_uom_conv_selling.uom_selling,resource.uom) as uom_selling,COALESCE(tmp_uom_conv_selling.factor,1) as uom_factor,
        item_addition.price_1,item_addition.include_tax,item_addition.vat_rate
        from resource inner join procure_det on
        resource.resource_no = procure_det.resource_no left outer join item_addition on
        resource.resource_no = item_addition.resource_no inner join commodities on
        procure_det.commodity = commodities.commodity left outer join (select resource_no,uom_selling,factor from uom_conv_selling
        where default_uom = 1 limit 1) tmp_uom_conv_selling  on
		tmp_uom_conv_selling.resource_no = resource.resource_no
        where commodities.commodity = %(commodity)s
        """
        params = {'commodity': 'RX'}

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

@episode_prescription_mysql.route("/episodePrescription/insertOrUpdateEpisodePrescriptionMySQL", methods=['POST'])
def insertOrUpdateEpisodePrescriptionMySQL():
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
        paramList = ['resource_no','resource_desc','uom_selling','uom_factor','price','qty','vat_rate','include_tax']
        paramCheckStringList = ['resource_no','resource_desc','uom_selling']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        visitSkey = dataInput['visit_skey']
        episodeSkey = dataInput['ep_skey']
        resourceNo = dataInput['resource_no']
        resourceDesc = dataInput['resource_desc']
        uomSelling = dataInput['uom_selling']
        uomFactor = dataInput['uom_factor']
        price = dataInput['price']
        qty = dataInput['qty']
        vatRate = dataInput['vat_rate']
        includeTax = dataInput['include_tax']

        conn = mysql.connect()
        cursor = conn.cursor()
        sql = """\
        select count(1)
        from lis_visit inner join episode on
        lis_visit.visit_skey = episode.visit_skey inner join ep_prescription on
        episode.ep_skey = ep_prescription.ep_skey
        where lis_visit.visit_skey = %(visit_skey)s and
        episode.ep_skey like %(ep_skey)s and
        ep_prescription.resource_no like %(resource_no)s
        """
        params = {'visit_skey': visitSkey,'ep_skey' : episodeSkey,'resource_no' :resourceNo}
        cursor.execute(sql,params)

        (number_of_rows,)=cursor.fetchone()

        if number_of_rows==0:
            prescriptionSkey = getNextSequenceMySQL('ep_prescription','ep_prescription','ep_rx_skey')
            sql = """\
            insert into ep_prescription
            (ep_rx_skey,ep_skey,resource_no,resource_desc,uom_selling,uom_factor,price,qty,vat_rate,include_tax,date_created,user_created,date_changed,user_changed)
            values(%(ep_rx_skey)s,%(ep_skey)s,%(resource_no)s,%(resource_desc)s,%(uom_selling)s,%(uom_factor)s,%(price)s,%(qty)s,%(vat_rate)s,%(include_tax)s,now(),%(user_created)s,now(),%(user_changed)s)
            """
            params = {'ep_rx_skey': prescriptionSkey,'ep_skey': episodeSkey,'resource_no': resourceNo,'resource_desc': resourceDesc
            ,'uom_selling': uomSelling,'uom_factor': uomFactor,'price': price,'qty': qty,
            'vat_rate': vatRate,'include_tax':includeTax,'user_created': userID,'user_changed': userID}
            cursor.execute(sql,params)
            conn.commit()
        else:
            sql = """\
            update ep_prescription
            set resource_desc = %(resource_desc)s,
            resource_desc = %(resource_desc)s,
            uom_selling = %(uom_selling)s,
            uom_factor = %(uom_factor)s,
            price = %(price)s,
            qty = %(qty)s,
            vat_rate = %(vat_rate)s,
            include_tax = %(include_tax)s,
            user_changed = now(),
            user_changed = %(user_changed)s
            where ep_prescription.ep_skey like %(ep_skey)s and
            ep_prescription.resource_no like %(resource_no)s
            """
            params = {'ep_skey': episodeSkey,'resource_no': resourceNo,'resource_desc': resourceDesc
            ,'uom_selling': uomSelling,'uom_factor': uomFactor,'price': price,'qty': qty,
            'vat_rate': vatRate,'include_tax':includeTax,'user_created': userID,'user_changed': userID}
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

@episode_prescription_mysql.route("/episodePrescription/deleteEpisodePrescriptionMySQL", methods=['POST'])
def deleteEpisodePrescriptionMySQL():
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
        paramList = ['resource_no','resource_desc','uom_selling','uom_factor','price','qty','vat_rate','include_tax']
        paramCheckStringList = ['resource_no','resource_desc','uom_selling']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        visitSkey = dataInput['visit_skey']
        episodeSkey = dataInput['ep_skey']
        resourceNo = dataInput['resource_no']
        resourceDesc = dataInput['resource_desc']
        uomSelling = dataInput['uom_selling']
        uomFactor = dataInput['uom_factor']
        price = dataInput['price']
        qty = dataInput['qty']
        vatRate = dataInput['vat_rate']
        includeTax = dataInput['include_tax']

        conn = mysql.connect()
        cursor = conn.cursor()

        sql = """\
        delete from ep_prescription
        where ep_prescription.ep_skey like %(ep_skey)s and
        ep_prescription.resource_no like %(resource_no)s
        """
        params = {'ep_skey': episodeSkey,'resource_no': resourceNo,'resource_desc': resourceDesc
        ,'uom_selling': uomSelling,'uom_factor': uomFactor,'price': price,'qty': qty,
        'vat_rate': vatRate,'include_tax':includeTax,'user_created': userID,'user_changed': userID}
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
