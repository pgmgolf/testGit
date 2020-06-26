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
from openpyxl import load_workbook
from werkzeug import secure_filename
import math
import codecs
from flask import Flask, request, make_response
from pyreportjasper import JasperPy

from db_config import *
from common import *

tax = Blueprint('tax', __name__)

@tax.route("/tax/gettaxYear", methods=['POST'])
def gettaxYear ():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    # sql = "select tax_name,tax_percent,tax_qty,tax_amount from temptax"
    sql = "select * from TaxYear"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@tax.route("/tax/gettax", methods=['POST'])
def gettax ():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    # sql = "select tax_name,tax_percent,tax_qty,tax_amount from temptax"
    sql = "select * from tempCalTax"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@tax.route("/tax/getDepreciationRate", methods=['POST'])
def getDepreciationRate ():
    isSuccess = True
    dataInput = request.json
    paramList = ['type_building','plant_year']
    paramCheckStringList = ['type_building','plant_year']
    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);
    typeBuilding = dataInput['type_building']
    plantYear = dataInput['plant_year']
    dataInput = request.json
    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = """select plantYear,typeBuilding,DepreciationRate
    from DepreciationRate a
    where exists (select max(b.plantYear),b.typeBuilding from DepreciationRate b
    		where b.plantYear <= %(plantYear)s and
    		b.typeBuilding = %(typeBuilding)s
    		group by b.typeBuilding
    		having max(b.plantYear) = a.plantYear and b.typeBuilding = a.typeBuilding)"""
    params = {'plantYear': plantYear,'typeBuilding': typeBuilding}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()

    return jsonify(toJson(data,columns))

@tax.route("/tax/getTaxRate", methods=['POST'])
def getTaxRate ():
    isSuccess = True
    dataInput = request.json
    paramList = ['type_use','cost_estimate','exception_detail','wasteland_year']
    paramCheckStringList = ['type_use','cost_estimate','exception_detail','wasteland_year']
    # msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    # print('-Golf2-----------------------------------------------')
    # if msgError != None:
    #     return jsonify(msgError);
    TypeUse = dataInput['type_use']
    CostEstimate = dataInput['cost_estimate']
    ExceptionDetail = dataInput['exception_detail']
    WastelandYear = dataInput['wasteland_year']
    dataInput = request.json
    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = """\
    DECLARE @TaxRate decimal(9,2);
    EXEC sp_get_TaxRate @TypeUse = %(TypeUse)s, @CostEstimate = %(CostEstimate)s, @ExceptionDetail = %(ExceptionDetail)s, @WastelandYear = %(WastelandYear)s, @TaxRate = @TaxRate OUTPUT;
    select @TaxRate as TaxRate
    """
    params = {'TypeUse': TypeUse,'CostEstimate': CostEstimate,'ExceptionDetail': ExceptionDetail,'WastelandYear': WastelandYear}
    cursor.execute(sql,params)
    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    print(columns)
    return jsonify(toJson(data,columns))

@tax.route("/tax/getTaxCal", methods=['POST'])
def getTaxCal ():
    isSuccess = True
    dataInput = request.json
    paramList = ['json_list']
    paramCheckStringList = ['json_list']
    JsonList = dataInput['json_list']
    dataInput = request.json
    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = """\
    DECLARE @AmountTotal decimal(18,2),@AmountTotalNet decimal(18,2),@Allowance decimal(18,2) ;
    EXEC sp_Cal_Tax @JsonList = %(JsonList)s, @AmountTotal = @AmountTotal output, @AmountTotalNet = @AmountTotalNet output, @Allowance = @Allowance output
    select @AmountTotal as AmountTotal, @AmountTotalNet as AmountTotalNet, @Allowance as Allowance
    """
    params = {'JsonList': JsonList}
    cursor.execute(sql,params)
    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@tax.route("/tax/getTaxCals", methods=['POST'])
