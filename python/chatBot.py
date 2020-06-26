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

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    MemberJoinedEvent, MemberLeftEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton,
    ImageSendMessage)

from db_config import *
from common import *

chatBot = Blueprint('chatBot', __name__)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

def checkLineUserID(lineUserID):
    try:
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)

        cursor = conn.cursor()
        sql = """\
        select pc_user_def.user_skey,pc_user_def.user_id,pc_user_def.first_name,pc_user_def.middle_name,pc_user_def.last_name,pc_user_def.ssn,
        pc_user_def.employee_no,pc_user_def.profile_skey,pc_user_def.active_flag,pc_user_def.facility_cd,pc_user_def.fin_default_co,
        pc_user_def.cust_skey,pc_user_def.email,pc_user_def.phone,pc_user_def.line_user_id,
        pc_profile_def.profile_name,pc_profile_def.sys_admin_ind,company.company_name,customer.cust_no,customer.name as cust_name
        from pc_user_def left outer join employee on
        pc_user_def.employee_no = employee.employee_no left outer join pc_profile_def on
        pc_user_def.profile_skey = pc_profile_def.profile_skey left outer join company on
        pc_user_def.fin_default_co = company .company_cd left outer join customer on
        pc_user_def.cust_skey = customer.cust_skey
        where line_user_id = %(line_user_id)s
        """
        params = {'line_user_id': lineUserID}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        return toJsonOne(data,columns)
    except Exception as e:
        print(e)

def getAppointmentPatient(appointmentSkey):
    try:
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)

        cursor = conn.cursor()
        sql = """\
        select lis_web_appointment.*,pc_user_def.line_user_id
        from lis_web_appointment inner join lis_lab_order on
        lis_web_appointment.order_skey = lis_lab_order.order_skey inner join lis_visit on
        lis_lab_order.visit_skey = lis_visit.visit_skey inner join facility on
        lis_visit.facility_cd = facility.facility_cd inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd left outer join pc_user_def on
        pc_user_def.patient_skey = lis_patient.patient_skey
        where lis_web_appointment.appointment_skey = %(appointment_skey)s
        """
        params = {'appointment_skey': appointmentSkey}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        return toJsonOne(data,columns)
    except Exception as e:
        print(e)

def getLabOrderPatient(orderSkey):
    try:
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)

        cursor = conn.cursor()
        sql = """\
        select lis_lab_order.order_skey,lis_lab_order.order_id,
		case when lis_lab_order.anonymous is null or len(lis_lab_order.anonymous) = 0 then patho_prefix.prefix_desc + ' ' + lis_patient.firstname + ' ' + lis_patient.lastname else lis_lab_order.anonymous end as patient_name,
		pc_user_def.line_user_id
        from lis_lab_order  inner join lis_visit on
        lis_lab_order.visit_skey = lis_visit.visit_skey inner join facility on
        lis_visit.facility_cd = facility.facility_cd inner join lis_patient on
        lis_visit.patient_skey = lis_patient.patient_skey inner join patho_sex on
        lis_patient.sex = patho_sex.sex_cd inner join patho_prefix on
        lis_patient.prefix = patho_prefix.prefix_cd left outer join pc_user_def on
        pc_user_def.patient_skey = lis_patient.patient_skey
        where lis_lab_order.order_skey = %(order_skey)s
        """
        params = {'order_skey': orderSkey}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        return toJsonOne(data,columns)
    except Exception as e:
        print(e)

def getClinicalUserID(lineUserID):
    try:
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)

        cursor = conn.cursor()

        sql = """\
        EXEC sp_lis_get_clinical_user @line_user_id = %(line_user_id)s;
        """
        params = {'line_user_id': lineUserID}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        return toJson(data,columns)
    except Exception as e:
        print(e)

def getLabOrderClinicalNotification(orderID,resultItemSkeyList):
    try:
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)

        cursor = conn.cursor()

        sql = """\
        EXEC sp_lis_get_lab_order_clinical_notification @order_id = %(order_id)s,@result_item_skey_list = %(result_item_skey_list)s;
        """
        params = {'order_id': orderID,'result_item_skey_list': resultItemSkeyList}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        return toJsonOne(data,columns)
    except Exception as e:
        print(e)

