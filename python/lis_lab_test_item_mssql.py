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

lis_lab_test_item_mssql = Blueprint('lis_lab_test_item_mssql', __name__)

def updateLabTestItemMSSQL(conn,dataUpdate):
    try:
        now = datetime.datetime.now()

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        orderSkey = dataUpdate.get("order_skey", None)
        testItemSkey = dataUpdate.get("test_item_skey", None)
        completeFlag = dataUpdate.get("complete_flag", None)
        completeDate = dataUpdate.get("complete_date", None)
        vendorSkey = dataUpdate.get("vendor_skey", None)
        dueDate = dataUpdate.get("due_date", None)
        sentDate = dataUpdate.get("sent_date", None)
        jobDocNo = dataUpdate.get("job_doc_no", None)
        remark = dataUpdate.get("remark", None)
        status = dataUpdate.get("status", None)
        subCategorySkey = dataUpdate.get("sub_category_skey", None)
        dueDateOutlab = dataUpdate.get("due_date_outlab", None)
        requiredAllResultItem = dataUpdate.get("required_all_result_item", None)
        stickerCode = dataUpdate.get("sticker_cd", None)
        testItemStatus = dataUpdate.get("test_item_status", None)
        rejectFlag = dataUpdate.get("reject_flag", None)

        cursor = conn.cursor()
        sql = """\
        update lis_lab_test_item
        set complete_flag = %(complete_flag)s,
        complete_date = %(complete_date)s,
        vendor_skey = %(vendor_skey)s,
        due_date = %(due_date)s,
        sent_date = %(sent_date)s,
        job_doc_no = %(job_doc_no)s,
        remark = %(remark)s,
        status = %(status)s,
        sub_category_skey = %(sub_category_skey)s,
        due_date_outlab = %(due_date_outlab)s,
        required_all_result_item = %(required_all_result_item)s,
        sticker_cd = %(sticker_cd)s,
        test_item_status = %(test_item_status)s,
        reject_flag = %(reject_flag)s
        where order_skey = %(order_skey)s and
        test_item_skey = %(test_item_skey)s
        """
        params = {'order_skey': orderSkey,'test_item_skey': testItemSkey,'complete_flag': completeFlag,'complete_date': completeDate,
        'vendor_skey': vendorSkey,'due_date': dueDate,'sent_date': sentDate,'job_doc_no': jobDocNo,'remark': remark,
        'status': status,'sub_category_skey': subCategorySkey,'due_date_outlab': dueDateOutlab,'required_all_result_item': requiredAllResultItem,
        'sticker_cd': stickerCode,'test_item_status': testItemStatus,'reject_flag': rejectFlag}
        cursor.execute(sql,params)

        print('update',orderSkey,testItemSkey,requiredAllResultItem,completeFlag)
    except Exception as e:
        raise e
