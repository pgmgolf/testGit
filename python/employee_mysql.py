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

employee_mysql = Blueprint('employee_mysql', __name__)

@employee_mysql.route("/employee/retrieveEmployeeMySQL", methods=['POST'])
def retrieveEmployeeMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select CONCAT(COALESCE(p.first_name,''),' ',COALESCE(p.middle_name,''),' ',COALESCE(p.last_name,'')) AS fullName,
    p.user_skey, p.user_id,p.first_name, p.middle_name, p.last_name,p.employee_no,p.email,user_password as password,p.profile_skey as profile,pro.profile_name,
    p.facility_cd, p.facility_cd as facility,
    active_flag,(CASE active_flag WHEN 'Y' THEN 'Active' WHEN 'N' THEN 'Inactive' WHEN 'P' THEN 'Pending' WHEN 'W' THEN 'Wait Change Password' END) as activeFlagDesc,
    a.dept,lis_iphysician_department.description as department,a.pay_code,
    a.date_hired, DATE_FORMAT(date_hired,'%d/%m/%Y') as dateHiredString,
    a.shift,a.status_code,a.hourly_rate,a.date_reviewed,a.vacation_hours,a.address_skey,
    address.street_1,address.street_2,address.street_3,address.street_4,address.city,
    address.state,r_state_province.name as provinceDesc,
    address.country_skey, r_country.description as countryDesc,
    address.zip_postal_code,
    address.local_phone as phone,
    address.email,
    to_base64(p.picture) as picture_base64
    from pc_user_def p
    left join pc_profile_def pro on p.profile_skey = pro.profile_skey
    inner join employee a on p.employee_no = a.employee_no
    left join address on a.address_skey = address.address_skey
    left join r_state_province on address.state = r_state_province.state_province_skey
    left join r_country on address.country_skey = r_country.country_skey
    left join lis_iphysician_department on a.dept = lis_iphysician_department.code
    """
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@employee_mysql.route("/employee/retrieveEmployeeCriteriaMySQL", methods=['POST'])
def retrieveEmployeeCriteriaMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    profile = dataInput['profile']
    Status = dataInput['Status']

    if not profile:
        profile = '%'

    if not Status:
        Status = '%'
    else:
        Status = Status + '%'

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select CONCAT(COALESCE(p.first_name,''),' ',COALESCE(p.middle_name,''),' ',COALESCE(p.last_name,'')) AS fullName,
    p.user_skey, p.user_id,p.first_name, p.middle_name, p.last_name,p.employee_no,p.email,user_password,p.profile_skey as profile,pro.profile_name,
    p.facility_cd, p.facility_cd as facility,
    active_flag,(CASE active_flag WHEN 'Y' THEN 'Active' WHEN 'N' THEN 'Inactive' WHEN 'P' THEN 'Pending' WHEN 'W' THEN 'Wait Change Password' END) as activeFlagDesc,
    a.dept,lis_iphysician_department.description as department,a.pay_code,
    a.date_hired, DATE_FORMAT(date_hired,'%%d/%%m/%%Y') as dateHiredString,
    a.shift,a.status_code,a.hourly_rate,a.date_reviewed,a.vacation_hours,a.address_skey,
    address.street_1,address.street_2,address.street_3,address.street_4,address.city,
    address.state,r_state_province.name as provinceDesc,
    address.country_skey, r_country.description as countryDesc,
    address.zip_postal_code,
    address.local_phone as phone,
    address.email,
    to_base64(p.picture) as picture_base64
    from pc_user_def p
    left join pc_profile_def pro on p.profile_skey = pro.profile_skey
    inner join employee a on p.employee_no = a.employee_no
    left join address on a.address_skey = address.address_skey
    left join r_state_province on address.state = r_state_province.state_province_skey
    left join r_country on address.country_skey = r_country.country_skey
    left join lis_iphysician_department on a.dept = lis_iphysician_department.code
    where 1=1 and (p.profile_skey like %(profile)s and IFNULL(p.active_flag, '') like %(Status)s)
    """
    params = {'Status': Status, 'profile': profile}
    print('=================================================================')
    print(sql, 'sql ')
    print(params, 'params ')
    print('=================================================================')
    cursor.execute(sql,params)

    print('////////////////////////////////////////////////////////////////')
    # params = {'Status': Status}
    # where employee.status = %(Status)s
    # cursor.execute(sql,params)
    # cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@employee_mysql.route("/employee/getProfileMySQL", methods=['POST'])