def getLineUserClinicalNotification(orderID):
    try:
        conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)

        cursor = conn.cursor()

        sql = """\
        EXEC sp_get_line_user_clinical_notification @order_id = %(order_id)s;
        """
        params = {'order_id': orderID}
        cursor.execute(sql,params)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        return toJson(data,columns)
    except Exception as e:
        print(e)

@chatBot.route("/sendClinical", methods=['POST'])
def sendClinical():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['order_id']
        paramCheckStringList = ['order_id']

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderID = dataInput['order_id']
        resultItemSkeyList = dataInput.get("result_item_skey_list", '')

        labOrderClinicalNotification = getLabOrderClinicalNotification(orderID,resultItemSkeyList)
        if labOrderClinicalNotification:
            lineUserClinicalNotification = getLineUserClinicalNotification(orderID)
            if lineUserClinicalNotification:
                for lineUser in lineUserClinicalNotification:
                    text = ""
                    text += "Clinical\n"""
                    text += "Patient Name {}\n"""
                    text += "HN {} Sex {}\n"""
                    text += "Lab Order {}\n"""
                    text += "Received Date {}\n"""
                    text += "{}/{}.pdf\n"
                    text += "{}\n"""
                    resultText = text.format(labOrderClinicalNotification["patient_name"],ifNoneValue(labOrderClinicalNotification["hn"],""),labOrderClinicalNotification["sex_desc"],labOrderClinicalNotification["order_id"],labOrderClinicalNotification["received_date"].strftime('%d-%b-%Y %H:%M:%S'),url_clinical,labOrderClinicalNotification["order_id"],labOrderClinicalNotification["result_item_list"])
                    resultText = resultText[0:1999]
                    line_bot_api.push_message(
                        lineUser["line_user_id"], [
                            TextSendMessage(resultText
                                )
                        ]
                    )
            else:
                isSuccess = False
                reasonCode = 500

                errColumns = ['isSuccess','reasonCode','reasonText']
                errData = [(isSuccess,reasonCode,'Not Found User Clinical Notification For Order ID{}'.format(orderID))]

                return jsonify(toJsonOne(errData,errColumns))
        else:
            isSuccess = False
            reasonCode = 500

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,'Not Found Order ID {}'.format(orderID))]

            return jsonify(toJsonOne(errData,errColumns))

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'ส่ง Clinical เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@chatBot.route("/sendLabResult", methods=['POST'])
def sendLabResult():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['order_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        orderSkey = dataInput['order_skey']
        labOrderPatient = getLabOrderPatient(orderSkey)
        if labOrderPatient:
            if len(ifNoneValue(labOrderPatient["line_user_id"],"")) == 0:
                isSuccess = False
                reasonCode = 500

                errColumns = ['isSuccess','reasonCode','reasonText']
                errData = [(isSuccess,reasonCode,'Not Found Line User ID for Order Skey {}'.format(orderSkey))]

                return jsonify(toJsonOne(errData,errColumns))

            f = open("ChatBotTemplate/lab_result.json","r",encoding='utf-8-sig')
            bubble_string = f.read()
            f.close()

            bubble_string = bubble_string.replace("/*order_id*/",ifNoneValue(labOrderPatient["order_id"],""))
            message = FlexSendMessage(alt_text="Lab Result", contents=json.loads(bubble_string))
            line_bot_api.push_message(labOrderPatient["line_user_id"],message)

            conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
            cursor = conn.cursor()
            sql = """\
            update lis_lab_order
            set line_sent_result_date = %(line_sent_result_date)s
            where order_skey = %(order_skey)s
            """
            params = {'order_skey': orderSkey,'line_sent_result_date': datetime.datetime.now()}
            cursor.execute(sql,params)
            conn.commit()
            cursor.close()
            conn.close()
        else:
            isSuccess = False
            reasonCode = 500

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,'Not Found Order Skey {}'.format(orderSkey))]

            return jsonify(toJsonOne(errData,errColumns))

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'ส่ง Lab Result เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@chatBot.route("/sendAppointment", methods=['POST'])
def sendAppointment():
    try:
        now = datetime.datetime.now()
        isSuccess = True
        reasonCode = 200
        reasonText = ""

        dataInput = request.json
        paramList = ['appointment_skey']
        paramCheckStringList = []

        msgError = checkParamDataInput(dataInput,paramList,paramCheckStringList)
        if msgError != None:
            return jsonify(msgError);

        appointmentSkey = dataInput['appointment_skey']

        appointmentPatient = getAppointmentPatient(appointmentSkey)
        if appointmentPatient:
            if len(ifNoneValue(appointmentPatient["line_user_id"],"")) == 0:
                isSuccess = False
                reasonCode = 500

                errColumns = ['isSuccess','reasonCode','reasonText']
                errData = [(isSuccess,reasonCode,'Not Found Line User ID for Appointment Skey {}'.format(appointmentSkey))]

                return jsonify(toJsonOne(errData,errColumns))

            # text = ""
            # text += "เลขที่นัด / Appointment ID : {}\n"""
            # text += "วันที่นัด/Appointment Date : {}\n"""
            # text += "เวลา / Time : {}\n"""
            # resultText = text.format(appointmentPatient["appointment_id"],appointmentPatient["appointment_date"].strftime('%d-%b-%Y'),appointmentPatient["appointment_date"].strftime('%H:%M'))
            # resultText = resultText[0:1999]
            f = open("ChatBotTemplate/appointment.json","r",encoding='utf-8-sig')
            bubble_string = f.read()
            f.close()

            bubble_string = bubble_string.replace("/*appointment_id*/",ifNoneValue(appointmentPatient["appointment_id"],""))
            bubble_string = bubble_string.replace("/*appointment_date*/",ifNoneValue(appointmentPatient["appointment_date"].strftime('%d-%b-%Y')," "))
            bubble_string = bubble_string.replace("/*appointment_time*/",ifNoneValue(appointmentPatient["appointment_date"].strftime('%H:%M')," "))
            message = FlexSendMessage(alt_text="Appointment", contents=json.loads(bubble_string))
            line_bot_api.push_message(appointmentPatient["line_user_id"],message)

            conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
            cursor = conn.cursor()
            sql = """\
            update lis_web_appointment
            set line_sent_appointment_date = %(line_sent_appointment_date)s
            where appointment_skey = %(appointment_skey)s
            """
            params = {'appointment_skey': appointmentSkey,'line_sent_appointment_date': datetime.datetime.now()}
            cursor.execute(sql,params)
            conn.commit()
            cursor.close()
            conn.close()
        else:
            isSuccess = False
            reasonCode = 500

            errColumns = ['isSuccess','reasonCode','reasonText']
            errData = [(isSuccess,reasonCode,'Not Found Appointment Skey {}'.format(appointmentSkey))]

            return jsonify(toJsonOne(errData,errColumns))

        displayColumns = ['isSuccess','reasonCode','reasonText']
        displayData = [(isSuccess,reasonCode,'ส่ง Appointment เรียบร้อย')]

        return jsonify(toJsonOne(displayData,displayColumns))
    except Exception as e:
        isSuccess = False
        reasonCode = 500

        errColumns = ['isSuccess','reasonCode','reasonText']
        errData = [(isSuccess,reasonCode,str(e))]

        return jsonify(toJsonOne(errData,errColumns))

