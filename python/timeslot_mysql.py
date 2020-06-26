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

timeslot_mysql = Blueprint('timeslot_mysql', __name__)

@timeslot_mysql.route("/timeslot/getDateTimeSlotMasterMySQL", methods=['POST'])
def getDateTimeSlotMaster ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    StartDate = dataInput['StartDate']
    EndDate = dataInput['EndDate']
    print(StartDate, '************************StartDate ')
    print(EndDate, '************************StartDate ')
    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select T.date
    from TimeSlot T
    where T.date >= %(StartDate)s and T.date <= %(EndDate)s
    group by T.date
    order by T.date,T.FromTime
    """
    params = {'StartDate': StartDate, 'EndDate': EndDate}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    print(data, '=================data')
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@timeslot_mysql.route("/timeslot/getTimeSlotMasterMySQL", methods=['POST'])
def getTimeSlotMaster ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    dateTimeSlot = dataInput['dateTimeSlot']
    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select T.date, CAST(T.FromTime as CHAR(5)) as FromTime, CAST(T.ToTime as CHAR(5)) as ToTime
    from TimeSlot T
    where T.date = %(dateTimeSlot)s
    order by T.date,T.FromTime
    """
    params = {'dateTimeSlot': dateTimeSlot}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    print(data, '=================data')
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))