def getTaxCals ():
    isSuccess = True
    dataInput = request.json
    paramList = ['json_list','tax_year','type_plan','type_person','type_use','type_owner','wasteland_year','cost_estimate','tax_total_old']
    paramCheckStringList = ['json_list','tax_year','type_plan','type_person','type_use','type_owner','wasteland_year','cost_estimate','tax_total_old']
    taxCalSQLs = dataInput['tax_cal_sql']

    for i in taxCalSQLs:
        taxYear = i['CalTax_taxYear']
        TypePlan = i['CalTax_TypePlan']
        TypeUse = i['CalTax_TypeUse']
        TypePerson = i['CalTax_TypePerson']
        TypeOwner = i['CalTax_TypeOwner']
        WastelandYear = i['CalTax_Owner_year']
        CostEstimate = i['CalTax_CostEstimate']
        CostEstimateSpacePlantingAreaDepreciation = i['CalTax_CostEstimateSpacePlantingAreaDepreciation']
        CostEstimateApartmentArea = i['CalTax_CostEstimateApartmentArea']
        TaxOld = i['CalTax_TaxOld']
        if CostEstimate == '' or CostEstimate == '-' or CostEstimate == '':
           CostEstimate = 0
        if CostEstimateSpacePlantingAreaDepreciation == '' or CostEstimateSpacePlantingAreaDepreciation == '-' or CostEstimateSpacePlantingAreaDepreciation == '':
           CostEstimateSpacePlantingAreaDepreciation = 0
        if CostEstimateApartmentArea == '' or CostEstimateApartmentArea == '-' or CostEstimateApartmentArea == '':
           CostEstimateApartmentArea = 0

        CostEstimateLandAndBuilding = float(CostEstimate) + float(CostEstimateSpacePlantingAreaDepreciation)
        # print(taxYear)
        # print(TypePlan)
        # print(TypeUse)
        # print(TypePerson)
        # print(TypeOwner)
        # print(WastelandYear)
        # print(CostEstimate)
        # print(CostEstimateSpacePlantingAreaDepreciation)
        print(CostEstimateLandAndBuilding, 'CostEstimateLandAndBuilding', i['CalTax_No'])
        print(CostEstimateApartmentArea, 'CostEstimateApartmentArea', i['CalTax_No'])


    # print(taxCalSQL)
    # with open("Output.txt", "w") as text_file:
    # print(taxCalSQL, file=text_file)
    data = ''
    columns = ''
    return jsonify(toJson(data,columns))
