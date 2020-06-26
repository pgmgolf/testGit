
from flask import Flask, session, redirect, url_for
from flask import Flask, request, jsonify, current_app, abort, send_from_directory
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

from common import *

from keystoneauth1 import session
from keystoneauth1.identity import v3
from keystoneclient.v3 import client
from novaclient.client import Client as client_nova
from neutronclient.v2_0 import client as client_neutron
from glanceclient import Client as client_glance
from cinderclient import client as client_cinder

cluster = Blueprint('cluster', __name__)

@cluster.route("/bio/cluster/testcreate", methods=['GET'])
def testcreate(clusterName,flavorID):
    auth = v3.Password(
                        auth_url='https://horizon.openlandscape.cloud:5000/v3',
                        username='dev_bio',
                        user_id='f273a6d2bfb44b84b15fe545ab8c31d7',
                        password='F3A]<a=h',
                        project_id='ff1c4ac29c9d44a988662fa122fd56e2'
                        )

    sess = session.Session(auth=auth)
    keystone = client.Client(version='v3', session=sess)


    nova = client_nova(2, session=keystone.session)
    neutron = client_neutron.Client(session=keystone.session)
    glance = client_glance(2, session=keystone.session)
    cinder = client_cinder.Client(1, session=keystone.session)

    for f in nova.flavors.list():
        print(f.id + ' ' + f.name)

    for g in glance.images.list():
    	if g.id == '2836883f-4ecd-4854-9723-42e9648f5e09':
    		image = g

    flavor  = nova.flavors.find(id=flavorID)
    net = nova.neutron.find_network("bio_net")
    nics = [{'net-id': net.id}]
    instance = nova.servers.create(name=clusterName,
                                       image=image,
                                       flavor=flavor,
                                       userdata=userdata_key('MIIEogIBAAKCAQEAoj2goQ54vr7RiuOZtLdCy9rCJXoJDO3y5/yZOFV+Q3MeC1Ww'
'HYSLoC8P4OZWt9ovwDZvKC3kZ4WT0oexdCD4/zlgXRRAqnoiiU9Fsghl1jAQhVi8'
'P4/9W/AWzaXSLwSk4fPOFWN3r8CW7IT7sUax8TXaWbFCu8X7r2X38XPKK7GGbHOB'
'6mDRi54hjMusJd6vuphAbbbarZ3y/J1nSjbuV+/6B3zNEnIVopc0UKqj6JH2x/be'
'MRjH8nlBSCtqQoJVn2e7M2dgYPoE8ox531/fgYZpchc3P5JgH9SgKlmR0JF6Bqio'
'q4yGabUs/YJIcGf994AqGMuWF4hA8sRXxhQlTwIDAQABAoIBAArKfI+ZzdAqEvfg'
'8Y1Cjy/N6hHiDw4MGZbyhyJnFVHZK0tntKIR+dN6rdywlV3/JiPruvL6MnHsQYvE'
'OLpXoxgesdkfCroMC5YEbsdLpbJcWgz0fPjhU+G0k1+0Qsmbzne05qUni4NmFOPA'
'aJk+8YDwqwhCMQUaQwZEivxFTlIfjoPgNZOsOM4hK0btjt3m0Rr7Ob/zv8n0rNXs'
'XJeGTcJhLvLqYUbyQ711EznwpZ8ZYXcQg2aOyR3X6xtS0XCTY4GduXKflGFKYkV/'
'pLLjZK4tXhUy22PYeJY8Y/b2rJOchVn8QwdoidVE5tdyWnzxRgHI6IKVj+NDGJ8O'
'DG/dMVkCgYEA1e2MhgMvbreRAY7or2m96fOIkergIlF1uBtBWDxDWRk2x5+ki2kG'
'EJW38dlb63QHJVnR3Y2lGrMw9nBMqw+cJKtSbs9gJu5MRYVoZGB1l4GsR0PvS9xQ'
'nEqd8x+gtx39KLkmkpx9bclRrhTkkvC8G5d5cm1vF/mCbdhqcgLl2RMCgYEAwiXT'
'k6p6l9cMR2SsFm5jqiDHowxpYcB/dHVYYylEQpK1mFp+csyClxErkTiImCtOlnCr'
'0S5k1mEbuEzN2MgUwjCtlEEzRWCpqZYFeXrqip+Xow6uQcuvcgpdXdqz8rN0XwQA'
'h2zf7C4PCW4Yg+n8K31HPk5jkjaDgvzUb6nU5lUCgYA93530KLmwUSF8jOPZ0ECg'
'iNJoOcGny1276Q4mQg/MllFUvWSu+apKY7M3HQHMANwMPoVHii9FoKw5qtNR6orj'
'xDVsXUhXGjcvKF3AInIAZv34ArsUet1Jxv8WEYC/Vcoh3CM+5koU1dRtABf4M+6E'
'IHR81w/5pC3ILX7kCNiHxwKBgCE0qQhDiy43KLF5RXmcrc0mSB7Z+5gtfV8kxtZG'
'85bTUt3Y9HGcCuXdmO8AlVQ5a/qNEMX5QmPsPfp6oGZoaiyAeN+3exZtnvcTYqJR'
'ZJYLD7tiwmkcdkhx/2ATDN4A1XF+1LxU4cOaaRX6z5SYS3oAtlOwwpT6X+niZk8m'
'4/P1AoGAXbaR+/AeQ62H82ZIllvkjte1jtud5W20hJYinSEdOtvhpxPa4Ru7rqP4'
'HmFkgcKGUrY+pf4ESyt0Z0jikZD6dC+vB2LtX+WxYpi7AbhYtdr06kOc5Gc9npgB'
'fi8DlfybQKHlXxa7yPav4c2Cb4DQ8fU+LkYQX4bAXrgP8yu0a7w=K/J7eDzurlXy0qlAHuRE1NrYU1GQsZ1KULvA7GcZGuzE6Z/T8Zt87AoGBAMEkwKqXY7hCwIUQsFLcZoUDRFHDqv4MSj5B43JofUSmUhpbXCY/YnLepF8SYa79dGfb5oKTxm2ppgZsGGmUwpmGTcWZnErJ8+C7Ygd0t6wYh1HYgZ2VHpHCjCA5mjVqb6vvk3w7TqGkpo6y6P4h2VUV9Upn8KumgDBQ7mctzZLsy' ,clusterName),
                                       nics=nics,
                                       max_count=1,
    								   availability_zone='nova')
    return 'Create cluster ok'



