# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
from flaskApp.modules import my_csv
import json
import time
import re
import os
from datetime import datetime


#/python/top_list req_data { "action":"findData", "whereJson":{"type": "host"}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'top_list'
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
        params['offset'] = params['limit'] * (int(params['page']) - 1) if 'page' in params else 0
        params['sortJson'] = params['sortJson'] if 'sortJson' in params else {}
        if 'whereJson' not in params:
            dict_res = {'code': 500, 'msg': 'miss whereJson'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'type' not in params['whereJson']:
            dict_res = {'code': 500, 'msg': 'whereJson错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        sortStr = ' order by num desc'
        if params['sortJson']:
            if 'err_rate' in params['sortJson']:
                pass
            else:
                sortStr = ' order by ' + self.mysqldb.get_sortStr(params)
        whereStr = ''
        if params['whereJson']['type'] == 'host':
            del params['whereJson']['type']
            if len(params['whereJson']) > 0:
                whereStr = ' where '+self.mysqldb.get_whereStr(params)
            sql = 'select t1.client_host, t1.num, t2.num_err from (select client_host, count(*) as num from dns_req_list'+whereStr+' group by client_host) t1 left join (select client_host, count(*) as num_err from dns_err_list where req_status = "SERVFAIL" group by client_host) t2 on t1.client_host=t2.client_host'+sortStr+' limit '+str(params['offset'])+','+str(params['limit'])
            sql_count = 'select count(*) as number from (select count(*) as number from dns_req_list'+whereStr+' group by client_host) gyd'
        else:
            del params['whereJson']['type']
            if len(params['whereJson']) > 0:
                whereStr = ' where '+self.mysqldb.get_whereStr(params)
            sql = 'select t3.client_ip, t3.num_host, t3.num, t2.num_err from (select t1.client_ip, count(*) as num_host, cast(sum(t1.num_host) as signed) as num from (select client_ip, client_host, count(*) as num_host from dns_req_list'+whereStr+' group by client_ip, client_host) t1 group by t1.client_ip) t3 left join (select client_ip, count(*) as num_err from dns_err_list where req_status = "SERVFAIL" group by client_ip) t2 on t3.client_ip=t2.client_ip'+sortStr+' limit '+str(params['offset'])+','+str(params['limit'])
            sql_count = 'select count(*) as number from (select t.client_ip, count(*) as num_host, sum(t.num_host) as num from (select client_ip, client_host, count(*) as num_host from dns_req_list'+whereStr+' group by client_ip, client_host) t group by t.client_ip) gyd'
        result = self.mysqldb.find_data(self.table_name, params, sql, sql_count)
        # print(result)

        if result:
            for item in result['rows']:
                item['num_err'] = item['num_err'] if item['num_err'] else 0
                item['err_rate'] = round(item['num_err']/item['num'],2)
            if 'err_rate' in params['sortJson']:
                if params['sortJson']['err_rate'] > 0:
                    result['rows']=sorted(result['rows'],key=lambda x:x['err_rate'])
                else:
                    result['rows']=sorted(result['rows'],key=lambda x:x['err_rate'],reverse=True)
            if result['count'] > 100:
                result['count'] = 100
                result['rows'] = result['rows'][:100]
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
        params['offset'] = params['limit'] * (int(params['page']) - 1) if 'page' in params else 0
        params['sortJson'] = params['sortJson'] if 'sortJson' in params else {}
        if 'whereJson' not in params:
            dict_res = {'code': 500, 'msg': 'miss whereJson'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'type' not in params['whereJson']:
            dict_res = {'code': 500, 'msg': 'whereJson错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        sortStr = ' order by num desc'
        whereStr = ''
        if params['whereJson']['type'] == 'host':
            del params['whereJson']['type']
            if len(params['whereJson']) > 0:
                whereStr = ' where '+self.mysqldb.get_whereStr(params)
            sql = 'select t1.client_host, t1.num, t2.num_err from (select client_host, count(*) as num from dns_req_list'+whereStr+' group by client_host) t1 left join (select client_host, count(*) as num_err from dns_err_list where req_status = "SERVFAIL" group by client_host) t2 on t1.client_host=t2.client_host'+sortStr+' limit '+str(params['offset'])+','+str(params['limit'])
            sql_count = 'select count(*) as number from (select count(*) as number from dns_req_list'+whereStr+' group by client_host) gyd'
            list_title = ['域名', 'NDS查询次数', '错误次数', '错误率']
            list_title_en = ['client_host', 'num', 'num_err', 'err_rate']
        else:
            del params['whereJson']['type']
            if len(params['whereJson']) > 0:
                whereStr = ' where '+self.mysqldb.get_whereStr(params)
            sql = 'select t3.client_ip, t3.num_host, t3.num, t2.num_err from (select t1.client_ip, count(*) as num_host, cast(sum(t1.num_host) as signed) as num from (select client_ip, client_host, count(*) as num_host from dns_req_list'+whereStr+' group by client_ip, client_host) t1 group by t1.client_ip) t3 left join (select client_ip, count(*) as num_err from dns_err_list where req_status = "SERVFAIL" group by client_ip) t2 on t3.client_ip=t2.client_ip'+sortStr+' limit '+str(params['offset'])+','+str(params['limit'])
            sql_count = 'select count(*) as number from (select t.client_ip, count(*) as num_host, sum(t.num_host) as num from (select client_ip, client_host, count(*) as num_host from dns_req_list'+whereStr+' group by client_ip, client_host) t group by t.client_ip) gyd'
            list_title = ['客户端IP', '解析次数', '请求域名次数', '错误次数', '错误率']
            list_title_en = ['client_ip', 'num', 'num_host', 'num_err', 'err_rate']
        result = self.mysqldb.find_data(self.table_name, params, sql, sql_count)
        # print(result)
        if result:
            for item in result['rows']:
                item['num_err'] = item['num_err'] if item['num_err'] else 0
                item['err_rate'] = str(int(item['num_err']/item['num']))+'%'
            if result['count'] > 100:
                result['count'] = 100
                result['rows'] = result['rows'][:100]
            file_path = os.path.dirname(os.path.dirname(__file__)) + '/static/uploadFile/'+ self.table_name +'_export.csv'
            # list_title = []
            # list_title_en = []
            mycsv = my_csv.model()
            result = mycsv.write(file_path,list_title,list_title_en,result['rows'])
            str_url = result['url']
            str_url = '/uploadFile' + str_url[str_url.rindex('/'):]
            dict_res = {'code': 200, 'msg': '操作成功', 'url': str_url}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))