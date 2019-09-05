# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
import json


#/python/menu req_data {"action": "findData"}  //查询数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'model_list'
        self.mysqldb = db_mysql.model()

    # 分配方法
    def actions(self):
        # GET请求
        if self.req.method == 'GET':
            if self.req.dict_req['action'] == 'findData':
                return self.find_data()
            else:
                dict_res = {'code': 500, 'msg': 'action错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

        # POST请求
        else:
            dict_res = {'code': 500, 'msg': 'method错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

    # 查询数据
    def find_data(self):
        params = {
            "limit":100000,
            "page":1,
            "fieldJson":{"id": 1,"name": 1,"level": 1,"parentId": 1,"sort": 1,"href": 1,"show": 1},
            'whereJson':{"`show`": 'true'},
            "sortJson":{"level": 1, "sort": 1},
        }
        result = self.mysqldb.find_data(self.table_name, params)
        # print(json.dumps(result, ensure_ascii=False))

        if result:
            list_rows = []
            for item in result['rows']:
                item['children'] = []
                if item['level'] == 1:
                    list_rows.append(item)
                elif item['level'] == 2:
                    for item2 in list_rows:
                        if item['parentId'] == item2['id']:
                            item2['children'].append(item)
                else:
                    pass
            dict_res = {'code': 200, 'msg': '操作成功', 'rows': list_rows}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败', 'rows': []}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
