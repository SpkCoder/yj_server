# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
import json
import time
import re


#/python/email_user_list req_data { "action":"findData", "limit":10, "page":1, "whereJson":{}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据
#/python/email_user_list req_data { "action":"insertData", "dataArr":[{"class_name":"超级用户"}], "tocken": "eb2xlX2lkIj4gphmei4" }  //插入数据
#/python/email_user_list req_data { "action":"updateData", "whereJson":{"id":"1"}, "updateJson":{"class_name":"超级用户"}, "tocken": "eb2xlX2lkIj4gphmei4" }  //修改数据
#/python/email_user_list req_data { "action":"delData", whereJson={"id":[1,3]}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //删除数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'email_user_list'
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
            if self.req.dict_req['action'] == 'insertData':
                return self.insert_data()
            elif self.req.dict_req['action'] == 'updateData':
                return self.update_data()
            elif self.req.dict_req['action'] == 'delData':
                return self.del_data()
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
        result = self.mysqldb.find_data(self.table_name, params)
        # print(result)

        if result:
            dict_res = {'code': 200, 'msg': '操作成功', 'limit': params['limit'], 'page': params['page'], 'count': result['count'], 'rows': result['rows']}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))


    # 插入数据
    def insert_data(self):
        if 'dataArr' not in self.req.dict_req:
            dict_res = {'code': 500, 'msg': 'miss dataArr'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if type(self.req.dict_req['dataArr']) != list or len(self.req.dict_req['dataArr']) == 0:
            dict_res = {'code': 500, 'msg': 'dataArr错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        list_data = self.req.dict_req['dataArr']
        for item in list_data:
            if 'email' not in item or item['email'] == '':
                dict_res = {'code': 500, 'msg': 'email错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

        result = self.mysqldb.insert_data(self.table_name, list_data)
        # print(result)

        if result:
            dict_res = {'code': 200, 'msg': '操作成功'}
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


    # 删除数据
    def del_data(self):
        if 'whereJson' not in self.req.dict_req:
            dict_res = {'code': 500, 'msg': 'miss whereJson'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        whereJson = self.req.dict_req['whereJson']
        result = self.mysqldb.del_data(self.table_name, whereJson)
        # print(result)

        if result:
            dict_res = {'code': 200, 'msg': '操作成功'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

