# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
import json
import time
import re
from datetime import datetime


#/python/client_type_list req_data { "action":"findData", "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'client_type_list'
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

        else:
            dict_res = {'code': 500, 'msg': 'method错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))


    # 查询数据
    def find_data(self):
        params = self.req.dict_req
        sql = 'select os_type, count(*) as num from client_type_list group by os_type order by num desc'
        result = self.mysqldb.find_data(self.table_name, params, sql)
        # print(result)

        if result:
            result['os_type'] = []
            result['os_type_num'] = []
            for item in result['rows']:
                if item['os_type'] not in result['os_type']:
                    result['os_type'].append(item['os_type'])
                    result['os_type_num'].append(item['num'])
            sum_ALL = sum(result['os_type_num'])
            result['rate'] = []
            for i, item in enumerate(result['os_type']):
                result['rate'].append(round(result['os_type_num'][i]/sum_ALL, 2))
            del result['count']
            del result['rows']
            del result['os_type_num']
            dict_res = {'code': 200, 'msg': '操作成功', 'info': result}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
