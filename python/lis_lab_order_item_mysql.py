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

lis_lab_order_item_mysql = Blueprint('lis_lab_order_item_mysql', __name__)

def insertOrUpdateLabOrderItemMySQL(conn,dataInsertOrUpdate):
    try:
        now = datetime.datetime.now()

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        orderSkey = dataInsertOrUpdate['order_skey']
        orderItemSkey = dataInsertOrUpdate['order_item_skey']
        editFlag = dataInsertOrUpdate['edit_flag']
        x = 1
        y = 1
        active = dataInsertOrUpdate['active']
        cancel = dataInsertOrUpdate['cancel']
        note = dataInsertOrUpdate['note']
        rcDateCreated = None
        rcUserCreated = None

        cursor = conn.cursor()
        sql = """\
        select count(1)
        from lis_lab_order inner join lis_lab_order_item on
        lis_lab_order.order_skey = lis_lab_order_item.order_skey
        where lis_lab_order_item.order_skey = %(order_skey)s and
        lis_lab_order_item.order_item_skey = %(order_item_skey)s
        """
        params = {'order_skey': orderSkey,'order_item_skey' : orderItemSkey}
        cursor.execute(sql,params)

        (number_of_rows,)=cursor.fetchone()
        if number_of_rows==0:
            sql = """\
            insert into lis_lab_order_item
            (order_skey,order_item_skey,x,y,active,cancel,note,rc_date_created,rc_user_created)
            values(%(order_skey)s,%(order_item_skey)s,%(x)s,%(y)s,%(active)s,%(cancel)s,%(note)s,%(rc_date_created)s,%(rc_user_created)s)
            """
            params = {'order_skey': orderSkey,'order_item_skey': orderItemSkey,'x': x,'y': y,
            'active': active,'cancel': cancel,'note': note,'rc_date_created': rcDateCreated,'rc_user_created': rcUserCreated}
            cursor.execute(sql,params)
        elif editFlag == 2:
            sql = """\
            update lis_lab_order_item
            set x = %(x)s,
            y = %(y)s,
            active = %(active)s,
            cancel = %(cancel)s,
            note = %(note)s,
            rc_date_created = %(rc_date_created)s,
            rc_user_created = %(rc_user_created)s
            where order_skey = %(order_skey)s and
            order_item_skey = %(order_item_skey)s
            """
            params = {'order_skey': orderSkey,'order_item_skey': orderItemSkey,'x': x,'y': y,
            'active': active,'cancel': cancel,'note': note,'rc_date_created': rcDateCreated,'rc_user_created': rcUserCreated}
            cursor.execute(sql,params)
    except Exception as e:
        raise e

def insertLabOrderItemMySQL(conn,dataInsert):
    try:
        now = datetime.datetime.now()

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        orderSkey = dataInsert['order_skey']
        orderItemSkey = dataInsert['order_item_skey']
        x = 1
        y = 1
        active = dataInsert['active']
        cancel = dataInsert['cancel']
        note = dataInsert['note']
        rcDateCreated = None
        rcUserCreated = None

        cursor = conn.cursor()
        sql = """\
        insert into lis_lab_order_item
        (order_skey,order_item_skey,x,y,active,cancel,note,rc_date_created,rc_user_created)
        values(%(order_skey)s,%(order_item_skey)s,%(x)s,%(y)s,%(active)s,%(cancel)s,%(note)s,%(rc_date_created)s,%(rc_user_created)s)
        """
        params = {'order_skey': orderSkey,'order_item_skey': orderItemSkey,'x': x,'y': y,
        'active': active,'cancel': cancel,'note': note,'rc_date_created': rcDateCreated,'rc_user_created': rcUserCreated}
        cursor.execute(sql,params)

        print('insert',orderItemSkey)
    except Exception as e:
        raise e

def updateLabOrderItemMySQL(conn,dataUpdate):
    try:
        now = datetime.datetime.now()

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);

        userID = returnUserToken["data"]["user_id"]

        orderSkey = dataUpdate['order_skey']
        orderItemSkey = dataUpdate['order_item_skey']
        x = 1
        y = 1
        active = dataUpdate['active']
        cancel = dataUpdate['cancel']
        note = dataUpdate['note']
        rcDateCreated = None
        rcUserCreated = None

        cursor = conn.cursor()
        sql = """\
        update lis_lab_order_item
        set x = %(x)s,
        y = %(y)s,
        active = %(active)s,
        cancel = %(cancel)s,
        note = %(note)s,
        rc_date_created = %(rc_date_created)s,
        rc_user_created = %(rc_user_created)s
        where order_skey = %(order_skey)s and
        order_item_skey = %(order_item_skey)s
        """
        params = {'order_skey': orderSkey,'order_item_skey': orderItemSkey,'x': x,'y': y,
        'active': active,'cancel': cancel,'note': note,'rc_date_created': rcDateCreated,'rc_user_created': rcUserCreated}
        cursor.execute(sql,params)
        print('update',orderItemSkey)
    except Exception as e:
        raise e

def deleteLabOrderItemMySQL(conn,dataInsertOrUpdate):
    try:
        now = datetime.datetime.now()

        returnUserToken = getUserToken(request.headers.get('Authorization'))
        if not returnUserToken["isSuccess"]:
            return jsonify(returnUserToken);
        userID = returnUserToken["data"]["user_id"]

        orderSkey = dataInsertOrUpdate['order_skey']
        orderItemSkey = dataInsertOrUpdate['order_item_skey']

        cursor = conn.cursor()

        sql = """\
        delete from lis_lab_order_item
        where order_skey = %(order_skey)s and
        order_item_skey = %(order_item_skey)s
        """
        params = {'order_skey': orderSkey,'order_item_skey' : orderItemSkey}
        cursor.execute(sql,params)
        print('delete',orderItemSkey)
    except Exception as e:
        raise e
