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

patient_mysql = Blueprint('patient_mysql', __name__)

@patient_mysql.route("/patient/retrievePatientMySQL", methods=['POST'])
def retrievePatientMySQL():

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
    select patient.patient_skey, patient_id, patient.prefix, patho_prefix.prefix_desc, patient.firstname, patient.middle_name, patient.lastname, sex.sex_desc as sex, sex.sex_cd as sexCode, DATE_FORMAT(birthday,'%Y-%m-%d') as birthday,
    TRUNCATE((DATEDIFF(CURRENT_DATE, DATE_FORMAT(birthday,'%Y-%m-%d'))/365),0) AS ageInYears,
    (CASE status WHEN 'OP' THEN 'OPEN' WHEN 'CA' THEN 'CANCEL' END) as statusDesc,
     hn, status, id_card, passport_id,to_base64(picture) as picture, primary_affiliation, secondary_affiliation, officer_id1, officer_id2, employer, employer_type_cd,
    register_unit, employer_cid, relationship_cd, payment_type_cd,
    blood_rh_cd, blood_abo_cd, graduate_cd, religion_cd, date_created as dateCreated, user_created, date_changed, user_changed, nationality, race, age_tmp, note, ignore_birthday,
    firstname_sound, lastname_sound, position, branch, department, employee_no,
    CONCAT(COALESCE(patho_prefix.prefix_desc,''),' ',COALESCE(patient.firstname,''),' ',COALESCE(patient.middle_name,''),' ',COALESCE(patient.lastname,'')) AS fullName,
    COALESCE(patient.id_card,patient.passport_id) AS id,
    patient.email, race, nationality, patient.note,
    payment_plan_cd as paymentPlan, lis_payment_plan.description as paymentPlanDesc,
    religion_cd, lis_religion.description as religionDesc,
    graduate_cd, lis_graduate.description as graduateDesc,
    blood_abo_cd, lis_blood_abo.description as bloodAboDesc,
    blood_rh_cd, lis_blood_rh.description as bloodRhDesc,
    occupation_cd, lis_occupation.description as occupationDesc, allergy, disease,
    relationship_cd, lis_relationship_status.description as relationshipDesc,to_base64(picture) as picture_base64, anonymous_name, anonymous_flag,
    address.street_1,address.street_2,address.street_3,address.street_4,address.city,
    address.state,r_state_province.name as provinceDesc,
    address.country_skey, r_country.description as countryDesc,
    address.zip_postal_code, patient.phone,
    patient_relation.patient_relation_skey,
    patient_relation.prefix as prefixRelation,  prefix_relation.prefix_desc as PrefixDescRelation,
    patient_relation.firstname as firstNameRelation, patient_relation.middle_name as middleNameRelation, patient_relation.lastname as LastNameRelation,
    patient_relation.sex as sexRelation , sex_relation.sex_desc as sexDescRelation,
    patient_relation.relation_cd, relation.description as relationDesc,
    addressRelation.street_1 as street1Relation,addressRelation.street_2 as street2Relation,
    addressRelation.city as cityRelation,addressRelation.state as stateRelation,
    addressRelation.country_skey as CountryRelation,addressRelation.zip_postal_code as zipCodeRelation,addressRelation.local_phone as localPhoneRelation,
    r_state_provinceRelation.name as provinceRelationDesc,r_countryRelation.description as countryRelationDesc,
    (select count(1) from lis_visit vv where vv.patient_skey = patient.patient_skey
    and vv.status = 'PE') as appointmentCount
    from lis_patient as patient
    inner join patho_prefix on patho_prefix.prefix_cd = patient.prefix
    inner join patho_sex as sex on sex.sex_cd = patient.sex
    left join lis_patient_address on lis_patient_address.patient_skey = patient.patient_skey
    left join address on lis_patient_address.address_skey = address.address_skey
    left join r_state_province on address.state = r_state_province.state_province_skey
    left join r_country on address.country_skey = r_country.country_skey
    left join lis_religion on patient.religion_cd = lis_religion.code
    left join lis_graduate on patient.graduate_cd = lis_graduate.code
    left join lis_blood_abo on patient.blood_abo_cd = lis_blood_abo.code
    left join lis_blood_rh on patient.blood_rh_cd = lis_blood_rh.code
    left join lis_occupation on patient.occupation_cd = lis_occupation.code
    left join lis_relationship_status on patient.relationship_cd = lis_relationship_status.code
    left join lis_patient_relation as patient_relation on patient.patient_skey = patient_relation.patient_skey
    left join patho_prefix prefix_relation on patient_relation.prefix = prefix_relation.prefix_cd
    left join patho_sex as sex_relation on patient_relation.sex = sex_relation.sex_cd
    left join relation on patient_relation.relation_cd = relation.code
    left join address addressRelation on patient_relation.address_skey = addressRelation.address_skey
    left join lis_payment_plan on patient.payment_plan_cd = lis_payment_plan.code
    left join r_state_province as r_state_provinceRelation on addressRelation.state = r_state_provinceRelation.state_province_skey
    left join r_country as r_countryRelation on addressRelation.country_skey = r_countryRelation.country_skey
    order by patient.patient_skey
    """
    cursor.execute(sql)
# and date_arrived > now()) as appointmentCount
    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]
    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrievePatientCriteriaMySQL", methods=['POST'])
def retrievePatientCriteriaMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    patientId = dataInput['patientId']
    hn = dataInput['hn']
    idcard = dataInput['idcard']
    Status = dataInput['Status']

    if not hn:
        hn = '%'
    else:
        hn = hn + '%'
    if not Status:
        Status = '%'
    else:
        Status = Status + '%'
    if not idcard:
        idcard = '%'
    else:
        idcard = idcard + '%'
    if not patientId:
        patientId = '%'

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    select patient.patient_skey, patient_id, patient.prefix, patho_prefix.prefix_desc, patient.firstname, patient.middle_name, patient.lastname, sex.sex_desc as sex, sex.sex_cd as sexCode, DATE_FORMAT(birthday,'%%Y-%%m-%%d') as birthday,
    TRUNCATE((DATEDIFF(CURRENT_DATE, DATE_FORMAT(birthday,'%%Y-%%m-%%d'))/365),0) AS ageInYears,
    (CASE status WHEN 'OP' THEN 'OPEN' WHEN 'CA' THEN 'CANCEL' END) as statusDesc,
     hn, status, id_card, passport_id,to_base64(picture) as picture, primary_affiliation, secondary_affiliation, officer_id1, officer_id2, employer, employer_type_cd,
    register_unit, employer_cid, relationship_cd, payment_type_cd,
    blood_rh_cd, blood_abo_cd, graduate_cd, religion_cd, date_created as dateCreated, user_created, date_changed, user_changed, nationality, race, age_tmp, note, ignore_birthday,
    firstname_sound, lastname_sound, position, branch, department, employee_no,
    CONCAT(COALESCE(patho_prefix.prefix_desc,''),' ',COALESCE(patient.firstname,''),' ',COALESCE(patient.middle_name,''),' ',COALESCE(patient.lastname,'')) AS fullName,
    COALESCE(patient.id_card,patient.passport_id) AS id,
    patient.email, race, nationality, patient.note,
    payment_plan_cd as paymentPlan, lis_payment_plan.description as paymentPlanDesc,
    religion_cd, lis_religion.description as religionDesc,
    graduate_cd, lis_graduate.description as graduateDesc,
    blood_abo_cd, lis_blood_abo.description as bloodAboDesc,
    blood_rh_cd, lis_blood_rh.description as bloodRhDesc,
    occupation_cd, lis_occupation.description as occupationDesc, allergy, disease,
    relationship_cd, lis_relationship_status.description as relationshipDesc,to_base64(picture) as picture_base64, anonymous_name, anonymous_flag,
    address.street_1,address.street_2,address.street_3,address.street_4,address.city,
    address.state,r_state_province.name as provinceDesc,
    address.country_skey, r_country.description as countryDesc,
    address.zip_postal_code, patient.phone,
    patient_relation.patient_relation_skey,
    patient_relation.prefix as prefixRelation,  prefix_relation.prefix_desc as PrefixDescRelation,
    patient_relation.firstname as firstNameRelation, patient_relation.middle_name as middleNameRelation, patient_relation.lastname as LastNameRelation,
    patient_relation.sex as sexRelation , sex_relation.sex_desc as sexDescRelation,
    patient_relation.relation_cd, relation.description as relationDesc,
    addressRelation.street_1 as street1Relation,addressRelation.street_2 as street2Relation,
    addressRelation.city as cityRelation,addressRelation.state as stateRelation,
    addressRelation.country_skey as CountryRelation,addressRelation.zip_postal_code as zipCodeRelation,addressRelation.local_phone as localPhoneRelation,
    r_state_provinceRelation.name as provinceRelationDesc,r_countryRelation.description as countryRelationDesc,
    (select (case when count(1) = 0 then null else count(1) end) from lis_visit vv where vv.patient_skey = patient.patient_skey
    and vv.status = 'PE') as appointmentCount
    from lis_patient as patient
    inner join patho_prefix on patho_prefix.prefix_cd = patient.prefix
    inner join patho_sex as sex on sex.sex_cd = patient.sex
    left join lis_patient_address on lis_patient_address.patient_skey = patient.patient_skey
    left join address on lis_patient_address.address_skey = address.address_skey
    left join r_state_province on address.state = r_state_province.state_province_skey
    left join r_country on address.country_skey = r_country.country_skey
    left join lis_religion on patient.religion_cd = lis_religion.code
    left join lis_graduate on patient.graduate_cd = lis_graduate.code
    left join lis_blood_abo on patient.blood_abo_cd = lis_blood_abo.code
    left join lis_blood_rh on patient.blood_rh_cd = lis_blood_rh.code
    left join lis_occupation on patient.occupation_cd = lis_occupation.code
    left join lis_relationship_status on patient.relationship_cd = lis_relationship_status.code
    left join lis_patient_relation as patient_relation on patient.patient_skey = patient_relation.patient_skey
    left join patho_prefix prefix_relation on patient_relation.prefix = prefix_relation.prefix_cd
    left join patho_sex as sex_relation on patient_relation.sex = sex_relation.sex_cd
    left join relation on patient_relation.relation_cd = relation.code
    left join address addressRelation on patient_relation.address_skey = addressRelation.address_skey
    left join lis_payment_plan on patient.payment_plan_cd = lis_payment_plan.code
    left join r_state_province as r_state_provinceRelation on addressRelation.state = r_state_provinceRelation.state_province_skey
    left join r_country as r_countryRelation on addressRelation.country_skey = r_countryRelation.country_skey
    where 1=1 and (patient.status like %(Status)s and IFNULL(patient.hn, '') like %(hn)s) and
    (patient.id_card like %(idcard)s or patient.passport_id like %(idcard)s) and patient_id like %(patientId)s
    order by patient.patient_skey
    """
    params = {'Status': Status, 'hn': hn, 'idcard': idcard, 'patientId': patientId}
    cursor.execute(sql,params)


    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/getPrefixMySQL", methods=['POST'])