@cluster.route("/bio/cluster/getClusterStatusList", methods=['GET'])
def getClusterStatusList():
    columns = ['code','description']
    data = [('OP','Open'),('CA','Cancel'),('TR','Terminate')]

    return jsonify(toJson(data,columns))

# @cluster.route("/bio/cluster/getClusterList", methods=['GET'])
# def getClusterList():
#     now = datetime.datetime.now()
#     columns = ['cluster_name','cluster_id','status','created','duration','node']
#     data=[]
#     for i in range(0, 20):
#         data.append(('Cluster Name ' + str(i),'ClusterID_' + str(i),'OP',now,'1 ชัวโมง 30 นาที','1/4'))
#
#     return jsonify(toJson(data,columns))

@cluster.route("/bio/cluster/getClusterList", methods=['GET'])
def getClusterList():
    client = MongoClient('localhost', 27017)
    db = client.bio
    cluster = db.cluster

    cluster_list = list(cluster.find({},{ "cluster_id": 1, "cluster_name": 1,
                                        "cluster_status": 1, "cluster_duration": 1, "cluster_node_qty": 1}))

    # i = 1
    # for clusterData in cluster_list:
    #     if i % random.randint(1,4) == 0:
    #         clusterData['select_row'] = False
    #     else:
    #         clusterData['select_row'] = True
    #     i = i + 1

    i = 1
    for clusterData in cluster_list:
        clusterData['select_row'] = False

    return json.dumps(cluster_list, sort_keys=True, indent=2, default=json_util.default)

