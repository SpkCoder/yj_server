# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
from flaskApp.modules import my_csv
import json
import time
import re
import os


#/python/operation_list req_data { "action":"findData", "limit":10, "page":1, "whereJson":{}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'operation_list'
        self.mysqldb = db_mysql.model()

    # 分配方法
    def actions(self):
        # GET请求
        if self.req.method == 'GET':

            str_action = self.req.dict_req['action']
            if str_action == 'exportData':
                str_action = 'findData'
            # 判断权限
            if not self.mysqldb.get_power(self.req.dict_tocken['role_id'], self.table_name, str_action):
                dict_res = {'code': 500, 'msg': '没有权限'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

            if self.req.dict_req['action'] == 'findData':
                return self.find_data()
            elif self.req.dict_req['action'] == 'exportData':
                return self.export_data()
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
        params['fieldJson'] = params['fieldJson'] if 'fieldJson' in params else {}
        params['fieldJson']['operation_list.id'] = 1
        params['fieldJson']['operation_list.username'] = 1
        params['fieldJson']['operation_list.client_ip'] = 1
        params['fieldJson']['operation_list.operation_type'] = 1
        params['fieldJson']['operation_list.operation_msg'] = 1
        params['fieldJson']['operation_list.log_time'] = 1
        params['fieldJson']['device_list.name'] = 1
        self.table_name = 'operation_list LEFT JOIN device_list ON operation_list.client_ip = device_list.ip'
        result = self.mysqldb.find_data(self.table_name, params)
        # print(result)

        if result:
            dict_res = {'code': 200, 'msg': '操作成功', 'limit': params['limit'], 'page': params['page'], 'count': result['count'], 'rows': result['rows']}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))


    # 导出数据
    def export_data(self):
        params = self.req.dict_req
        params['limit'] = int(params['limit']) if 'limit' in params else 10
        params['page'] = int(params['page']) if 'page' in params else 1
        result = self.mysqldb.find_data(self.table_name, params)
        # print(result)
        if result:
            file_path = os.path.dirname(os.path.dirname(__file__)) + '/static/uploadFile/'+ self.table_name +'_export.csv'
            list_title = ['用户', '设备IP', '操作类型', '操作信息', '时间']
            list_title_en = ['username', 'client_ip', 'operation_type', 'operation_msg', 'log_time']
            mycsv = my_csv.model()
            result = mycsv.write(file_path,list_title,list_title_en,result['rows'])
            str_url = result['url']
            str_url = '/uploadFile' + str_url[str_url.rindex('/'):]
            dict_res = {'code': 200, 'msg': '操作成功', 'url': str_url}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))