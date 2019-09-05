# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
import json
import time
import re
from datetime import datetime


#/python/alarm_list req_data { "action":"findData", "whereJson":{"status": 1}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据
#/python/alarm_list req_data { "action":"updateData", "whereJson":{"status": 1, "client_ip": "192.168.200.197", "alarm_type_id": 6}, "updateJson":{"status":0}, "tocken": "eb2xlX2lkIj4gphmei4" }  //修改数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'alarm_list'
        self.mysqldb = db_mysql.model()

    # 分配方法
    def actions(self):
        # GET请求
        if self.req.method == 'GET':

            # 判断权限
            if not self.mysqldb.get_power(self.req.dict_tocken['role_id'], self.table_name, self.req.dict_req['action']):
                dict_res = {'code': 500, 'msg': '没有权限'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

            if self.req.dict_req['action'] == 'findData':
                return self.find_data()
            else:
                dict_res = {'code': 500, 'msg': 'action错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

        # POST请求
        elif self.req.method == 'POST':

            # 判断权限
            if not self.mysqldb.get_power(self.req.dict_tocken['role_id'], self.table_name, self.req.dict_req['action']):
                dict_res = {'code': 500, 'msg': '没有权限'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            if self.req.dict_req['action'] == 'updateData':
                return self.update_data()
            else:
                dict_res = {'code': 500, 'msg': 'action错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

        else:
            dict_res = {'code': 500, 'msg': 'method错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))


    # 查询数据
    def find_data(self):
        params = self.req.dict_req
        params['limit'] = int(params['limit']) if 'limit' in params else 10
        params['page'] = int(params['page']) if 'page' in params else 1
        params['offset'] = params['limit'] * (int(params['page']) - 1) if 'page' in params else 0
        params['whereJson'] = params['whereJson'] if 'whereJson' in params else {}
        params['fieldJson'] = params['fieldJson'] if 'fieldJson' in params else {}

        if 'status' in params['whereJson'] and 'group' in params['whereJson']:
            params['whereJson']['alarm_list.status'] = params['whereJson']['status']
            del params['whereJson']['status']
            del params['whereJson']['group']
            whereStr = ' where '+self.mysqldb.get_whereStr(params)
            sortStr = ' order by alarm_time desc'
            sql = 'select alarm_list.client_ip, alarm_list.alarm_type_id, min(alarm_list.alarm_time) as first_alarm_time, max(alarm_list.alarm_time) as last_alarm_time, alarm_list.alarm_msg, alarm_list.status, alarm_type_list.alarm_type from alarm_list left join alarm_type_list on alarm_list.alarm_type_id = alarm_type_list.id'+whereStr+' group by client_ip, alarm_type_id'+sortStr+' limit '+str(params['offset'])+','+str(params['limit'])
            sql_count = 'select count(*) as number from (select count(*) as number from alarm_list'+whereStr+' group by client_ip, alarm_type_id) t2'
            result = self.mysqldb.find_data(self.table_name, params, sql, sql_count)
        else:
            params['whereJson']['alarm_list.status'] = params['whereJson']['status']
            del params['whereJson']['status']
            params['fieldJson']['alarm_list.id'] = 1
            params['fieldJson']['alarm_list.client_ip'] = 1
            params['fieldJson']['alarm_list.alarm_type_id'] = 1
            params['fieldJson']['alarm_list.alarm_time'] = 1
            params['fieldJson']['alarm_list.alarm_msg'] = 1
            params['fieldJson']['alarm_list.status'] = 1
            params['fieldJson']['alarm_type_list.alarm_type'] = 1
            self.table_name = 'alarm_list LEFT JOIN alarm_type_list ON alarm_list.alarm_type_id = alarm_type_list.id'
            result = self.mysqldb.find_data(self.table_name, params)

        # print(result)
        if result:
            dict_res = {'code': 200, 'msg': '操作成功', 'limit': params['limit'], 'page': params['page'], 'count': result['count'], 'rows': result['rows']}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

    # 修改数据
    def update_data(self):
        if 'whereJson' not in self.req.dict_req:
            dict_res = {'code': 500, 'msg': 'miss whereJson'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'updateJson' not in self.req.dict_req:
            dict_res = {'code': 500, 'msg': 'miss updateJson'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        whereJson = self.req.dict_req['whereJson']
        updateJson = self.req.dict_req['updateJson']
        result = self.mysqldb.update_data(self.table_name, whereJson, updateJson)
        # print(result)

        if result:
            dict_res = {'code': 200, 'msg': '操作成功'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))