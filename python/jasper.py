# -*- coding: utf-8 -*-

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
import jwt
import codecs
from flask import Flask, request, make_response
from pyreportjasper import JasperPy

from db_config import *
from common import *
jasper = Blueprint('jasper', __name__)

@jasper.route("/getReportDatabaseMSSQL", methods=['POST'])
def getReportDatabase():
    try:
        now = datetime.datetime.now()
        datetimeStr = now.strftime('%Y%m%d_%H%M%S%f')

        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['report_name',"param"]
        paramCheckStringList = ['report_name']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        reportName = dataInput['report_name']
        param = dataInput['param']

        input_file = '{}/report/{}.jrxml'.format(os.path.dirname(os.path.abspath(__file__)), reportName)
        compile_file = '{}/report/{}.jasper'.format(os.path.dirname(os.path.abspath(__file__)), reportName)
        output_file = '{}/output/{}'.format(os.path.dirname(os.path.abspath(__file__)), datetimeStr)
        resource_file = '{}/font/THSarabunPSK.jar'.format(os.path.dirname(os.path.abspath(__file__)))

        con = {
            'driver' : 'generic',
            'jdbc_driver': 'com.microsoft.sqlserver.jdbc.SQLServerDriver',
            'jdbc_url' : 'jdbc:sqlserver://{};databaseName={}'.format(mssql_server, mssql_database),
            'username': mssql_user,
            'password': mssql_password
        }

        jasper = JasperPy()
        jasper.process(
            compile_file,
            output_file=output_file,
            format_list=["pdf"],
            parameters=param,
            db_connection=con,
            locale='en_US',
            resource=resource_file
        )

        with open(output_file + '.pdf', "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())

        os.remove(output_file + '.pdf')
        errColumns = ['isSuccess','reasonCode','reasonText','pdf_base64']
        errData = [(isSuccess,reasonCode,reasonText,encoded_string)]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@jasper.route("/getReportByJSONBase64", methods=['POST'])
def getReportByJSONBase64():
    try:
        now = datetime.datetime.now()
        datetimeStr = now.strftime('%Y%m%d_%H%M%S%f')

        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['report_name','data_json']
        paramCheckStringList = ['report_name','data_json']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        dataJson = dataInput['data_json']
        reportName = dataInput['report_name']

        input_file = '{}/report/{}.jrxml'.format(os.path.dirname(os.path.abspath(__file__)), reportName)
        compile_file = '{}/report/{}.jasper'.format(os.path.dirname(os.path.abspath(__file__)), reportName)
        output_file = '{}/output/{}'.format(os.path.dirname(os.path.abspath(__file__)), datetimeStr)
        data_file = '{}/data/data_tmp{}.json'.format(os.path.dirname(os.path.abspath(__file__)), datetimeStr)
        resource_file = '{}/font/THSarabunPSK.jar'.format(os.path.dirname(os.path.abspath(__file__)))

        file = codecs.open(data_file,"w","utf-8")
        file.write(json.dumps(dataJson[0]))
        # file.write(str(dataJson))
        file.close()
        con = {
            'data_file': data_file,
            'driver': 'json',
            'json_query': 'data',
        }

        jasper = JasperPy()
        # jasper.compile(input_file)
        jasper.process(
            compile_file,
            output_file=output_file,
            format_list=['pdf'],
            parameters={},
            db_connection=con,
            locale='en_US',
            resource=resource_file
        )

        with open(output_file + '.pdf', "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())

        os.remove(output_file + '.pdf')
        os.remove(data_file)
        errColumns = ['isSuccess','reasonCode','reasonText','pdf_base64']
        errData = [(isSuccess,reasonCode,reasonText,encoded_string)]

        return jsonify(toJsonOne(errData,errColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))
