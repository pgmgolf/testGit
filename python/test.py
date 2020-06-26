from flask import Flask, session, redirect, url_for
from flask import Flask, request, jsonify, current_app, abort, send_from_directory, send_file
from flask_cors import CORS, cross_origin
from flask import Blueprint
from flaskext.mysql import MySQL
from pymongo import MongoClient
import json
from bson import BSON
from bson import json_util
import os
import pymssql
import datetime
import re
import random
import math
import base64
import codecs
import pythoncom
import comtypes.client
# import win32com.client
# from comtypes.client import CreateObject
from flask import Flask, request, make_response
from pyreportjasper import JasperPy
from openpyxl import load_workbook
from werkzeug import secure_filename

from db_config import *
from common import *
test = Blueprint('test', __name__)

@test.route("/test/getResource", methods=['GET'])
def getResource():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = "select top 10 resource_no,description from resource"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.close()

    print(columns)
    print(data)

    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@test.route("/test/procUserTable", methods=['POST'])
def procUserTable():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()

    data = []
    specimenTestItem = {}

    specimenTestItem['order_skey'] = 8
    specimenTestItem['specimen_type_id'] = 'AAA'
    specimenTestItem['routing_seq'] = '10'
    specimenTestItem['status'] = 'CO'
    specimenTestItem['reason'] = 'resaon'
    specimenTestItem['remark'] = 'remark'
    data.append(specimenTestItem)

    print(data)

    sql = """\
    EXEC sp_test_user_table @tb_lab_specimen_test_item = %(tb_lab_specimen_test_item)s;
    """
    params = {'tb_lab_specimen_test_item': data}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    cursor.close()

    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]
    return jsonify(toJsonOne(displayData,displayColumns))


@test.route("/test/file", methods=['POST'])
def file():
    filename_tmp = ''
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))
    return ''

@test.route("/test/testString", methods=['POST'])
def testString():
    dataInput = request.json
    str1 = dataInput['str1']
    print(str1)
    return ''

@test.route("/test/getReportBase64", methods=['POST'])
def getReportBase64():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    try:
        with open(os.path.dirname(os.path.abspath(__file__)) + '/output/test_item.pdf', "rb") as f:
            encoded_string = base64.b64encode(f.read())

        displayColumns = ['isSuccess','reasonCode','reasonText','pdf_base64']
        displayData = [(isSuccess,reasonCode,reasonText,encoded_string)]

        return jsonify(toJsonOne(displayData,displayColumns))
    except IOError:
      return make_response("<h1>403 Forbidden</h1>", 403)

@test.route("/test/getReportArrayBuffer", methods=['POST'])
def getReportArrayBuffer():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    try:
      with open(os.path.dirname(os.path.abspath(__file__)) + '/output/sample.pdf', "rb") as f:
        content = f.read()
      response = make_response(content)
      response.headers['Content-Type'] = 'application/pdf; charset=utf-8'
      response.headers['Content-Disposition'] = 'attachment; filename=hello_world.pdf'
      return response

      # return send_file(os.path.dirname(os.path.abspath(__file__)) + '/output/test_item.pdf', mimetype='application/pdf')
    except IOError:
        return make_response("<h1>403 Forbidden</h1>", 403)

@test.route("/test/ppttoPDF", methods=['POST'])
def PPTtoPDF():
    try:
        isSuccess = True
        reasonCode = 500
        reasonText = ""
        now = datetime.datetime.now()
        datetimeStr = now.strftime('%Y%m%d_%H%M%S%f')
        filename_tmp = ''
        filename_out = ''
        if request.method == 'POST':
            f = request.files['file']
            filename_tmp = os.path.join(GetPathFlask(),'temp',secure_filename('{}_{}'.format(datetimeStr, f.filename)))
            filename_out = os.path.join(GetPathFlask(),'temp',secure_filename('{}_{}'.format(datetimeStr, 'out.pdf')))
            f.save(filename_tmp)
        else:
            reasonText = 'Invalid request file'
            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJsonOne(errData,errColumns))

        pythoncom.CoInitialize()

        powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
        # powerpoint = win32com.client.Dispatch('Powerpoint.Application')
        # powerpoint = CreateObject("Powerpoint.Application")
        powerpoint.Visible = 1

        deck = powerpoint.Presentations.Open(filename_tmp)
        deck.SaveAs(filename_out, 32) # formatType = 32 for ppt to pdf
        powerpoint.Quit()

        with open(filename_out, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())

        # encoded_string = 'fasdf'

        displayColumns = ['isSuccess','reasonCode','reasonText','pdf_base64']
        displayData = [(isSuccess,reasonCode,reasonText,encoded_string)]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
    finally:
        print('aa')
        # os.remove(filename_tmp)
        # os.remove(filename_out)