@cluster.route("/bio/cluster/cloneCluster", methods=['POST'])
def cloneCluster():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['cluster_id']
    paramCheckStringList = ['cluster_id']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    clusterID = dataInput['cluster_id']

    client = MongoClient('localhost', 27017)
    db = client.bio
    cluster = db.cluster

    clusterList = list(db.cluster.find({"cluster_id" : clusterID},{"cluster_name" : 1}))

    if len(clusterList) == 0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Cluster ID " + clusterID

        columns = ['isSuccess','reasonCode','reasonText']
        data = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJson(data,columns))

    # Clone Cluster

    columns = ['isSuccess','reasonCode','reasonText']
    data = [(isSuccess,reasonCode,"Clone Cluster สำเร็จ")]

    return jsonify(toJson(data,columns))


@cluster.route("/bio/cluster/terminateCluster", methods=['POST'])
def terminateCluster():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['cluster_id']
    paramCheckStringList = ['cluster_id']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    clusterID = dataInput['cluster_id']

    client = MongoClient('localhost', 27017)
    db = client.bio
    cluster = db.cluster

    clusterList = list(db.cluster.find({"cluster_id" : clusterID},{"cluster_name" : 1}))

    if len(clusterList) == 0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Invalid Cluster ID " + clusterID

        columns = ['isSuccess','reasonCode','reasonText']
        data = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJson(data,columns))

    # Terminate Cluster

    columns = ['isSuccess','reasonCode','reasonText']
    data = [(isSuccess,reasonCode,"Terminate Cluster สำเร็จ")]

    return jsonify(toJson(data,columns))


@cluster.route("/bio/cluster/getCreateClusterPage", methods=['GET'])
def getCreateClusterPage():
    client = MongoClient('localhost', 27017)
    db = client.bio
    release = db.release
    flavor = db.flavor
    keyPair = db.key_pair
    releaseList = list(release.find({},{"_id": 0}))
    flavorList = list(flavor.find({},{"_id": 0}))
    keyPairList = list(keyPair.find({},{"_id": 0}))

    releaseJson = json.dumps(releaseList, sort_keys=True, indent=2, default=json_util.default)
    flavorJson = json.dumps(flavorList, sort_keys=True, indent=2, default=json_util.default)
    keyPairJson = json.dumps(keyPairList, sort_keys=True, indent=2, default=json_util.default)

    # clusterlicationJson = toJson(clusterlicationData,clusterlicationColumn)
    #
    # machineColumn = ['machine_code','machine_description']
    # machineData = [('A','m1.large'),('B','m1.medium')]
    #
    # machineJson = toJson(machineData,machineColumn)
    #
    # keyPairColumn = ['keyPair']
    # keyPairData = [('ggdsgsfsdfsghgadfdsf',)]
    #
    # keyPairJson = toJson(keyPairData,keyPairColumn)
    #
    return jsonify(release = releaseList,flavor = flavorList,keyPair = keyPairList)


@cluster.route("/bio/cluster/createKeyPair", methods=['POST'])
def createKeyPair():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['key_pair']
    paramCheckStringList = ['key_pair']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    keyPair = dataInput['key_pair']

    if len(keyPair)==0:
        isSuccess = False
        reasonCode = 500
        reasonText = "Please enter Key Pair"

        columns = ['isSuccess','reasonCode','reasonText']
        data = [(isSuccess,reasonCode,reasonText)]

        return jsonify(toJson(data,columns))

    columns = ['isSuccess','reasonCode','reasonText']
    data = [(isSuccess,reasonCode,"Create KeyPair สำเร็จ")]

    return jsonify(toJson(data,columns))