def getPrefix ():
    # returnUserToken = getUserToken(request.headers.get('Authorization'))
    # if not returnUserToken["isSuccess"]:
    #     return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from patho_prefix"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getPaymentPlanMySQL", methods=['POST'])
def getPaymentPlan ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_payment_plan"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getProvinceMySQL", methods=['POST'])
def getProvince ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    Country = dataInput['Country']
    conn = mysql.connect()
    cursor = conn.cursor()
    # sql = "select state_province_skey,name from r_state_province"
    # cursor.execute(sql)
    sql = "select state_province_skey,name from r_state_province where country_skey = %s order by name"
    cursor.execute(sql,Country)
    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getCountryMySQL", methods=['POST'])
def getCountry ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select country_skey,description from r_country"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getRelationMySQL", methods=['POST'])
def getRelation ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from relation"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getOccupationMySQL", methods=['POST'])
def getOccupation ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_occupation"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getReligionMySQL", methods=['POST'])
def getReligion ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_religion"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getGraduateMySQL", methods=['POST'])
def getGraduate ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_graduate"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getBloodAboMySQL", methods=['POST'])
def getBloodAbo ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_blood_abo"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getBloodRhMySQL", methods=['POST'])
def getBloodRh ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_blood_rh"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/getRelationshipStatusMySQL", methods=['POST'])
def getRelationshipStatus ():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_relationship_status"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@patient_mysql.route("/patient/addPatientMySQL", methods=['POST'])
def addPatientMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['prefix','firstname','lastname','sex','birthday','status']
    paramCheckStringList = ['prefix','firstname','lastname','sex','birthday','status']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    # payload = getUserToken(request.headers.get('Authorization'))
    # userID = payload['user_id']

    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    userID = returnUserToken["data"]["user_id"]

    patient_id = 0
    prefix = dataInput['prefix']
    firstname = dataInput['firstname']
    middle_name = dataInput['middle_name']
    lastname = dataInput['lastname']
    sex = dataInput['sex']
    birthday = dataInput['birthday']
    hn = dataInput['hn']
    status = dataInput['status']
    id_card = dataInput['id_card']
    passport_id = dataInput['passport_id']
    picture = dataInput['picture']
    paymentPlan = dataInput['paymentPlan']
    anonymousName = dataInput['anonymousName']
    anonymousFlag = dataInput['anonymousFlag']
    phone = dataInput['phone']
    email = dataInput['email']
    occupation_cd = dataInput['occupation_cd']
    blood_rh_cd = dataInput['bloodRh_cd']
    blood_abo_cd = dataInput['bloodAbo_cd']
    relationship_cd = dataInput['relationship_cd']
    graduate_cd = dataInput['graduate_cd']
    religion_cd = dataInput['religion_cd']
    allergy = dataInput['allergy']
    disease = dataInput['disease']
    nationality = dataInput['nationality']
    race = dataInput['race']
    note = dataInput['note']
    street_1 = dataInput['street_1']
    street_2 = dataInput['street_2']
    city = dataInput['city']
    state = dataInput['state']
    zip_postal_code = dataInput['zip_postal_code']
    country_skey = dataInput['country_skey']
    prefix_relation = dataInput['prefix_relation']
    first_name_relation = dataInput['first_name_relation']
    middle_name_relation = dataInput['middle_name_relation']
    Last_name_relation = dataInput['Last_name_relation']
    sex_relation = dataInput['sex_relation']
    relation_cd = dataInput['relation_cd']
    street1_relation = dataInput['street1_relation']
    street2_relation = dataInput['street2_relation']
    city_relation = dataInput['city_relation']
    state_relation = dataInput['state_relation']
    zipCode_relation = dataInput['zipCode_relation']
    Country_relation = dataInput['Country_relation']
    local_phone_relation = dataInput['local_phone_relation']
    imageUrl = dataInput['imageUrl']
    imageUrlEncode = imageUrl[23:]

    if state=='':
        state = 0

    if state_relation=='':
        state_relation = 0


    conn = mysql.connect()
    cursor = conn.cursor()

    sql = "select count(1) from lis_patient where id_card like %s"
    cursor.execute(sql,id_card),
    (number_of_rows,)=cursor.fetchone()

    if (number_of_rows>0) and (id_card):
        isSuccess = False
        reasonCode = 500
        reasonText = "Id Card ID already " + id_card

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]
        return jsonify(toJsonOne(errData,errColumns))


    patient_skey = getNextSequenceMySQL('lis_patient','lis_patient','patient_skey')
    patient_address_skey = getNextSequenceMySQL('lis_patient_address','lis_patient_address','patient_address_skey')
    address_skey = getNextSequenceMySQL('address','address','address_skey')
    patient_relation_skey = getNextSequenceMySQL('lis_patient_relation','lis_patient_relation','patient_relation_skey')
    # patient_id = patient_skey
    patient_id = getSequenceNumberMySQL('lis_patient','P',2018,1,1,'00000000','00','00','00','Y','N','N','','','-')
    print(patient_skey, '==>patient_skey')
    print(patient_address_skey, '==>patient_address_skey')
    print(address_skey, '==>address_skey')
    print(patient_relation_skey, '==>patient_relation_skey')
    print(patient_id, '==>patient_id')
    rank = 1
    sql = """\
    insert into lis_patient
    (patient_skey, patient_id, prefix, firstname, middle_name, lastname, sex,
    birthday, status, id_card, passport_id, payment_plan_cd, anonymous_name, anonymous_flag,
    hn, email, phone, relationship_cd,
    occupation_cd, blood_rh_cd, blood_abo_cd, graduate_cd, religion_cd,
    allergy, disease, nationality, race, note,
    date_created, user_created, date_changed, user_changed, picture)
    values(%(patient_skey)s, %(patient_id)s, %(prefix)s, %(firstname)s, %(middle_name)s, %(lastname)s, %(sex)s,
    %(birthday)s, %(status)s, %(id_card)s, %(passport_id)s, %(paymentPlan)s, %(anonymousName)s,%(anonymousFlag)s,
    %(hn)s, %(email)s, %(phone)s, %(relationship_cd)s,
    %(occupation_cd)s, %(blood_rh_cd)s, %(blood_abo_cd)s,%(graduate_cd)s, %(religion_cd)s,
    %(allergy)s, %(disease)s, %(nationality)s,%(race)s, %(note)s,
    NOW(), %(userID)s, NOW(), %(userID)s, FROM_BASE64(%(imageUrlEncode)s))
    """
    params = {'patient_skey': patient_skey,'patient_id': patient_id,'prefix': prefix,'firstname': firstname,'middle_name': middle_name,
    'lastname': lastname,'sex': sex,'birthday': birthday,'status': status,'id_card': id_card,'passport_id':passport_id,'paymentPlan': paymentPlan,
    'anonymousName': anonymousName, 'anonymousFlag': anonymousFlag,
    'hn': hn, 'phone': phone, 'email': email, 'relationship_cd': relationship_cd,
    'occupation_cd': occupation_cd, 'blood_rh_cd': blood_rh_cd, 'blood_abo_cd': blood_abo_cd, 'graduate_cd': graduate_cd, 'religion_cd': religion_cd,
    'allergy': allergy, 'disease': disease, 'nationality': nationality, 'race': race, 'note': note, 'imageUrlEncode': imageUrlEncode,
    'userID': userID}
    cursor.execute(sql,params)
    sql = """\
    insert into lis_patient_address
    (patient_skey,patient_address_skey,address_skey,rank)
    values(%(patient_skey)s,%(patient_address_skey)s,%(address_skey)s,%(rank)s)
    """
    params = {'patient_skey': patient_skey,'patient_address_skey': patient_address_skey,'address_skey': address_skey,'rank': rank}
    cursor.execute(sql,params)
    sql = """\
    insert into address
    (address_skey, addr_type, street_1, street_2,
    city, state, zip_postal_code, country_skey,
    added_dt, last_actv_dt, edi_shipto_id, name)
    values(%(address_skey)s,'PT',%(street_1)s,%(street_2)s,
    %(city)s,%(state)s,%(zip_postal_code)s,%(country_skey)s,
    NOW(),NOW(),'','')
    """
    params = {'address_skey': address_skey,'street_1': street_1,'street_2': street_2,
    'city': city, 'state': state, 'zip_postal_code': zip_postal_code, 'country_skey': country_skey}
    cursor.execute(sql,params)
