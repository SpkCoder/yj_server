# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
from flaskApp.modules import my_csv
import json
import time
import re
import os
from datetime import datetime


#/python/dns_req_list req_data { "action":"findData", "whereJson":{"time": "2019-07-13"}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'dns_req_list'
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


    # 查询数据
    def find_data(self):
        params = self.req.dict_req
        params['limit'] = int(params['limit']) if 'limit' in params else 10
        params['page'] = int(params['page']) if 'page' in params else 1
        params['whereJson'] = params['whereJson'] if 'whereJson' in params else {}

        # 下钻
        if 'create_time' in params['whereJson']:
            if 'client_ip' in params['whereJson']:
                params['whereJson']['server_ip'] = params['whereJson']['client_ip']
                del params['whereJson']['client_ip']
            if params['whereJson']['type'] == '1H':
                params['whereJson']['date_format(log_time,"%Y-%m-%d %H:00:00")'] = params['whereJson']['create_time']
                del params['whereJson']['create_time']
            if params['whereJson']['type'] == '1M':
                params['whereJson']['date_format(log_time,"%Y-%m-%d %H:%i:00")'] = params['whereJson']['create_time']
                del params['whereJson']['create_time']
            del params['whereJson']['type']
            result = self.mysqldb.find_data(self.table_name, params)
            # print(result)

            if result:
                dict_res = {'code': 200, 'msg': '操作成功', 'limit': params['limit'], 'page': params['page'], 'count': result['count'], 'rows': result['rows']}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            else:
                dict_res = {'code': 500, 'msg': '操作失败'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

        if 'time_start' not in params['whereJson'] or 'time_end' not in params['whereJson'] or 'type' not in params['whereJson']:
            dict_res = {'code': 500, 'msg': 'whereJson错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if params['whereJson']['time_start'] == '' or params['whereJson']['time_end'] == '':
            dict_res = {'code': 500, 'msg': 'whereJson错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        str_gte = params['whereJson']['time_start']
        str_lt = params['whereJson']['time_end']
        if params['whereJson']['type'] == '1H':
            time_interval = 3600
            str_gte = params['whereJson']['time_start'][:13] + ':00:00'
            str_lt = params['whereJson']['time_end'][:13] + ':00:00'
        elif params['whereJson']['type'] == '1M':
            time_interval = 60
            str_gte = params['whereJson']['time_start'][:16] + ':00'
            str_lt = params['whereJson']['time_end'][:16] + ':00'
        else :
            time_interval = 300
            if int(params['whereJson']['time_start'][15:16]) >= 5:
                str_gte = params['whereJson']['time_start'][:15] + '5:00'
            else:
                str_gte = params['whereJson']['time_start'][:15] + '0:00'
            if int(params['whereJson']['time_end'][15:16]) >= 5:
                str_lt = params['whereJson']['time_end'][:15] + '5:00'
            else:
                str_lt = params['whereJson']['time_end'][:15] + '0:00'
        date_gte = datetime.strptime(str_gte, '%Y-%m-%d %H:%M:%S')
        date_lt = datetime.strptime(str_lt, '%Y-%m-%d %H:%M:%S')
        int_gte = int(date_gte.timestamp())
        int_lt = int(date_lt.timestamp())
        int_lt = int_lt - int_lt % time_interval
        int_num = int((int_lt-int_gte)/time_interval)
        whereStr = 'log_time < "'+str_lt+'" and log_time >= "'+str_gte+'"'
        if 'ip' in params['whereJson']:
            whereStr += ' and server_ip = "'+params['whereJson']['ip']+'"'
        if time_interval == 3600:
            sql = 'select date_format(log_time,"%Y-%m-%d %H:00:00") as time, type_name, count(*) as num from dns_req_list where '+whereStr+' group by time,type_name order by create_time asc'
        if time_interval == 300:
            sql = 'select create_time as time, type_name, count(*) as num from dns_req_list where '+whereStr+' group by create_time,type_name order by create_time asc'
        if time_interval == 60:
            sql = 'select date_format(log_time,"%Y-%m-%d %H:%i:00") as time, type_name, count(*) as num from dns_req_list where '+whereStr+' group by time,type_name order by create_time asc'
        result = self.mysqldb.find_data(self.table_name, params, sql)
        # print(result)

        if result:
            result['dict_time_type'] = {}
            result['time'] = []
            result['type_name'] = ['ALL']
            result['ALL'] = []
            for item in result['rows']:
                if item['type_name'] not in result['type_name']:
                    result['type_name'].append(item['type_name'])
                    result[item['type_name']] = []
                result['dict_time_type'][item['time']+'-'+item['type_name']] = item['num']
            # print(result['dict_time_type'])
            for i in range(int_num):
                str_time = datetime.fromtimestamp(int_gte + time_interval*i).strftime('%Y-%m-%d %H:%M:%S')
                # print(str_time)
                num_all = 0
                for item in result['type_name']:
                    str_time_type = str_time+'-'+item
                    if str_time_type in result['dict_time_type']:
                        num = result['dict_time_type'][str_time_type]
                    else:
                        num = 0
                    num_all += num
                    if item != 'ALL':
                        result[item].append(num)
                result['ALL'].append(num_all)
                result['time'].append(str_time)
            sum_ALL = sum(result['ALL'])
            result['rate'] = []
            for item in result['type_name']:
                if sum_ALL == 0:
                    result['rate'].append(0)
                else:
                    result['rate'].append(round(sum(result[item])/sum_ALL, 2))
            del result['count']
            del result['rows']
            del result['dict_time_type']
            dict_res = {'code': 200, 'msg': '操作成功', 'info': result}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))


    # 导出数据
    def export_data(self):
        params = self.req.dict_req
        params['limit'] = -1
        params['page'] = 1
        if 'time_start' not in params['whereJson'] or 'time_end' not in params['whereJson']:
            dict_res = {'code': 500, 'msg': 'whereJson错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if params['whereJson']['time_start'] == '' or params['whereJson']['time_end'] == '':
            dict_res = {'code': 500, 'msg': 'whereJson错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'ip' in params['whereJson']:
            params['whereJson']['server_ip'] = params['whereJson']['ip']
            del params['whereJson']['ip']
        params['whereJson']['log_time'] = {'$gte': params['whereJson']['time_start'], '$lt': params['whereJson']['time_end']}
        del params['whereJson']['time_start']
        del params['whereJson']['time_end']
        params['sortJson'] = {'log_time': 1}
        result = self.mysqldb.find_data(self.table_name, params)
        # print(result)
        if result:
            file_path = os.path.dirname(os.path.dirname(__file__)) + '/static/uploadFile/'+ self.table_name +'_export.csv'
            list_title = ['设备IP', '域名', '客户端IP', '端口', '类型', '时间']
            list_title_en = ['server_ip','client_host','client_ip','client_port','type_name','log_time']
            mycsv = my_csv.model()
            result = mycsv.write(file_path,list_title,list_title_en,result['rows'])
            str_url = result['url']
            str_url = '/uploadFile' + str_url[str_url.rindex('/'):]
            dict_res = {'code': 200, 'msg': '操作成功', 'url': str_url}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