@cluster.route("/bio/cluster/createCluster", methods=['POST'])
def createCluster():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['clusterName','nodeQty','keyPair','FlavorID']
    paramCheckStringList = ['clusterName','keyPair','FlavorID']
    paramCheckNumberList = ['nodeQty']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckNumberList and not isinstance(dataInput[param], int)):
            isSuccess = False
            reasonCode = 500
            reasonText = "Paramter {} must be integer".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    clusterName = dataInput['clusterName']
    nodeQty = dataInput['nodeQty']
    keyPair = dataInput['keyPair']
    FlavorID = dataInput['FlavorID']

    client = MongoClient('localhost', 27017)
    db = client.bio
    cluster = db.cluster

    now = datetime.datetime.now()
    nodeList= []

    for i in range(0, nodeQty):
        nodeDict = {}
        nodeDict = {'node_id': now, 'node_name': "master Instance Group",
                            'note_type': 'MASTER' if i == 0 else 'CORE', 'node_status': 'OPEN',
                            'machine_type': 'm4.large 4 Vcore 8GiB memory EBS only storate EBS Storage: 32 GiB', 'node_create_by': 'test',
                            'node_create_time': now, 'node_update_by': 'test', 'node_update_time': now}
        nodeList.append(nodeDict)

    cluster.insert_one({'cluster_id': now, 'cluster_name': clusterName,
                        'cluster_status': 'Open', 'cluster_create_date': now,
                        'cluster_node_qty': nodeQty, 'cluster_create_by': 'test',
                        'cluster_create_time': now, 'cluster_update_by': 'test', 'cluster_update_time': now,
                        'node': nodeList})

    columns = ['isSuccess','reasonCode','reasonText']
    data = [(isSuccess,reasonCode,"Create Cluster สำเร็จ")]

    testcreate(clusterName,FlavorID)
    columns = ['isSuccess','reasonCode','reasonText']
    data = [(isSuccess,reasonCode,"Wait response from server")]
    return jsonify(toJson(data,columns))


@cluster.route("/bio/cluster/getClusterSummary", methods=['POST'])
def getClusterSummary():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['cluster_id']
    paramCheckStringList = ['cluster_id']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    clusterID = dataInput['cluster_id']

    columns = ['cluster_id','cluster_code','cluster_name','release_name','machine_type','cluster_size',
        'primary_dns','release_label','hadoop_distribution','clusterlication','loguri','description']
    data = [('j-24QRJT7QWFEC7','cluster_code','cluster_name','emr-5.11.1','machine_type','cluster_size','ec2-13-229-143.59.ap-southeast-1.computer.amazonaws.com','emr-5.11.1',
        '2.7.3','Core Hadoop:Hadoop 2.8.3 with 3.7.2,Hive 2.3.2 Hue 4.1.0 Mahout 0.13.0, Pid 0.17.0.and Tez 0.8.4','logs-201803211030455_203','description')]

    return jsonify(toJson(data,columns))


@cluster.route("/bio/cluster/getclusterlicationList", methods=['POST'])
def getclusterlicationList():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['cluster_id']
    paramCheckStringList = ['cluster_id']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    clusterID = dataInput['cluster_id']

    # columns = ['clusterlication_id','clusterid','type','action','name','starttime', 'endtime', 'duration', 'status']
    # data=[]
    #
    # for i in range(0, 20):
    #     data.append(['clusterlication_id ' + str(i),'clusterid','type','action','name','starttime', 'endtime', 'duration', 'status'])
    #
    # return jsonify(toJson(data,columns))

    client = MongoClient('localhost', 27017)
    db = client.bio
    cluster = db.cluster

    cluster_list = list(cluster.find({"cluster_id" : clusterID},{"event" : 1}))

    return json.dumps(cluster_list, sort_keys=True, indent=2, default=json_util.default)


@cluster.route("/bio/cluster/getNodeList", methods=['POST'])
def getNodeList():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['cluster_id']
    paramCheckStringList = ['cluster_id']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    clusterID = dataInput['cluster_id']

    # columns = ['node_id','status','node_name','node_type','machine_type']
    # data=[]
    #
    # for i in range(0, 50):
    #     data.append(['node_id ' + str(i),'Terminated','MASTER','Master Instance Group','m4.large 4 Vcore,8 GiB memory,EBS only storage EBS Storage: 32 GiB'])
    #
    # return jsonify(toJson(data,columns))

    client = MongoClient('localhost', 27017)
    db = client.bio
    cluster = db.cluster

    cluster_list = list(cluster.find({"cluster_id" : clusterID},{"node" : 1}))

    return json.dumps(cluster_list, sort_keys=True, indent=2, default=json_util.default)


@cluster.route("/bio/cluster/getNodeMachineList", methods=['POST'])
def getNodeMachineList():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['node_id']
    paramCheckStringList = ['node_id']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    nodeID = dataInput['node_id']

    client = MongoClient('localhost', 27017)
    db = client.bio
    cluster = db.cluster

    cluster_list = list(cluster.find({"node.node_id" : nodeID},{"node.machine" : 1}))

    return json.dumps(cluster_list, sort_keys=True, indent=2, default=json_util.default)