# relation
    address_relation_skey = getNextSequenceMySQL('address','address','address_skey')
    print(address_relation_skey, '==>address_relation_skey')
    sql = """\
    insert into lis_patient_relation
    (patient_relation_skey, patient_skey, prefix, firstname, middle_name, lastname, sex, relation_cd, address_skey)
    values(%(patient_relation_skey)s,%(patient_skey)s,%(prefix)s,
    %(firstname)s,%(middle_name)s,%(lastname)s,%(sex)s,%(relation_cd)s,%(address_skey)s)
    """
    params = {'patient_relation_skey': patient_relation_skey, 'patient_skey': patient_skey,
    'prefix': prefix_relation,'firstname': first_name_relation,
    'middle_name': middle_name_relation, 'lastname': Last_name_relation, 'sex': sex_relation,
    'relation_cd': relation_cd, 'address_skey': address_relation_skey}
    cursor.execute(sql,params)
    sql = """\
    insert into address
    (address_skey, addr_type, street_1, street_2,
    city, state, zip_postal_code, country_skey, local_phone,
    added_dt, last_actv_dt, edi_shipto_id, name)
    values(%(address_skey)s,'PT',%(street_1)s,%(street_2)s,
    %(city)s,%(state)s,%(zip_postal_code)s,%(country_skey)s,%(local_phone)s,
    NOW(),NOW(),'','')
    """
    params = {'address_skey': address_relation_skey,'street_1': street1_relation,'street_2': street2_relation,
    'city': city_relation, 'state': state_relation, 'zip_postal_code': zipCode_relation, 'country_skey': Country_relation,
    'local_phone': local_phone_relation}
    cursor.execute(sql,params)
