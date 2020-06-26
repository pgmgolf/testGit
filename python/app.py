from flask import Flask, session, redirect, url_for
from flask import Flask, request, jsonify, current_app, abort, send_from_directory
from flask_cors import CORS, cross_origin
from flaskext.mysql import MySQL
from logging.config import dictConfig
import json
from bson import BSON
from bson import json_util
import os
import pymssql
import datetime
import re
import random
from common import *
from chatBot import *
from test import test
from db_mysql import db_mysql
from db_mssql import db_mssql
from common import common
from browse_mssql import browse_mssql
from jasper import jasper
from tax import tax
from excel import excel
from user_mysql import user_mysql
from user_mssql import user_mssql
from nav_group_mysql import nav_group_mysql
from nav_window_mysql import nav_window_mysql
from nav_window_sercurity_mysql import nav_window_sercurity_mysql
from nav_user_object_mysql import nav_user_object_mysql
from nav_group_object_mysql import nav_group_object_mysql
from nav_node_mysql import nav_node_mysql
from nav_node_language_mysql import nav_node_language_mysql
from nav_node_language_mssql import nav_node_language_mssql
from nav_route_mysql import nav_route_mysql
from patient_mysql import patient_mysql
from employee_mysql import employee_mysql
from visit_mysql import visit_mysql
from clinic_mysql import clinic_mysql
from timeslot_mysql import timeslot_mysql
from visit_episode_mysql import visit_episode_mysql
from episode_diagnose_mysql import episode_diagnose_mysql
from episode_procedure_mysql import episode_procedure_mysql
from episode_prescription_mysql import episode_prescription_mysql
from episode_attachment_mysql import episode_attachment_mysql
from physician_mysql import physician_mysql
from uom_mysql import uom_mysql
from visit_mssql import visit_mssql
from nav_group_mssql import nav_group_mssql
from nav_window_mssql import nav_window_mssql
from nav_window_sercurity_mssql import nav_window_sercurity_mssql
from nav_user_object_mssql import nav_user_object_mssql
from nav_group_object_mssql import nav_group_object_mssql
from nav_node_mssql import nav_node_mssql
from nav_route_mssql import nav_route_mssql
from lab_order_mysql import lab_order_mysql
from lab_order_mssql import lab_order_mssql
from lis_order_item_mysql import lis_order_item_mysql
from lis_order_item_mssql import lis_order_item_mssql
from lis_lab_test_item_mssql import lis_lab_test_item_mssql
from lab_order_manual_result import lab_order_manual_result
# from lis_lab_order_item_mysql import lis_lab_order_item_mysql
from pymongoDB import pymongoDB
from schedule_resource_mssql import schedule_resource_mssql
from mobile import mobile
from web_order import web_order
from labOrderEntry import LabOrderEntry

app = Flask(__name__)
app.debug = True
app.config.from_object('config.BaseConfig')
CORS(app)

dictConfig({
'version': 1,
'formatters': {'default': {
    'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
}},
'handlers': {
    'wsgi': {
        'class': 'logging.StreamHandler',
        'formatter': 'default'
    },
    'custom_handler': {
        'class': 'logging.FileHandler',
        'formatter': 'default',
        'filename': r'log\flask.log'
    }
},
'root': {
    'level': 'INFO',
    'handlers': ['wsgi', 'custom_handler']
}
})

# UPLOAD_FOLDER = '/path/to/the/uploads'
UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route(prefixPath + "/",methods=['GET'])
def hello():
    return "Welcome to Innotech Clinic"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

app.register_blueprint(test, url_prefix=prefixPath)
app.register_blueprint(db_mysql, url_prefix=prefixPath)
app.register_blueprint(db_mssql, url_prefix=prefixPath)
app.register_blueprint(common, url_prefix=prefixPath)
app.register_blueprint(chatBot, url_prefix=prefixPath)
app.register_blueprint(browse_mssql, url_prefix=prefixPath)
app.register_blueprint(jasper, url_prefix=prefixPath)
app.register_blueprint(excel, url_prefix=prefixPath)
app.register_blueprint(user_mysql, url_prefix=prefixPath)
app.register_blueprint(user_mssql, url_prefix=prefixPath)
app.register_blueprint(nav_group_mysql, url_prefix=prefixPath)
app.register_blueprint(nav_window_mysql, url_prefix=prefixPath)
app.register_blueprint(nav_window_sercurity_mysql, url_prefix=prefixPath)
app.register_blueprint(nav_user_object_mysql, url_prefix=prefixPath)
app.register_blueprint(nav_group_object_mysql, url_prefix=prefixPath)
app.register_blueprint(nav_node_mysql, url_prefix=prefixPath)
app.register_blueprint(nav_node_language_mysql, url_prefix=prefixPath)
app.register_blueprint(nav_node_language_mssql, url_prefix=prefixPath)
app.register_blueprint(nav_route_mysql, url_prefix=prefixPath)
app.register_blueprint(patient_mysql, url_prefix=prefixPath)
app.register_blueprint(tax, url_prefix=prefixPath)
app.register_blueprint(employee_mysql, url_prefix=prefixPath)
app.register_blueprint(visit_mysql, url_prefix=prefixPath)
app.register_blueprint(clinic_mysql, url_prefix=prefixPath)
app.register_blueprint(timeslot_mysql, url_prefix=prefixPath)
app.register_blueprint(visit_episode_mysql, url_prefix=prefixPath)
app.register_blueprint(episode_diagnose_mysql, url_prefix=prefixPath)
app.register_blueprint(episode_procedure_mysql, url_prefix=prefixPath)
app.register_blueprint(episode_prescription_mysql, url_prefix=prefixPath)
app.register_blueprint(episode_attachment_mysql, url_prefix=prefixPath)
app.register_blueprint(physician_mysql, url_prefix=prefixPath)
app.register_blueprint(uom_mysql, url_prefix=prefixPath)
app.register_blueprint(visit_mssql, url_prefix=prefixPath)
app.register_blueprint(nav_group_mssql, url_prefix=prefixPath)
app.register_blueprint(nav_window_mssql, url_prefix=prefixPath)
app.register_blueprint(nav_window_sercurity_mssql, url_prefix=prefixPath)
app.register_blueprint(nav_user_object_mssql, url_prefix=prefixPath)
app.register_blueprint(nav_group_object_mssql, url_prefix=prefixPath)
app.register_blueprint(nav_node_mssql, url_prefix=prefixPath)
app.register_blueprint(nav_route_mssql, url_prefix=prefixPath)
app.register_blueprint(lab_order_mysql, url_prefix=prefixPath)
app.register_blueprint(lab_order_mssql, url_prefix=prefixPath)
app.register_blueprint(lis_order_item_mysql, url_prefix=prefixPath)
app.register_blueprint(lis_order_item_mssql, url_prefix=prefixPath)
app.register_blueprint(lis_lab_test_item_mssql, url_prefix=prefixPath)
app.register_blueprint(lab_order_manual_result, url_prefix=prefixPath)
app.register_blueprint(schedule_resource_mssql, url_prefix=prefixPath)
app.register_blueprint(pymongoDB, url_prefix=prefixPath)
# app.register_blueprint(lis_lab_order_item_mysql, url_prefix=prefixPath)
app.register_blueprint(mobile, url_prefix=prefixPath)
app.register_blueprint(web_order, url_prefix=prefixPath)
app.register_blueprint(labOrderEntry, url_prefix=prefixPath)

if __name__ == "__main__":
    app.run()
    # app.run(host = '0.0.0.0',port=5000)
