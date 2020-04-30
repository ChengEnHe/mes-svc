#!flask/bin/
# -*- coding: utf-8 -*-
from flask import Flask
from flask import jsonify
from flask import request
from datetime import datetime
import cx_Oracle
import pymongo
import json
import os 

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8' 
dbType = 'orcl'
if "db-type" in os.environ:
  dbType = os.environ["db-type"]
ip='10.70.1.31'
if "db-addr" in os.environ:
  ip = os.environ["db-addr"]
port=1521
if "db-port" in os.environ:
  ip = os.environ["db-port"]
SID='xe'
if "db-name" in os.environ:
  SID = os.environ["db-name"]
acc = 'system'
if "db-acc" in os.environ:
  acc = os.environ["db-acc"]
pwd = 'oracle'
if "db-pwd" in os.environ:
  pwd = os.environ["db-pwd"]
dsn_tns = cx_Oracle.makedsn(ip, port, SID)
mongoUrl = 'mongodb://admin:gemtek123@mongodb:27017/argi_dev'
if "mongo-url" in os.environ:
  mongoUrl = os.environ["mongo-url"]
mongoDb = 'argi_dev'
if "mongo-db" in os.environ:
  mongoDb = os.environ["mongo-db"]
app = Flask(__name__)

@app.route('/')
def index():
    return "This is a microservice for mes"

@app.route('/<dbType>/cnt/<schema>/<tbl>', methods=['GET'])
def get_tblCnt(dbType, schema, tbl):
    payload = {}
    if not checkDbType(dbType):
        payload['responseCode'] = '401'
        payload['responseMsg'] = 'db type access error'
        return jsonify(payload)
    db=cx_Oracle.connect(acc, pwd, dsn_tns)
    cr=db.cursor()
    errorFlg = False
    sql='select count(*) as Cnt from '+schema+'.'+tbl
    try:
        cr.execute(sql)
        rs=cr.fetchall()  
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        if error.code == 942:
            payload['responseMsg'] = 'table or view does not exist'
        else:
            payload['responseMsg'] = 'db access error, error code:'+error.code
        payload['responseCode'] = '500'
        errorFlg = True
    finally:
        cr.close()
        db.close()
    if not errorFlg:
        ans = rsToList(rs)
        payload['responseCode'] = '000'
        payload['responseMsg'] = 'query success'
        payload['size'] = ans[0][0]
    payload['schema'] = schema
    payload['tbl'] = tbl
    return jsonify(payload)

@app.route('/<dbType>/<schema>/<tbl>', methods=['POST'])
def insert_tblData(dbType, schema, tbl):
    payload = {}
    if not checkDbType(dbType):
        payload['responseCode'] = '401'
        payload['responseMsg'] = 'db type access error'
        return jsonify(payload)
    if tbl.upper() == 'CIM100ROLA01':
        if not request.json or not 'tagId' in request.json:
            payload['responseCode'] = '404'
            payload['responseMsg'] = 'tagId does not exist'
            return jsonify(payload)
        in_d = datetime.strptime(request.json['in_ts'], '%Y-%m-%d %H:%M:%S')
        params = (request.json['tagId'], request.json['macAddr'], request.json.get('macAddr_name', "").encode('utf-8'), request.json['factory_val'], request.json.get('factory_name', "").encode('utf-8'), request.json['zone_val'], request.json.get('zone_name', "").encode('utf-8'), request.json['station_val'], request.json.get('station_name', "").encode('utf-8'), in_d, request.json['out_ts'], request.json['weight'])
        sql = 'insert into '+schema+'.'+tbl+'(tagId, macAddr, macAddr_name, factory_val, factory_name, zone_val, zone_name, station_val, station_name, in_ts, out_ts, weight) values (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12)'
        payload = insertUpdateData(sql, params, True)
    elif tbl.upper() == 'SFC901M':
        if not request.json or not 'tagId' in request.json:
            payload['responseCode'] = '404'
            payload['responseMsg'] = 'tagId does not exist'
            return jsonify(payload)
        in_d = datetime.strptime(request.json['in_ts'], '%Y-%m-%d %H:%M:%S')
        in_type = request.json['type']
        if in_type == 'mac':
            if not 'weight' in request.json:
                params = (request.json['tagId'], request.json['macAddr'], request.json['eid'], in_d, request.json['order'])
                sql = 'insert into '+schema+'.'+tbl+'(seqno, mac_no, cre_user, cre_date, barcode) values (:1, :2, :3, :4, :5)'
                payload = insertUpdateData(sql, params, True)
            else:
                params = (request.json['tagId'], request.json['macAddr'], request.json['eid'], in_d, request.json['order'], request.json['weight'])
                sql = 'insert into '+schema+'.'+tbl+'(seqno, mac_no, cre_user, cre_date, barcode, wt) values (:1, :2, :3, :4, :5, :6)'
                payload = insertUpdateData(sql, params, True)
        elif in_type == 'loc':
            if not 'weight' in request.json:
                params = (request.json['tagId'], request.json['macAddr'], request.json['eid'], in_d, request.json['order'])
                sql = 'insert into '+schema+'.'+tbl+'(seqno, loc_no, cre_user, cre_date, barcode) values (:1, :2, :3, :4, :5)'
                payload = insertUpdateData(sql, params, True)
            else:
                params = (request.json['tagId'], request.json['macAddr'], request.json['eid'], in_d, request.json['order'], request.json['weight'])
                sql = 'insert into '+schema+'.'+tbl+'(seqno, loc_no, cre_user, cre_date, barcode, wt) values (:1, :2, :3, :4, :5, :6)'
                payload = insertUpdateData(sql, params, True)
        else:
            payload['responseCode'] = '404'
            payload['responseMsg'] = 'unknown type'
            return jsonify(payload)
    else:
      payload['resposeCode'] = '404'
      payload['responseMsg'] = 'tbl not define'
    return jsonify(payload)