# relation
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้างข้อมูลคนไข้ เรียบร้อย')]
    # except KeyError, e:
    #     print 'I got a KeyError - reason "%s"' % str(e)
    # except:
    #     print 'I got another exception, but I should re-raise'
    # raise
    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/updatePatientMySQL", methods=['POST'])
def updatePatientPlanMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    # payload = getUserToken(request.headers.get('Authorization'))
    # userID = payload['user_id']

    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    userID = returnUserToken["data"]["user_id"]

    dataInput = request.json
    paramList = ['patient_skey']
    paramCheckStringList = ['patient_skey']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    patient_skey = dataInput['patient_skey']
    patient_id = dataInput['patient_id']
    prefix = dataInput['prefix']
    firstname = dataInput['firstname']
    middle_name = dataInput['middle_name']
    lastname = dataInput['lastname']
    sex = dataInput['sex']
    birthday = dataInput['birthday']
    hn = dataInput['hn']
    status = dataInput['status']
    id_card = dataInput['id_card']
    passport_id = dataInput['passport_id']
    picture = dataInput['picture']
    paymentPlan = dataInput['paymentPlan']
    anonymousName = dataInput['anonymousName']
    anonymousFlag = dataInput['anonymousFlag']
    phone = dataInput['phone']
    email = dataInput['email']
    occupation_cd = dataInput['occupation_cd']
    blood_rh_cd = dataInput['bloodRh_cd']
    blood_abo_cd = dataInput['bloodAbo_cd']
    relationship_cd = dataInput['relationship_cd']
    graduate_cd = dataInput['graduate_cd']
    religion_cd = dataInput['religion_cd']
    allergy = dataInput['allergy']
    disease = dataInput['disease']
    nationality = dataInput['nationality']
    race = dataInput['race']
    note = dataInput['note']
    street_1 = dataInput['street_1']
    street_2 = dataInput['street_2']
    city = dataInput['city']
    state = dataInput['state']
    zip_postal_code = dataInput['zip_postal_code']
    country_skey = dataInput['country_skey']
    prefix_relation = dataInput['prefix_relation']
    first_name_relation = dataInput['first_name_relation']
    middle_name_relation = dataInput['middle_name_relation']
    Last_name_relation = dataInput['Last_name_relation']
    sex_relation = dataInput['sex_relation']
    relation_cd = dataInput['relation_cd']
    street1_relation = dataInput['street1_relation']
    street2_relation = dataInput['street2_relation']
    city_relation = dataInput['city_relation']
    state_relation = dataInput['state_relation']
    zipCode_relation = dataInput['zipCode_relation']
    Country_relation = dataInput['Country_relation']
    local_phone_relation = dataInput['local_phone_relation']
    imageUrl = dataInput['imageUrl']
    imageUrlEncode = imageUrl[23:]
    if state=='':
        state = 0
    if state_relation=='':
        state_relation = 0

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_patient where patient_skey like %s"
    cursor.execute(sql,patient_skey)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Patient " + patient_skey

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_patient set prefix =  %(prefix)s, firstname =  %(firstname)s, middle_name =  %(middle_name)s, lastname =  %(lastname)s,
    sex =  %(sex)s, birthday =  %(birthday)s, status =  %(status)s, id_card =  %(id_card)s, passport_id =  %(passport_id)s,
    payment_plan_cd =  %(paymentPlan)s, anonymous_name =  %(anonymousName)s, anonymous_flag =  %(anonymousFlag)s,
    hn =  %(hn)s, email =  %(email)s, phone =  %(phone)s, relationship_cd =  %(relationship_cd)s,
    occupation_cd =  %(occupation_cd)s, blood_rh_cd =  %(blood_rh_cd)s, blood_abo_cd =  %(blood_abo_cd)s,
    graduate_cd =  %(graduate_cd)s, religion_cd =  %(religion_cd)s, allergy =  %(allergy)s, disease =  %(disease)s,
    nationality =  %(nationality)s, race =  %(race)s, note =  %(note)s,
    date_changed = NOW(), user_changed = %(userID)s,
    picture =  FROM_BASE64(%(imageUrlEncode)s)
    where patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey,'patient_id': patient_id,'prefix': prefix,'firstname': firstname,'middle_name': middle_name,
    'lastname': lastname,'sex': sex,'birthday': birthday,'status': status,'id_card': id_card,'passport_id':passport_id,'paymentPlan': paymentPlan,
    'anonymousName': anonymousName, 'anonymousFlag': anonymousFlag,
    'hn': hn, 'phone': phone, 'email': email, 'relationship_cd': relationship_cd,
    'occupation_cd': occupation_cd, 'blood_rh_cd': blood_rh_cd, 'blood_abo_cd': blood_abo_cd, 'graduate_cd': graduate_cd, 'religion_cd': religion_cd,
    'allergy': allergy, 'disease': disease, 'nationality': nationality, 'race': race, 'note': note, 'imageUrlEncode': imageUrlEncode,
    'userID': userID}
    cursor.execute(sql,params)
    sql = """\
    update address a
    inner join lis_patient_address b on a.address_skey = b.address_skey
    inner join lis_patient c on b.patient_skey = c.patient_skey
    set street_1 = %(street_1)s, street_2 = %(street_2)s, city = %(city)s, state = %(state)s, zip_postal_code = %(zip_postal_code)s,
    country_skey = %(country_skey)s,last_actv_dt = NOW()
    where b.patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey,'street_1': street_1,'street_2': street_2,'city': city,'state': state,
    'zip_postal_code': zip_postal_code,'country_skey': country_skey}
    cursor.execute(sql,params)
    print(patient_skey, 'patient_skey')
    print(first_name_relation, 'first_name_relation')
    print(middle_name, 'middle_name_relation')
    sql = """\
    update lis_patient_relation b
    inner join lis_patient c on b.patient_skey = c.patient_skey
    set b.prefix = %(prefix)s, b.firstname = %(firstname)s, b.middle_name = %(middle_name)s, b.lastname = %(lastname)s,
    b.sex = %(sex)s, b.relation_cd = %(relation_cd)s
    where b.patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey, 'prefix': prefix_relation,'firstname': first_name_relation,'middle_name': middle_name_relation,
    'lastname': Last_name_relation, 'sex': sex_relation, 'relation_cd': relation_cd}
    cursor.execute(sql,params)

    sql = """\
    update address a
    inner join lis_patient_relation b on a.address_skey = b.address_skey
    inner join lis_patient c on b.patient_skey = c.patient_skey
    set street_1 = %(street_1)s, street_2 = %(street_2)s, city = %(city)s, state = %(state)s, zip_postal_code = %(zip_postal_code)s,
    local_phone = %(local_phone)s,
    country_skey = %(country_skey)s,last_actv_dt = NOW()
    where b.patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey,'street_1': street1_relation,'street_2': street2_relation,'city': city_relation,'state': state_relation,
    'zip_postal_code': zipCode_relation,'country_skey': Country_relation,'local_phone': local_phone_relation}
    cursor.execute(sql,params)

    conn.commit()
    cursor.close()
    conn.close()

    # print(session['message'])

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลสิทธิ์ผู้ป่วยเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/updatePatientStatusMySQL", methods=['POST'])
def updatePatientStatusPlanMySQL():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['patient_skey']
    paramCheckStringList = ['patient_skey']

    # payload = getUserToken(request.headers.get('Authorization'))
    # userID = payload['user_id']

    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    userID = returnUserToken["data"]["user_id"]

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    patient_skey = dataInput['patient_skey']
    status = dataInput['status']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_patient where patient_skey like %s"
    cursor.execute(sql,patient_skey)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Patient " + patient_skey

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_patient set status =  %(status)s,
    date_changed = NOW(), user_changed = %(userID)s
    where patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey,'status': status,'userID': userID}
    cursor.execute(sql,params)

    conn.commit()
    cursor.close()
    conn.close()

    # print(session['message'])
    if status == "OP":
        statusDesc = "Open"
    elif status == "CA":
        statusDesc = "Cancel"

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขสถานะเป็น : ' + statusDesc)]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/deletePatientMySQL", methods=['POST'])
def deletePatientMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['patient_skey']
    paramCheckStringList = ['patient_skey']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    patient_skey = dataInput['patient_skey']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_patient where patient_skey like %s"
    cursor.execute(sql,patient_skey)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Patient " + patient_skey

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete address
    from address
    inner join lis_patient_relation b on address.address_skey = b.address_skey
    inner join lis_patient c on b.patient_skey = c.patient_skey
    where b.patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey}
    cursor.execute(sql,params)
    sql = """\
    delete lis_patient_relation
    from lis_patient_relation
    inner join lis_patient c on lis_patient_relation.patient_skey = c.patient_skey
    where lis_patient_relation.patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey}
    cursor.execute(sql,params)
    sql = """\
    delete address
    from address
    inner join lis_patient_address b on address.address_skey = b.address_skey
    inner join lis_patient c on b.patient_skey = c.patient_skey
    where b.patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey}
    cursor.execute(sql,params)
    sql = """\
    delete lis_patient_address
    from  lis_patient_address
    inner join lis_patient c on lis_patient_address.patient_skey = c.patient_skey
    where lis_patient_address.patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey}
    cursor.execute(sql,params)
    sql = """\
    delete from lis_patient where patient_skey = %(patient_skey)s
    """
    params = {'patient_skey': patient_skey}
    cursor.execute(sql,params)

    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลคนไข้เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrievePaymentPlanMySQL", methods=['POST'])
def retrievePaymentPlanMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = " select * from  lis_payment_plan"

    # sql = "SELECT user_id,first_name,last_name,ssn,employee_no,facility_cd,to_base64(picture) as picture_base64  from pc_user_def"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/addPaymentPlanMySQL", methods=['POST'])
def addPaymentPlanMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_payment_plan where description like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Code already " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    insert into lis_payment_plan
    (code,description,remark)
    values(%(code)s,%(description)s,%(remark)s)
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้างข้อมูลสิทธิ์ผู้ป่วยเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))



@patient_mysql.route("/patient/updatePaymentPlanMySQL", methods=['POST'])
def updatePaymentPlanMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_payment_plan where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Payment Plan " + code
        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]
        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_payment_plan
    set code = %(code)s,
    description = %(description)s,
    remark = %(remark)s
    where code = %(code)s
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลสิทธิ์ผู้ป่วยเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/deletePaymentPlanMySQL", methods=['POST'])
def deletePaymentPlanMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['code']
    paramCheckStringList = ['code']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_payment_plan where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Payment Plan " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete from lis_payment_plan
    where code = %(code)s
    """
    params = {'code': code}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลสิทธิ์ผู้ป่วยเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrievePrefixMySQL", methods=['POST'])
def retrievePrefixMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from patho_prefix order by prefix_cd"

    # sql = "SELECT user_id,first_name,last_name,ssn,employee_no,facility_cd,to_base64(picture) as picture_base64  from pc_user_def"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/addPrefixMySQL", methods=['POST'])
def addPrefixMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['prefix_cd','prefix_desc']
    paramCheckStringList = ['prefix_cd','prefix_desc']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    prefix_cd = dataInput['prefix_cd']
    prefix_desc = dataInput['prefix_desc']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from patho_prefix where prefix_desc like %s"
    cursor.execute(sql,prefix_desc)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "prefix already " + prefix_desc

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    insert into patho_prefix
    (prefix_cd,prefix_desc)
    values(%(prefix_cd)s,%(prefix_desc)s)
    """
    params = {'prefix_cd': prefix_cd,'prefix_desc': prefix_desc}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้างข้อมูลคำนำหน้าเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/updatePrefixMySQL", methods=['POST'])
def updatePrefixMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['prefix_cd','prefix_desc']
    paramCheckStringList = ['prefix_cd','prefix_desc']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    prefix_cd = dataInput['prefix_cd']
    prefix_desc = dataInput['prefix_desc']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from patho_prefix where prefix_cd like %s"
    cursor.execute(sql,prefix_cd)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Prefix " + prefix_cd

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update patho_prefix
    set prefix_cd = %(prefix_cd)s,
    prefix_desc = %(prefix_desc)s
    where prefix_cd = %(prefix_cd)s
    """
    params = {'prefix_cd': prefix_cd,'prefix_desc': prefix_desc}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลคำนำหน้าเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/deletePrefixMySQL", methods=['POST'])
def deletePrefixMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['prefix_cd']
    paramCheckStringList = ['prefix_cd']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    prefix_cd = dataInput['prefix_cd']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from patho_prefix where prefix_cd like %s"
    cursor.execute(sql,prefix_cd)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Prefix " + prefix_cd

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete from patho_prefix
    where prefix_cd = %(prefix_cd)s
    """
    params = {'prefix_cd': prefix_cd}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลคำนำหน้าเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrieveOccupationMySQL", methods=['POST'])
def retrieveOccupationMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_occupation"

    # sql = "SELECT user_id,first_name,last_name,ssn,employee_no,facility_cd,to_base64(picture) as picture_base64  from pc_user_def"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/addOccupationMySQL", methods=['POST'])
def addOccupationMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_occupation where description like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Code already " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    insert into lis_occupation
    (code,description,remark)
    values(%(code)s,%(description)s,%(remark)s)
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้างข้อมูลอาชีพเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))



@patient_mysql.route("/patient/updateOccupationMySQL", methods=['POST'])
def updateOccupationMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_occupation where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Occupation " + code
        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]
        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_occupation
    set code = %(code)s,
    description = %(description)s,
    remark = %(remark)s
    where code = %(code)s
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลอาขีพเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/deleteOccupationMySQL", methods=['POST'])
def deleteOccupationMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['code']
    paramCheckStringList = ['code']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_occupation where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Occupation " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete from lis_occupation
    where code = %(code)s
    """
    params = {'code': code}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลอาชีพเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrieveGraduateMySQL", methods=['POST'])
def retrieveGraduateMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_graduate"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/addGraduateMySQL", methods=['POST'])
def addGraduateMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_graduate where description like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Code already " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    insert into lis_graduate
    (code,description,remark)
    values(%(code)s,%(description)s,%(remark)s)
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้างข้อมูลการศึกษาเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))



@patient_mysql.route("/patient/updateGraduateMySQL", methods=['POST'])
def updateGraduateMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_graduate where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Graduate " + code
        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]
        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_graduate
    set code = %(code)s,
    description = %(description)s,
    remark = %(remark)s
    where code = %(code)s
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลการศึกษาเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/deleteGraduateMySQL", methods=['POST'])
def deleteGraduateMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['code']
    paramCheckStringList = ['code']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_graduate where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Graduate " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete from lis_graduate
    where code = %(code)s
    """
    params = {'code': code}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลการศึกษาเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrieveBloodAboMySQL", methods=['POST'])
def retrieveBloodAboMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_blood_abo"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/addBloodAboMySQL", methods=['POST'])
def addBloodAboMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_blood_abo where description like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Code already " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    insert into lis_blood_abo
    (code,description,remark)
    values(%(code)s,%(description)s,%(remark)s)
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้างข้อมูลกรุ๊ปเลือดเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))



