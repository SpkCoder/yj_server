# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
import json
import time
import re


#/python/power_list req_data { "action":"findData", "whereJson":{"role_id":1}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据
#/python/power_list req_data { "action":"updateData", "whereJson":{"role_id":1}, "updateJson":{"fn_id":[1,2,3]}, "tocken": "eb2xlX2lkIj4gphmei4" }  //修改数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'power_list'
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
        params['limit'] = -1
        params['page'] = 1
        params['whereJson'] = params['whereJson'] if 'whereJson' in params else {}
        if 'role_id' not in params['whereJson']:
            dict_res = {'code': 500, 'msg': 'miss role_id'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        result = self.mysqldb.find_data(self.table_name, params)
        # print(result)

        if result:
            list_fn_id = []
            for item in result['rows']:
                list_fn_id.append(item['fn_id'])
            # 查询menu
            sql = 'select model_list.id,model_list.name,model_list.level,model_list.parentId,model_list.sort,model_list.show,model_list_fn.id as fn_id,model_list_fn.function_ch from model_list left join model_list_fn on model_list.id = model_list_fn.model_id where `show` = "true" order by level asc, sort asc'
            result2 = self.mysqldb.find_data(self.table_name, params, sql)
            if result2:
                list_rows = []
                for item in result2['rows']:
                    # item['children'] = []
                    if item['level'] == 1:
                        list_rows.append({'id': item['id'], 'name': item['name'], 'children': []})
                    elif item['level'] == 2:
                        for item2 in list_rows:
                            if item['parentId'] == item2['id']:
                                if item['fn_id'] in list_fn_id:
                                    item['checked'] = 'true'
                                else:
                                    item['checked'] = 'false'
                                item2['children'].append({'id': item['fn_id'], 'name': item['name']+'-'+item['function_ch'], 'checked': item['checked'], 'children': []})
                    else:
                        pass
            for item in list_rows:
                item['checked'] = 'false'
                for item2 in item['children']:
                    if item2['checked'] == 'true':
                        item['checked'] = 'true'
                        break

            dict_res = {'code': 200, 'msg': '操作成功', 'rows': list_rows}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))


    # 修改数据
    def update_data(self):
        params = self.req.dict_req
        params['whereJson'] = params['whereJson'] if 'whereJson' in params else {}
        params['updateJson'] = params['updateJson'] if 'updateJson' in params else {}
        if 'role_id' not in params['whereJson']:
            dict_res = {'code': 500, 'msg': 'miss role_id'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'fn_id' not in params['updateJson']:
            dict_res = {'code': 500, 'msg': 'miss fn_id'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        list_data = []
        for item in params['updateJson']['fn_id']:
            list_data.append({'role_id': params['whereJson']['role_id'], 'fn_id': item})

        #先删除再插入
        result = self.mysqldb.del_data(self.table_name, {"role_id": [ params['whereJson']['role_id'] ]})
        if len(list_data) > 0:
            result = self.mysqldb.insert_data(self.table_name, list_data)
        # print(result)

        if result:
            dict_res = {'code': 200, 'msg': '操作成功'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