@app.route('/<dbType>/<schema>/<tbl>', methods=['PUT'])
def update_tblData(dbType, schema, tbl):
    payload = {}
    if not checkDbType(dbType):
        payload['responseCode'] = '401'
        payload['responseMsg'] = 'db type access error'
        return jsonify(payload)
    if tbl.upper() == 'CIM100ROLA01':
        if not request.json or not 'tagId' in request.json:
            payload['responseCode'] = '404'
            payload['responseMsg'] = 'tagId does not exist'
            return jsonify(payload)
        outFlg = False
        wFlg = False
        updateFlg = False
        if 'out_ts' in request.json and len(request.json['out_ts']) > 0:
            out_d = datetime.strptime(request.json['out_ts'], '%Y-%m-%d %H:%M:%S')
            outFlg = True
        if 'weight' in request.json and len(request.json['weight']) > 0:
            weight = request.json['weight']
            wFlg = True
        if not outFlg and not wFlg:
            payload['resposeCode'] = '404'
            payload['responseMsg'] = 'update field not define'
        else:
            updateFlg = True
        if updateFlg:
            sql = 'update ' +schema+'.'+tbl+' set '
            params = {}
            if outFlg:
                params['out_d'] = out_d
                sql += 'out_ts = :out_d '
                if wFlg:
                    params['weight'] = weight
                    sql += ', weight = :weight '
            else:
                if wFlg:
                    params['weight'] = weight
                    sql += 'weight = :weight '
            params['tagId'] = request.json['tagId']
            sql += ' where tagId = :tagId '
            payload = insertUpdateData(sql, params, False)
    else:
      payload['resposeCode'] = '404'
      payload['responseMsg'] = 'tbl not define'
    return jsonify(payload)
@app.route('/check/<collection>', methods=['DELETE'])
def delete_cehckData(collection):
    payload = {}
    if collection.upper() == 'CHECKTAGINFO':
      client = pymongo.MongoClient(mongoUrl)
      db = client[mongoDb]
      targetCollection = db[collection]
      if not request.json or not 'barCode' in request.json:
        payload['responseCode'] = '404'
        payload['responseMsg'] = 'request parameter error'
        return jsonify(payload)
      condition = {}
      condition['order'] = request.json['barCode']
      result = targetCollection.delete_many(condition)
      payload['resposeCode'] = '000'
      payload['responseMsg'] = 'delete success'
      payload['size'] = result.deleted_count
      return jsonify(payload)
    else:
      payload['resposeCode'] = '404'
      payload['responseMsg'] = 'collection not define'
    return jsonify(payload)
@app.route('/check/<collection>', methods=['POST'])
def insert_cehckData(collection):
    payload = {}
    if collection.upper() == 'CHECKTAGINFO':
      client = pymongo.MongoClient(mongoUrl)
      db = client[mongoDb]
      targetCollection = db[collection]
      if not request.json or not 'seqNo' in request.json or not 'barCode' in request.json or not 'locCode' in request.json:
        payload['responseCode'] = '404'
        payload['responseMsg'] = 'request parameter error'
        return jsonify(payload)
      checkCount = targetCollection.find({'_id':request.json['seqNo']}).count()
      if checkCount > 0:
        payload['responseCode'] = '500'
        payload['responseMsg'] = 'seqNo [' + request.json['seqNo'] + '] already exist'
        return jsonify(payload)
      checkData = {}
      checkData['_id'] = request.json['seqNo']
      checkData['order'] = request.json['barCode']
      checkData['loc_code'] = request.json['locCode']
      checkData['proc_desc'] = request.json.get('procDesc', "")
      checkData['remark'] = request.json.get('remark', "")
      now = datetime.now()
      checkData['createTime'] = now
      result = targetCollection.insert_one(checkData)
      if result.inserted_id == request.json['seqNo']:
        payload['resposeCode'] = '000'
        payload['responseMsg'] = 'insert success'
        return jsonify(payload)
      else:
        payload['resposeCode'] = '500'
        payload['responseMsg'] = 'insert fail'
        return jsonify(payload)
    else:
      payload['resposeCode'] = '404'
      payload['responseMsg'] = 'collection not define'
    return jsonify(payload)
def insertUpdateData(sql, params, isNew):
    payload = {}
    errorFlg = False
    db=cx_Oracle.connect(acc, pwd, dsn_tns)
    cr = db.cursor()
    actionResult = ''
    try:
        cr.execute(sql, params)
        db.commit()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        if error.code == 942:
            payload['responseMsg'] = 'table or view does not exist'
        else:
            payload['responseMsg'] = error.message
        payload['responseCode'] = error.code
        payload['sql'] = sql
        payload['params'] = params
        errorFlg = True
    finally:
        cr.close()
        db.close()
    if not errorFlg:
        if cr.rowcount >= 1:
            payload['responseCode'] = '000'
            if isNew:
                payload['responseMsg'] = 'insert success'
            else:
                payload['responseMsg'] = 'update success'
        else:
            payload['responseCode'] = '500'
            if isNew:
                payload['responseMsg'] = 'insert fail'
            else:
                payload['responseMsg'] = 'update fail'
    return payload
def rsToList(rs):
    queryAnsList = []
    for ansItem in rs:
        queryAnsList.append(list(ansItem))
    return queryAnsList
def checkDbType(passType):
    if passType != dbType:
        return False
    else:
        return True
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