@patient_mysql.route("/patient/updateBloodAboMySQL", methods=['POST'])
def updateBloodAboMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_blood_abo where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid BloodAbo " + code
        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]
        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_blood_abo
    set code = %(code)s,
    description = %(description)s,
    remark = %(remark)s
    where code = %(code)s
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลกรุ๊ปเลือดเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/deleteBloodAboMySQL", methods=['POST'])
def deleteBloodAboMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['code']
    paramCheckStringList = ['code']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_blood_abo where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid BloodAbo " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete from lis_blood_abo
    where code = %(code)s
    """
    params = {'code': code}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลกรุ๊ปเลือดเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrieveBloodRhMySQL", methods=['POST'])
def retrieveBloodRhMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_blood_rh"

    # sql = "SELECT user_id,first_name,last_name,ssn,employee_no,facility_cd,to_base64(picture) as picture_base64  from pc_user_def"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/addBloodRhMySQL", methods=['POST'])
def addBloodRhMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_blood_rh where description like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Code already " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    insert into lis_blood_rh
    (code,description,remark)
    values(%(code)s,%(description)s,%(remark)s)
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้างข้อมูลกรุ๊ปเลือด Rh เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))



@patient_mysql.route("/patient/updateBloodRhMySQL", methods=['POST'])
def updateBloodRhMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_blood_rh where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid BloodRh " + code
        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]
        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_blood_rh
    set code = %(code)s,
    description = %(description)s,
    remark = %(remark)s
    where code = %(code)s
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลกรุ๊ปเลือด Rh เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/deleteBloodRhMySQL", methods=['POST'])
def deleteBloodRhMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['code']
    paramCheckStringList = ['code']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_blood_rh where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid BloodRh " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete from lis_blood_rh
    where code = %(code)s
    """
    params = {'code': code}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลกรุ๊ปเลือด Rh เรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrieveReligionMySQL", methods=['POST'])
def retrieveReligionMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_religion"

    # sql = "SELECT user_id,first_name,last_name,ssn,employee_no,facility_cd,to_base64(picture) as picture_base64  from pc_user_def"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/addReligionMySQL", methods=['POST'])
def addReligionMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_religion where description like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Code already " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    insert into lis_religion
    (code,description,remark)
    values(%(code)s,%(description)s,%(remark)s)
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้างข้อมูลกรุ๊ปเลือดศาสนาเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))



@patient_mysql.route("/patient/updateReligionMySQL", methods=['POST'])
def updateReligionMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_religion where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Religion " + code
        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]
        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_religion
    set code = %(code)s,
    description = %(description)s,
    remark = %(remark)s
    where code = %(code)s
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลศาสนาเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/deleteReligionMySQL", methods=['POST'])
def deleteReligionMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['code']
    paramCheckStringList = ['code']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_religion where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Religion " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete from lis_religion
    where code = %(code)s
    """
    params = {'code': code}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลศาสนาเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrieveRelationshipStatusMySQL", methods=['POST'])
def retrieveRelationshipStatusMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select * from lis_relationship_status"

    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/addRelationshipStatusMySQL", methods=['POST'])
def addRelationshipStatusMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_relationship_status where description like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows>0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Code already " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    insert into lis_relationship_status
    (code,description,remark)
    values(%(code)s,%(description)s,%(remark)s)
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'สร้างข้อมูลสถานะภาพผู้ป่วยเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))



@patient_mysql.route("/patient/updateRelationshipStatusMySQL", methods=['POST'])
def updateRelationshipStatusMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    paramList = ['code','description']
    paramCheckStringList = ['code','description']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']
    description = dataInput['description']
    remark = dataInput['remark']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_relationship_status where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Relationship Status " + code
        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]
        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    update lis_relationship_status
    set code = %(code)s,
    description = %(description)s,
    remark = %(remark)s
    where code = %(code)s
    """
    params = {'code': code,'description': description,'remark': remark}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'แก้ไขข้อมูลสถานะภาพผู้ป่วยเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/deleteRelationshipStatusMySQL", methods=['POST'])
def deleteRelationshipStatusMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['code']
    paramCheckStringList = ['code']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    code = dataInput['code']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "select count(1) from lis_relationship_status where code like %s"
    cursor.execute(sql,code)
    (number_of_rows,)=cursor.fetchone()

    if number_of_rows==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Relationship Status " + code

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJsonOne(errData,errColumns))

    sql = """\
    delete from lis_relationship_status
    where code = %(code)s
    """
    params = {'code': code}
    cursor.execute(sql,params)
    conn.commit()
    cursor.close()
    conn.close()

    displayColumns = ['isSuccess','reasonCode','reasonText']
    displayData = [(isSuccess,reasonCode,'ลบข้อมูลสถานะภาพผู้ป่วยเรียบร้อย')]

    return jsonify(toJsonOne(displayData,displayColumns))

@patient_mysql.route("/patient/retrieveVisitDateMySQL", methods=['POST'])
def retrieveVisitDateMySQL():
    returnUserToken = getUserToken(request.headers.get('Authorization'))
    if not returnUserToken["isSuccess"]:
        return jsonify(returnUserToken);

    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    PatientId = dataInput['PatientId']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """\
    SELECT 1 AS no,DATE_FORMAT(date_arrived,'%%d/%%m/%%Y') as dateArrived, date_arrived,visit_skey
    FROM lis_visit
    inner join lis_patient on lis_visit.patient_skey = lis_patient.patient_skey
    where patient_id = %(PatientId)s
    order by date_arrived
    """

    # sql = "SELECT user_id,first_name,last_name,ssn,employee_no,facility_cd,to_base64(picture) as picture_base64  from pc_user_def"
    params = {'PatientId': PatientId}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    displayColumns = ['isSuccess','data']
    displayData = [(isSuccess,toJson(data,columns))]

    return jsonify(toJsonOne(displayData,displayColumns))
