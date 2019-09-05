# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
import json
import time
import re
import hashlib


#/python/user_list req_data { "action":"findData", "limit":10, "page":1, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据
#/python/user_list req_data { "action":"insertData", "dataArr":[{"username":"peter","password":"123456","name":"匿名","email":"15331650@qq.com","phone":"16675199666","sex":"男","age":18,"role_id":1}], "tocken": "eb2xlX2lkIj4gphmei4" }  //插入数据
#/python/user_list req_data { "action":"updateData", "whereJson":{"username":"peter"}, "updateJson":{"name":"xx"}, "tocken": "eb2xlX2lkIj4gphmei4" }  //修改数据
#/python/user_list req_data { "action":"delData", whereJson={"username":["peter"]}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //删除数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'user_list'
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
        params['fieldJson'] = params['fieldJson'] if 'fieldJson' in params else {}
        params['fieldJson']['user_list.id'] = 1
        params['fieldJson']['user_list.username'] = 1
        params['fieldJson']['user_list.name'] = 1
        params['fieldJson']['user_list.email'] = 1
        params['fieldJson']['user_list.phone'] = 1
        params['fieldJson']['user_list.sex'] = 1
        params['fieldJson']['user_list.age'] = 1
        params['fieldJson']['user_list.message'] = 1
        params['fieldJson']['user_list.role_id'] = 1
        params['fieldJson']['role_class.class_name'] = 1
        self.table_name = 'user_list LEFT JOIN role_class ON user_list.role_id = role_class.id'
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
        list_username = []
        for item in list_data:
            if re.search(r'^\w*$', item['username']) and len(item['password']) >= 6:
                password = "pw" + item['password'] + item['password'][0:3]
                md5 = hashlib.md5()
                md5.update(password.encode(encoding='utf-8'))
                md5_password = md5.hexdigest()
                item['password'] = md5_password
                item['username'] = item['username'].lower()
                list_username.append(item['username'])
            else:
                dict_res = {'code': 500, 'msg': '用户名或密码格式错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            if 'role_id' not in item or type(item['role_id']) != int:
                dict_res = {'code': 500, 'msg': 'role_id错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

            item['create_name'] = self.req.dict_tocken['username']
            item['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            item['update_name'] = ''
            item['update_time'] = ''

        params = { 'whereJson':{ 'username': {'$in':list_username} }, 'fieldJson':{ 'id': 1, 'username': 1 } }
        result = self.mysqldb.find_data(self.table_name, params)
        if result['count'] != 0:
            dict_res = {'code': 200, 'msg': '用户名已存在'}
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
        if 'id' in self.req.dict_req['updateJson']:
            dict_res = {'code': 500, 'msg': '禁止修改id'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'username' in self.req.dict_req['updateJson']:
            dict_res = {'code': 500, 'msg': '禁止修改username'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        whereJson = self.req.dict_req['whereJson']
        updateJson = self.req.dict_req['updateJson']
        if 'password' in updateJson:
            if len(updateJson['password']) >= 6:
                password = "pw" + updateJson['password'] + updateJson['password'][0:3]
                md5 = hashlib.md5()
                md5.update(password.encode(encoding='utf-8'))
                md5_password = md5.hexdigest()
                updateJson['password'] = md5_password
            else:
                dict_res = {'code': 500, 'msg': '密码格式错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

        updateJson['update_name'] = self.req.dict_tocken['username']
        updateJson['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
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