@tax.route("/tax/ExportToExcel", methods=['POST'])
def ExportToExcel():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['data_json']
    paramCheckStringList = ['data_json']

    msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
    if msgError != None:
        return jsonify(msgError);

    dataJson = dataInput['data_json']

    now = datetime.datetime.now()
    datetimeStr = now.strftime('%Y%m%d_%H%M%S%f')
    filename_tmp = secure_filename('{}_{}'.format(datetimeStr, 'Template_Poll.xlsx'))
    wb = load_workbook('Template\Template_Poll.xlsx')

    if len(dataJson) > 0:
        print(dataJson)
        sheet = wb['แบบฟอร์มสำหรับจัดเก็บข้อมูล อปท']
        sheet['D3'] = dataJson[0]["json_changwatsInput"]
        sheet['D2'] = dataJson[0]['json_taxYearBE']
        sheet['D4'] = dataJson[0]['json_subDistrictHeaderInput']
        sheet['D5'] = dataJson[0]['json_DistrictHeaderInput']

        offset = 9
        i = 0
        for row in dataJson:
            sheet['A'+str(offset + i)] = row['json_No']
            sheet['B'+str(offset + i)] = row['json_CodeOwner']
            sheet['C'+str(offset + i)] = row['json_DistrictHeaderInput']
            sheet['D'+str(offset + i)] = row['json_TTaxpayerStatus']
            sheet['E'+str(offset + i)] = row['json_TTypeUseLand']
            sheet['F'+str(offset + i)] = row['json_TypeOwner']
            sheet['G'+str(offset + i)] = row['json_TypeUseLands']
            sheet['H'+str(offset + i)] = row['json_ParcelNumber']
            sheet['I'+str(offset + i)] = row['json_DeedNumber']
            sheet['J'+str(offset + i)] = row['json_SheetNumber']
            sheet['K'+str(offset + i)] = row['json_SpaceAreaSqw']
            sheet['L'+str(offset + i)] = row['json_CostEstimateSpaceAreaSQ']
            sheet['M'+str(offset + i)] = row['json_CostEstimate']
            sheet['N'+str(offset + i)] = row['json_PlantType']
            sheet['O'+str(offset + i)] = row['json_plantFloor']
            sheet['P'+str(offset + i)] = row['json_plantYear']
            sheet['Q'+str(offset + i)] = row['json_SpacePlantingAreaSqm']
            sheet['R'+str(offset + i)] = row['json_CostEstimateSpacePlantingAreaSqm']
            sheet['S'+str(offset + i)] = row['json_CostEstimateSpacePlantingArea']
            sheet['T'+str(offset + i)] = row['json_DepreciationRate']
            sheet['U'+str(offset + i)] = row['json_Depreciation']
            sheet['V'+str(offset + i)] = row['json_CostEstimateSpacePlantingAreaDepreciation']
            sheet['W'+str(offset + i)] = row['json_TypeUseMix']
            sheet['X'+str(offset + i)] = row['json_SpacePlantingAreaSqmMix']
            sheet['Y'+str(offset + i)] = row['json_CostEstimateMix']
            sheet['Z'+str(offset + i)] = row['json_CostEstimateSpacePlantingAreaMix']
            sheet['AA'+str(offset + i)] = row['json_CostEstimateLandAndBuilding']
            sheet['AB'+str(offset + i)] = row['json_TaxRate']
            sheet['AC'+str(offset + i)] = row['json_AmountTotal']
            sheet['AD'+str(offset + i)] = row['json_Allowance']
            sheet['AE'+str(offset + i)] = row['json_TaxOlderLandAndProperty']
            sheet['AF'+str(offset + i)] = row['json_TaxOlderLocal']
            sheet['AG'+str(offset + i)] = row['json_AmountTotalNet']
            sheet['AH'+str(offset + i)] = row['json_TaxActual']
            sheet['AI'+str(offset + i)] = row['json_remark']
            # j = 1
            # for col in row:
            #     sheet[num_to_col_letters(j)+str(offset + i)] = row[col]
            #     j = j + 1
            i = i + 1

    wb.save(filename_tmp)

    with open(os.path.dirname(os.path.abspath(__file__)) + '/' + filename_tmp, "rb") as f:
        encoded_string = base64.b64encode(f.read())

    os.remove(filename_tmp)

    displayColumns = ['isSuccess','reasonCode','reasonText','excel_base64']
    displayData = [(isSuccess,reasonCode,reasonText,encoded_string)]

    return jsonify(toJsonOne(displayData,displayColumns))

@tax.route("/tax/getProvice", methods=['POST'])
def getProvice ():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    # sql = "select tax_name,tax_percent,tax_qty,tax_amount from temptax"
    sql = "select distinct province_name from province order by province_name"
    cursor.execute(sql)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@tax.route("/tax/getDistric", methods=['POST'])
def getDistric ():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    provice = dataInput['provice']
    print(provice)
    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = "select distinct district from province where province_name like %s order by district"
    cursor.execute(sql,provice)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))

@tax.route("/tax/getSubDistric", methods=['POST'])
def getSubDistric ():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""
    dataInput = request.json
    provice = dataInput['provice']
    district = dataInput['district']
    print(provice)
    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = "select distinct sub_district from province where province_name like %(provice)s and district like %(district)s order by sub_district"
    params = {'provice': provice,'district': district}
    cursor.execute(sql,params)



    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    conn.commit()
    cursor.close()
    return jsonify(toJson(data,columns))