@cluster.route("/bio/cluster/getEventList", methods=['POST'])
def getEventList():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['cluster_id']
    paramCheckStringList = ['cluster_id']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    clusterID = dataInput['cluster_id']

    # columns = ['source_type','source_ref','event_type','event_time','severity']
    # data=[]
    #
    # for i in range(0, 50):
    #     data.append(['Amazon EMR Cluster j-YVKFYGBLL3','j-YVKFYGBLL3','Cluster','Cluster State Change','CRITICAL'])
    #
    # return jsonify(toJson(data,columns))


    client = MongoClient('localhost', 27017)
    db = client.bio
    cluster = db.cluster

    cluster_list = list(cluster.find({"cluster_id" : clusterID},{"event" : 1}))

    return json.dumps(cluster_list, sort_keys=True, indent=2, default=json_util.default)



@cluster.route("/bio/cluster/getMonitorData", methods=['POST'])
def getMonitorData():
    now = datetime.datetime.now()
    isSuccess = True
    reasonCode = 200
    reasonText = ""

    dataInput = request.json
    paramList = ['cluster_id']
    paramCheckStringList = ['cluster_id']

    for param in paramList:
        if param not in dataInput:
            isSuccess = False
            reasonCode = 500
            reasonText = "Invalid Parameter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

        if (param in paramCheckStringList and isinstance(dataInput[param], str) and len(dataInput[param])==0):
            isSuccess = False
            reasonCode = 500
            reasonText = "Please enter {}".format(param)

            columns = ['isSuccess','reasonCode','reasonText']
            data = [(isSuccess,reasonCode,reasonText)]

            return jsonify(toJson(data,columns))

    cluster = dataInput['cluster_id']

    columns = ['source_type','source_ref','event_type','event_time','severity']
    data=[]

    for i in range(0, 50):
        data.append(['Amazon EMR Cluster j-YVKFYGBLL3','j-YVKFYGBLL3','Cluster','Cluster State Change','CRITICAL'])

    return jsonify(toJson(data,columns))


@cluster.route("/getResourceMySQL", methods=['GET'])
def getResourceMySQL ():
    # dataInput = request.json
    # user = dataInput['user']

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "SELECT code,name FROM doctor"
    cursor.execute(sql)
    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    result = toJson(data,columns)
    conn.commit()
    cursor.close()

    return jsonify(result)

@cluster.route("/getResourceProc", methods=['POST'])
def getResourceProc():
    dataInput = request.json
    val = dataInput['val']

    code = (val['Code'])

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    # sql = """\
    # DECLARE @resource_no nvarchar(100);
    # EXEC sp_test_proc_post @resource_no = %s;
    # """

    # params = (code)
    # cursor.execute(sql,params)

    # cursor.callproc('sp_test_proc_post',  ('01%',))

    # for row in cursor:
    #     print(row)

    # params = {'resource_no': code,'uom': "EA"}
    # cursor.execute("EXEC sp_test_proc_post %(uom)s, %(resource_no)s", params)

    sql = """\
    DECLARE @resource_no nvarchar(100),
    @uom nvarchar(100);
    EXEC sp_test_proc_post @uom = %(uom)s,@resource_no = %(resource_no)s;
    """
    params = {'resource_no': code,'uom': "EA"}
    cursor.execute(sql,params)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    result = toJson(data,columns)

    conn.commit()
    cursor.close()

    return jsonify(result)

@cluster.route("/getResource", methods=['POST'])
def getResource():
    dataInput = request.json
    val = dataInput['val']

    code = (val['Code'])

    conn = pymssql.connect(mssql_server,mssql_user,mssql_password,mssql_database)
    cursor = conn.cursor()
    sql = "SELECT resource_no,description FROM resource where resource_no like %s"
    cursor.execute(sql,code)

    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    result = toJson(data,columns)

    conn.commit()
    cursor.close()

    return jsonify(result)

@cluster.route("/getDoctor", methods=['POST'])
def getDoctor ():
    dataInput = request.json
    val = dataInput['val']

    code = (val['Code'])

    print(val)

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "SELECT code,name FROM doctor where code = %s"
    cursor.execute(sql,code)
    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    result = toJson(data,columns)
    conn.commit()
    cursor.close()

    return jsonify(result)