@chatBot.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.json
    bodyText = request.get_data(as_text=True)
    # app.logger.info("Request body: " + bodyText)
    f = open("log.txt", "a")
    f.write(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + '\t' + bodyText + '\n')
    f.close()

    # handle webhook body
    try:
        lineUserID = body["events"][0]["source"]["userId"]
        profile = line_bot_api.get_profile(lineUserID)
        userInfo = checkLineUserID(lineUserID)

        if body["events"][0]["type"] != "chatRead":
            if userInfo:
                # print("ยินดีต้อนรับคูณ {}".format(userInfo["user_id"]))
                app.logger.info("ยินดีต้อนรับคูณ {}".format(userInfo["user_id"]))

                handler.handle(bodyText, signature)
            else:
                # line_bot_api.reply_message(
                #     body["events"][0]["replyToken"],
                #     TextMessage(text="กรุณา Login"))
                line_bot_api.reply_message(
                    body["events"][0]["replyToken"],
                    TextMessage(text="กรุณา Login\n{}{}".format(http_liff,liff_id_login)))
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    profile = line_bot_api.get_profile(event.source.user_id)
    userInfo = checkLineUserID(event.source.user_id)
    if text == 'info':
        if isinstance(event.source, SourceUser):
            if userInfo:
                # line_bot_api.reply_message(
                #     event.reply_token, [
                #         ImageSendMessage(
                #             original_content_url=ifNoneValue(profile.picture_url,"https://www.aaa.com/aa"),
                #             preview_image_url=ifNoneValue(profile.picture_url,"https://www.aaa.com/aa"),
                #         )
                #     ]
                # )

                f = open("ChatBotTemplate/user_info.json", "r")
                bubble_string = f.read()
                f.close()

                bubble_string = bubble_string.replace("/*picture_url*/",ifNoneValue(profile.picture_url,"https://www.aaa.com/aa"))
                bubble_string = bubble_string.replace("/*first_name*/",ifNoneValue(userInfo["first_name"]," "))
                bubble_string = bubble_string.replace("/*last_name*/",ifNoneValue(userInfo["last_name"]," "))
                bubble_string = bubble_string.replace("/*email*/",ifNoneValue(userInfo["email"],"-"))
                bubble_string = bubble_string.replace("/*phone*/",ifNoneValue(userInfo["phone"],"-"))
                message = FlexSendMessage(alt_text="User Info", contents=json.loads(bubble_string))
                line_bot_api.reply_message(event.reply_token, message)

                # line_bot_api.push_message(
                #     event.source.user_id, [
                #         TextSendMessage(
                #             text='คุณ {} {}\nEmail {}\nTel {}'
                #             .format(userInfo["first_name"],userInfo["last_name"],userInfo["email"],userInfo["phone"])
                #         )
                #     ]
                # )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't use profile API without user ID"))
    elif text == 'tel':
        if isinstance(event.source, SourceUser):
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="tel:0868905463"))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't use profile API without user ID"))
    elif text == 'Clinical':
        if isinstance(event.source, SourceUser):
            labOrdersUser = getClinicalUserID(event.source.user_id)
            if labOrdersUser:
                first_name = ''
                lastt_name = ''
                if userInfo:
                    first_name = userInfo["first_name"]
                    # last_name = userInfo["last_name"]
                    # line_bot_api.push_message(
                    #     event.source.user_id, [
                    #         ImageSendMessage(
                    #             original_content_url=profile.picture_url,
                    #             preview_image_url=profile.picture_url
                    #         )
                    #     ]
                    # )
                    # line_bot_api.push_message(
                    #     event.source.user_id, [
                    #         TextMessage(text="คุณ {} {}\nผล Clinical 5 ครั้งล่าสุด".format(userInfo["first_name"],userInfo["last_name"]))
                    #     ]
                    # )
                for labOrder in labOrdersUser:
                    f = open("ChatBotTemplate/clinical_result.json", "r")
                    bubble_string = f.read()
                    f.close()

                    bubble_string = bubble_string.replace("/*order_id*/",labOrder["order_id"])
                    bubble_string = bubble_string.replace("/*patient_name*/",labOrder["patient_name"])
                    bubble_string = bubble_string.replace("/*received_date*/",labOrder["received_date"].strftime('%Y-%m-%d-%H:%M:%S'))
                    bubble_string = bubble_string.replace("/*hn*/",ifNoneValue(labOrder["hn"]," "))
                    bubble_string = bubble_string.replace("/*sex_desc*/",labOrder["sex_desc"])
                    bubble_string = bubble_string.replace("/*test_item_desc_list*/",labOrder["test_item_desc_list"])
                    message = FlexSendMessage(alt_text="Lab Result", contents=json.loads(bubble_string))

                    # line_bot_api.push_message(
                    #     event.source.user_id,message)

                    line_bot_api.reply_message(event.reply_token, message)
                    # TextSendMessage(
                    #     text='Lab Order {}\nReceived Date {}\nline://app/1654084194-9JVnOQEb?order_id={}'
                    #     .format(labOrder["order_id"],labOrder["received_date"],labOrder["order_id"],labOrder["order_id"]))
            else:
                first_name = ''
                lastt_name = ''
                if userInfo:
                    first_name = userInfo["first_name"]
                    last_name = userInfo["last_name"]

                line_bot_api.reply_message(
                    event.reply_token,
                    TextMessage(text="คุณ {} {}\nไม่มีผล Clinical".format(userInfo["first_name"],userInfo["last_name"])))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text="Bot can't use profile API without user ID"))
    elif text == 'profile':
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text='Display name: ' + profile.display_name),
                    TextSendMessage(text='Status message: ' + str(profile.status_message))
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Bot can't use profile API without user ID"))
    elif text == 'quota':
        quota = line_bot_api.get_message_quota()
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text='type: ' + quota.type),
                TextSendMessage(text='value: ' + str(quota.value))
            ]
        )
    elif text == 'quota_consumption':
        quota_consumption = line_bot_api.get_message_quota_consumption()
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text='total usage: ' + str(quota_consumption.total_usage)),
            ]
        )
    elif text == 'push':
        line_bot_api.push_message(
            event.source.user_id, [
                TextSendMessage(text='PUSH!'),
            ]
        )
    elif text == 'multicast':
        line_bot_api.multicast(
            [event.source.user_id], [
                TextSendMessage(text='THIS IS A MULTICAST MESSAGE'),
            ]
        )
    elif text == 'broadcast':
        line_bot_api.broadcast(
            [
                TextSendMessage(text='THIS IS A BROADCAST MESSAGE'),
            ]
        )
    elif text.startswith('broadcast '):  # broadcast 20190505
        date = text.split(' ')[1]
        print("Getting broadcast result: " + date)
        result = line_bot_api.get_message_delivery_broadcast(date)
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text='Number of sent broadcast messages: ' + date),
                TextSendMessage(text='status: ' + str(result.status)),
                TextSendMessage(text='success: ' + str(result.success)),
            ]
        )
    elif text == 'bye':
        if isinstance(event.source, SourceGroup):
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='Leaving group'))
            line_bot_api.leave_group(event.source.group_id)
        elif isinstance(event.source, SourceRoom):
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(text='Leaving group'))
            line_bot_api.leave_room(event.source.room_id)
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Bot can't leave from 1:1 chat"))
    elif text == 'image':
        url = request.url_root + '/static/logo.png'
        app.logger.info("url=" + url)
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(url, url)
        )
    elif text == 'confirm':
        confirm_template = ConfirmTemplate(text='Do it?', actions=[
            MessageAction(label='Yes', text='Yes!'),
            MessageAction(label='No', text='No!'),
        ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif text == 'buttons':
        buttons_template = ButtonsTemplate(
            title='My buttons sample', text='Hello, my buttons', actions=[
                URIAction(label='Go to line.me', uri='https://line.me'),
                PostbackAction(label='ping', data='ping'),
                PostbackAction(label='ping with text', data='ping', text='ping'),
                MessageAction(label='Translate Rice', text='米')
            ])
        template_message = TemplateSendMessage(
            alt_text='Buttons alt text', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif text == 'carousel':
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(text='hoge1', title='fuga1', actions=[
                URIAction(label='Go to line.me', uri='https://line.me'),
                PostbackAction(label='ping', data='ping')
            ]),
            CarouselColumn(text='hoge2', title='fuga2', actions=[
                PostbackAction(label='ping with text', data='ping', text='ping'),
                MessageAction(label='Translate Rice', text='米')
            ]),
        ])
        template_message = TemplateSendMessage(
            alt_text='Carousel alt text', template=carousel_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif text == 'image_carousel':
        image_carousel_template = ImageCarouselTemplate(columns=[
            ImageCarouselColumn(image_url='https://via.placeholder.com/1024x1024',
                                action=DatetimePickerAction(label='datetime',
                                                            data='datetime_postback',
                                                            mode='datetime')),
            ImageCarouselColumn(image_url='https://via.placeholder.com/1024x1024',
                                action=DatetimePickerAction(label='date',
                                                            data='date_postback',
                                                            mode='date'))
        ])
        template_message = TemplateSendMessage(
            alt_text='ImageCarousel alt text', template=image_carousel_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    elif text == 'imagemap':
        pass
    elif text == 'flex':
        bubble = BubbleContainer(
            direction='ltr',
            hero=ImageComponent(
                url='https://example.com/cafe.jpg',
                size='full',
                aspect_ratio='20:13',
                aspect_mode='cover',
                action=URIAction(uri='http://example.com', label='label')
            ),
            body=BoxComponent(
                layout='vertical',
                contents=[
                    # title
                    TextComponent(text='Brown Cafe', weight='bold', size='xl'),
                    # review
                    BoxComponent(
                        layout='baseline',
                        margin='md',
                        contents=[
                            IconComponent(size='sm', url='https://example.com/gold_star.png'),
                            IconComponent(size='sm', url='https://example.com/grey_star.png'),
                            IconComponent(size='sm', url='https://example.com/gold_star.png'),
                            IconComponent(size='sm', url='https://example.com/gold_star.png'),
                            IconComponent(size='sm', url='https://example.com/grey_star.png'),
                            TextComponent(text='4.0', size='sm', color='#999999', margin='md',
                                          flex=0)
                        ]
                    ),
                    # info
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                spacing='sm',
                                contents=[
                                    TextComponent(
                                        text='Place',
                                        color='#aaaaaa',
                                        size='sm',
                                        flex=1
                                    ),
                                    TextComponent(
                                        text='Shinjuku, Tokyo',
                                        wrap=True,
                                        color='#666666',
                                        size='sm',
                                        flex=5
                                    )
                                ],
                            ),
                            BoxComponent(
                                layout='baseline',
                                spacing='sm',
                                contents=[
                                    TextComponent(
                                        text='Time',
                                        color='#aaaaaa',
                                        size='sm',
                                        flex=1
                                    ),
                                    TextComponent(
                                        text="10:00 - 23:00",
                                        wrap=True,
                                        color='#666666',
                                        size='sm',
                                        flex=5,
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='sm',
                contents=[
                    # callAction, separator, websiteAction
                    SpacerComponent(size='sm'),
                    # callAction
                    ButtonComponent(
                        style='link',
                        height='sm',
                        action=URIAction(label='CALL', uri='tel:000000'),
                    ),
                    # separator
                    SeparatorComponent(),
                    # websiteAction
                    ButtonComponent(
                        style='link',
                        height='sm',
                        action=URIAction(label='WEBSITE', uri="https://example.com")
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
    elif text == 'flex_update_1':
        bubble_string = """
        {
          "type": "bubble",
          "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "image",
                "url": "https://scdn.line-apps.com/n/channel_devcenter/img/flexsnapshot/clip/clip3.jpg",
                "position": "relative",
                "size": "full",
                "aspectMode": "cover",
                "aspectRatio": "1:1",
                "gravity": "center"
              },
              {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                  {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": "Brown Hotel",
                        "weight": "bold",
                        "size": "xl",
                        "color": "#ffffff"
                      },
                      {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                          {
                            "type": "icon",
                            "size": "sm",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                          },
                          {
                            "type": "icon",
                            "size": "sm",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                          },
                          {
                            "type": "icon",
                            "size": "sm",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                          },
                          {
                            "type": "icon",
                            "size": "sm",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gold_star_28.png"
                          },
                          {
                            "type": "icon",
                            "size": "sm",
                            "url": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/review_gray_star_28.png"
                          },
                          {
                            "type": "text",
                            "text": "4.0",
                            "size": "sm",
                            "color": "#d6d6d6",
                            "margin": "md",
                            "flex": 0
                          }
                        ]
                      }
                    ]
                  },
                  {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                      {
                        "type": "text",
                        "text": "¥62,000",
                        "color": "#a9a9a9",
                        "decoration": "line-through",
                        "align": "end"
                      },
                      {
                        "type": "text",
                        "text": "¥42,000",
                        "color": "#ebebeb",
                        "size": "xl",
                        "align": "end"
                      }
                    ]
                  }
                ],
                "position": "absolute",
                "offsetBottom": "0px",
                "offsetStart": "0px",
                "offsetEnd": "0px",
                "backgroundColor": "#00000099",
                "paddingAll": "20px"
              },
              {
                "type": "box",
                "layout": "vertical",
                "contents": [
                  {
                    "type": "text",
                    "text": "SALE",
                    "color": "#ffffff"
                  }
                ],
                "position": "absolute",
                "backgroundColor": "#ff2600",
                "cornerRadius": "20px",
                "paddingAll": "5px",
                "offsetTop": "10px",
                "offsetEnd": "10px",
                "paddingStart": "10px",
                "paddingEnd": "10px"
              }
            ],
            "paddingAll": "0px"
          }
        }
        """
        message = FlexSendMessage(alt_text="hello", contents=json.loads(bubble_string))
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
    elif text == 'quick_reply':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='Quick reply',
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=PostbackAction(label="label1", data="data1")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="label2", text="text2")
                        ),
                        QuickReplyButton(
                            action=DatetimePickerAction(label="label3",
                                                        data="data3",
                                                        mode="date")
                        ),
                        QuickReplyButton(
                            action=CameraAction(label="label4")
                        ),
                        QuickReplyButton(
                            action=CameraRollAction(label="label5")
                        ),
                        QuickReplyButton(
                            action=LocationAction(label="label6")
                        ),
                    ])))
    elif text == 'link_token' and isinstance(event.source, SourceUser):
        link_token_response = line_bot_api.issue_link_token(event.source.user_id)
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text='link_token: ' + link_token_response.link_token)
            ]
        )
    elif text == 'insight_message_delivery':
        today = datetime.date.today().strftime("%Y%m%d")
        response = line_bot_api.get_insight_message_delivery(today)
        if response.status == 'ready':
            messages = [
                TextSendMessage(text='broadcast: ' + str(response.broadcast)),
                TextSendMessage(text='targeting: ' + str(response.targeting)),
            ]
        else:
            messages = [TextSendMessage(text='status: ' + response.status)]
        line_bot_api.reply_message(event.reply_token, messages)
    elif text == 'insight_followers':
        today = datetime.date.today().strftime("%Y%m%d")
        response = line_bot_api.get_insight_followers(today)
        if response.status == 'ready':
            messages = [
                TextSendMessage(text='followers: ' + str(response.followers)),
                TextSendMessage(text='targetedReaches: ' + str(response.targeted_reaches)),
                TextSendMessage(text='blocks: ' + str(response.blocks)),
            ]
        else:
            messages = [TextSendMessage(text='status: ' + response.status)]
        line_bot_api.reply_message(event.reply_token, messages)
    elif text == 'insight_demographic':
        response = line_bot_api.get_insight_demographic()
        if response.available:
            messages = ["{gender}: {percentage}".format(gender=it.gender, percentage=it.percentage)
                        for it in response.genders]
        else:
            messages = [TextSendMessage(text='available: false')]
        line_bot_api.reply_message(event.reply_token, messages)
    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text))


@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title='Location', address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )


# Other Message Type
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save content.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(MessageEvent, message=FileMessage)
def handle_file_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='file-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '-' + event.message.file_name
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save file.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(FollowEvent)
def handle_follow(event):
    app.logger.info("Got Follow event:" + event.source.user_id)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text='Got follow event'))


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    app.logger.info("Got Unfollow event:" + event.source.user_id)


@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Joined this ' + event.source.type))


@handler.add(LeaveEvent)
def handle_leave():
    app.logger.info("Got leave event")


@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data == 'ping':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='pong'))
    elif event.postback.data == 'datetime_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['datetime']))
    elif event.postback.data == 'date_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['date']))


@handler.add(BeaconEvent)
def handle_beacon(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='Got beacon event. hwid={}, device_message(hex string)={}'.format(
                event.beacon.hwid, event.beacon.dm)))


@handler.add(MemberJoinedEvent)
def handle_member_joined(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='Got memberJoined event. event={}'.format(
                event)))


@handler.add(MemberLeftEvent)
def handle_member_left(event):
    app.logger.info("Got memberLeft event")