def getProfile ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from pc_profile_def"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@employee_mysql.route("/employee/getFacilityMySQL", methods=['POST'])
def getFacility ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select facility_cd, facility_name from facility"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@employee_mysql.route("/employee/addEmployeeMySQL", methods=['POST'])
def addEmployeeMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['user_id','password','firstname','lastname']
    paramCheckStringList = ['user_id','password','firstname','lastname']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    userID = dataInput['user_id']
    password = dataInput['password']
    employeeNo = dataInput['employeeNo']
    firstname = dataInput['firstname']
    middlename = dataInput['middlename']
    lastname = dataInput['lastname']
    activeFlag = dataInput['activeFlag']
    street_1 = dataInput['street_1']
    street_2 = dataInput['street_2']
    city = dataInput['city']
    state = dataInput['state']
    country_skey = dataInput['country_skey']
    zip_postal_code = dataInput['zip_postal_code']
    phone = dataInput['phone']
    profile = dataInput['profile']
    facility = dataInput['facility']
    email = dataInput['email']
    employeeNo = userID
    imageUrl = dataInput['imageUrl']
    imageUrlEncode = imageUrl[23:]
    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from pc_user_def where user_id like %s"
    cursor.execute(sql,userID)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "User ID already " + userID

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    if state=='':
        state = 0

    userSkey = getNextSequenceMySQL('pc_user_def','pc_user_def','user_skey')
    address_skey = getNextSequenceMySQL('address','address','address_skey')
    sql = """\
    insert into pc_user_def
    (user_skey,user_id,first_name,last_name,user_password,picture,
    middle_name,employee_no,profile_skey,active_flag,email,facility_cd)
    values(%(user_skey)s,%(user_id)s,%(firstname)s,%(lastname)s,%(user_password)s,FROM_BASE64(%(imageUrlEncode)s),
    %(middlename)s,%(employeeNo)s,%(profile)s,%(activeFlag)s,%(email)s,%(facility)s)
    """
    params = {'user_skey': userSkey,'user_id': userID,'user_password': Encrypt(password),
    'firstname': firstname,'lastname': lastname, 'imageUrlEncode': imageUrlEncode,
    'middlename': middlename,
    'employeeNo': employeeNo,
    'profile': profile,
    'facility': facility,
    'activeFlag': activeFlag,
    'email': email}
    cursor.execute(sql,params)
    sql = """\
    INSERT INTO employee
    (employee_no, dept, pay_code, date_hired, shift, status_code, hourly_rate, date_reviewed, vacation_hours,
    vac_hours_used, ss_no, holiday_hours, hol_hours_used, emp_img, address_skey,
    first_name, middle_name, last_name, primary_email_address)
    values(%(employeeNo)s,'000','A',NOW(),'1','A',1,NOW(),1,
    1, '1', 1, 1,FROM_BASE64(%(imageUrlEncode)s),%(address_skey)s,
    %(firstname)s,%(middlename)s,%(lastname)s,%(email)s)
    """
    params = {'employeeNo': employeeNo,
    'imageUrlEncode': imageUrlEncode,'address_skey': address_skey,
    'firstname': firstname,'middlename': middlename,'lastname': lastname,
    'email': email}
    cursor.execute(sql,params)
    sql = """\
    insert into address
    (address_skey, addr_type, street_1, street_2,
    city, state, zip_postal_code, country_skey,
    added_dt, last_actv_dt, edi_shipto_id, name,local_phone,email)
    values(%(address_skey)s,'PT',%(street_1)s,%(street_2)s,
    %(city)s,%(state)s,%(zip_postal_code)s,%(country_skey)s,
    NOW(),NOW(),'','',%(local_phone)s,%(email)s)
    """
    params = {'address_skey': address_skey,'street_1': street_1,'street_2': street_2,
    'city': city, 'state': state, 'zip_postal_code': zip_postal_code, 'country_skey': country_skey,
    'local_phone': phone, 'email': email}
    cursor.execute(sql,params)

    if profile == "physician":
        sql = "select count(1) from patho_physician where employee_no like %s and physician_no like %s"
        cursor.execute(sql,employeeNo)
        (number_of_rows,)=cursor.fetchone()
        if number_of_rows<0:
            sql = """\
            INSERT INTO patho_physician
            (physician_no, employee_no)
            values(%(employeeNo)s,%(employeeNo)s)
            """
            params = {'employeeNo': employeeNo}
            cursor.execute(sql,params)



    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้าง Employee เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@employee_mysql.route("/employee/updateEmployeeMySQL", methods=['POST'])
def updateEmployeeMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['user_id']
    paramCheckStringList = ['user_id']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    userID = dataInput['user_id']
    password = dataInput['password']
    employeeNo = dataInput['employeeNo']
    firstname = dataInput['firstname']
    middlename = dataInput['middlename']
    lastname = dataInput['lastname']
    activeFlag = dataInput['activeFlag']
    street_1 = dataInput['street_1']
    street_2 = dataInput['street_2']
    city = dataInput['city']
    state = dataInput['state']
    country_skey = dataInput['country_skey']
    zip_postal_code = dataInput['zip_postal_code']
    phone = dataInput['phone']
    profile = dataInput['profile']
    facility = dataInput['facility']
    email = dataInput['email']
    employeeNo = userID
    imageUrl = dataInput['imageUrl']
    imageUrlEncode = imageUrl[23:]
    print(middlename, 'sdfsf')
    if state=='':
        state = 0

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from pc_user_def where user_id like %s"
    cursor.execute(sql,userID)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid User " + userID

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))
# middle_name = %(middlename),
# last_name = %(lastname)s,
# picture=FROM_BASE64(%(imageUrlEncode)s),
# user_password = %(user_password)s,
# profile_skey=%(profile)s,
# active_flag = %(activeFlag)s,
# email = %(email)s
    sql = """\
    update pc_user_def
    set
    first_name = %(firstname)s,
    last_name = %(lastname)s,
    middle_name = %(middlename)s,
    picture=FROM_BASE64(%(imageUrlEncode)s),
    user_password = %(user_password)s,
    profile_skey=%(profile)s,
    facility_cd=%(facility)s,
    active_flag = %(activeFlag)s,
    email = %(email)s
    where user_id = %(userID)s
    """
    params = {'userID': userID,
    'firstname': firstname,
    'lastname': lastname,
    'middlename': middlename,
    'imageUrlEncode': imageUrlEncode,
    'user_password': Encrypt(password),
    'profile': profile,
    'facility': facility,
    'activeFlag': activeFlag,
    'email': email}
    cursor.execute(sql,params)

    sql = """\
    update employee b
    inner join address a on a.address_skey = b.address_skey
    inner join pc_user_def c on b.employee_no = c.employee_no
    set b.primary_email_address = %(email)s, b.first_name = %(firstname)s, b.middle_name = %(middlename)s, b.last_name = %(lastname)s,
    emp_img = FROM_BASE64(%(imageUrlEncode)s)
    where c.user_id = %(userID)s
    """
    params = {'userID': userID,
    'imageUrlEncode': imageUrlEncode,
    'firstname': firstname,'middlename': middlename,'lastname': lastname,
    'email': email}
    cursor.execute(sql,params)

    sql = """\
    update address a
    inner join employee b on a.address_skey = b.address_skey
    inner join pc_user_def c on b.employee_no = c.employee_no
    set a.email = %(email)s, street_1 = %(street_1)s, street_2 = %(street_2)s, city = %(city)s, state = %(state)s, zip_postal_code = %(zip_postal_code)s,
    local_phone = %(local_phone)s,
    country_skey = %(country_skey)s,last_actv_dt = NOW()
    where c.user_id = %(userID)s
    """
    params = {'userID': userID,'employeeNo': employeeNo,'street_1': street_1,'street_2': street_2,'city': city,'state': state,
    'zip_postal_code': zip_postal_code,'country_skey': country_skey,'local_phone': phone, 'email': email}
    cursor.execute(sql,params)
    if profile == 10:
        sql = "select count(1) from patho_physician where employee_no like %s"
        cursor.execute(sql,employeeNo)
        (number_of_rows,)=cursor.fetchone()
        if number_of_rows == 0:
            sql = """\
            INSERT INTO patho_physician
            (physician_no, employee_no)
            values(%(physician_no)s,%(employeeNo)s)
            """
            params = {'physician_no': employeeNo, 'employeeNo': employeeNo}
            cursor.execute(sql,params)
    else:
        print( 'else =================== profile')
        sql = """\
        delete patho_physician
        from patho_physician
        where physician_no = %(employeeNo)s
        """
        params = {'employeeNo': employeeNo}
        cursor.execute(sql,params)

    conn.commit()
    cursor.close()
    conn.close()

    # print(session['message'])

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลพนักงานเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@employee_mysql.route("/employee/deleteEmployeeMySQL", methods=['POST'])
def deleteEmployeeMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['user_id']
    paramCheckStringList = ['user_id']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    user_id = dataInput['user_id']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from pc_user_def where user_id like %s"
    cursor.execute(sql,user_id)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid User " + patient_skey

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete address
    from address
    inner join employee b on address.address_skey = b.address_skey
    inner join pc_user_def c on b.employee_no = c.employee_no
    where c.user_id = %(user_id)s
    """
    params = {'user_id': user_id}
    cursor.execute(sql,params)
    sql = """\
    delete patho_physician
    from patho_physician
    inner join pc_user_def c on patho_physician.employee_no = c.employee_no
    where c.user_id = %(user_id)s
    """
    params = {'user_id': user_id}
    cursor.execute(sql,params)
    sql = """\
    delete employee
    from employee
    inner join pc_user_def c on employee.employee_no = c.employee_no
    where c.user_id = %(user_id)s
    """
    params = {'user_id': user_id}
    cursor.execute(sql,params)
    sql = """\
    delete from pc_user_def
    where user_id = %(user_id)s
    """
    params = {'user_id': user_id}
    cursor.execute(sql,params)

    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลพนักงานเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@employee_mysql.route("/patient/updateEmployeeStatusMySQL", methods=['POST'])
def updateEmployeeStatusPlanMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['user_id']
    paramCheckStringList = ['user_id']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    user_id = dataInput['user_id']
    active_flag = dataInput['active_flag']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from pc_user_def where user_id like %s"
    cursor.execute(sql,user_id)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid User " + user_id

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update pc_user_def set active_flag =  %(active_flag)s
    where user_id = %(user_id)s
    """
    params = {'user_id': user_id,'active_flag': active_flag}
    cursor.execute(sql,params)

    conn.commit()
    cursor.close()
    conn.close()

    # print(session['message'])
    if active_flag == "Y":
        statusDesc = "Active"
    elif active_flag == "N":
        statusDesc = "Inactive"
    elif active_flag == "P":
        statusDesc = "Pending"
    elif active_flag == "W":
        statusDesc = "Wait"

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขสถานะเป็น : ' + statusDesc)]

    return jsonify(toJsonOne(displayData,displayColumns))
