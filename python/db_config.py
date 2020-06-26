
from flask import Flask, session, redirect, url_for
from flask import Flask, request, jsonify, current_app, abort, send_from_directory
from flask_cors import CORS, cross_origin
from flask import Blueprint
from flaskext.mysql import MySQL
import json
from bson import BSON
from bson import json_util
import os
import pymssql
import datetime
import re
import random

from common import *

app = Flask(__name__)

prefixPath = "/FlaskBNHLabOnline"
# prefixPath = "/"

mssql_server='.'
#mssql_database='iSLIM_Krit'
#
#mssql_user='sa'
#mssql_password='Aphrozonetw2tw2017'
#mssql_database='iSLIM_Golf'
mssql_database='BNH_lab_online'
mssql_user='sa'
mssql_password='P@ssw0rd'

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'admin'
app.config['MYSQL_DATABASE_DB'] = 'clinic'
# app.config['MYSQL_DATABASE_HOST'] = '192.168.10.249'
# app.config['MYSQL_DATABASE_HOST'] = '192.168.10.250'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'

http_liff = 'https://liff.line.me/'
liff_id_login = '1654122544-NdqQ6qkX'

# get channel_secret and channel_access_token from your environment variable
# channel_secret = '151f33243dff886a36729d1b9e93201e'
# channel_access_token = 'KGlCQl0VHl3N190Fa16DaDS2IZFEblEZUw8wMbPoLVU40BoTpQRNSzKee4floExkPiKHEA6BwoL39g6+DGgKIMRDTiIHz8Xm8P5P6MCYzbdzorYTx8rInZhni9eY7svMeDn3gKzDQLjtdveWfUdTdAdB04t89/1O/w1cDnyilFU='
channel_secret = '6166217f317105b7db3d8c9cd1a342bd'
channel_access_token = 'WaZxNAhKWY04nnNmRAVpJl856PQ/51lUrwitTzJR4mw313bFCLR5XS1yCKJ70I8sbU31ibp2i86iv7VPxyzq5cJVtC4XrAPupS1zup748+8e9m3MZqShDV3gfjAWkOjXoMyu9Pm7jolFqlAj2/3krwdB04t89/1O/w1cDnyilFU='
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')

mysql = MySQL()
mysql.init_app(app)
