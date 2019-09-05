# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
import json
import time
import re
from datetime import datetime

#/python/dhcp_record_list req_data { "action":"findData", "limit":10, "page":1, "whereJson":{}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'dhcp_record_list'
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
        params['limit'] = int(params['limit']) if 'limit' in params else 10
        params['page'] = int(params['page']) if 'page' in params else 1
        params['whereJson'] = params['whereJson'] if 'whereJson' in params else {}

        # 下钻页面
        if 'client_ip' in params['whereJson']:
            if 'time' not in params['whereJson']:
                dict_res = {'code': 500, 'msg': 'whereJson错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            time_space = 60*60*4  #4小时粒度
            str_gte = params['whereJson']['time'] + ' 00:00:00'
            date_gte = datetime.strptime(str_gte, '%Y-%m-%d %H:%M:%S')
            int_gte = int(date_gte.timestamp())
            int_now = int(time.time())
            int_now = int_now - int_now % time_space
            if (int_now-int_gte)/3600/24 >= 1:
                date_lt = datetime.fromtimestamp(int_gte+3600*24)
                int_num = int(3600*24/time_space)
            else:
                date_lt = datetime.fromtimestamp(int_now)
                int_num = int((int_now-int_gte)/time_space)
            str_lt = date_lt.strftime('%Y-%m-%d %H:%M:00')
            sql = 'select create_time as time, lease from dhcp_record_list where client_ip = "'+params['whereJson']['client_ip']+'" and create_time < "'+str_lt+'" and create_time >= "'+str_gte+'" order by create_time asc'
            result = self.mysqldb.find_data(self.table_name, params, sql)
            # print(result)

            if result:
                result['time'] = []
                result['lease'] = []
                for i in range(int_num+1):
                    if i == 0:
                        continue
                    list_lease = []
                    for item in result['rows']:
                        this_time = datetime.strptime(item['time'], '%Y-%m-%d %H:%M:%S').timestamp()
                        if this_time <= int_gte + time_space*i:
                            list_lease.append(item['lease'])
                    if len(list_lease)>0:
                        result['lease'].append(round(sum(list_lease)/len(list_lease),3))
                    else:
                        result['lease'].append(0)
                    str_time = datetime.fromtimestamp(int_gte + time_space*i).strftime('%Y-%m-%d %H:00:00')
                    result['time'].append(str_time.split(' ')[1])
                del result['count']
                del result['rows']
                dict_res = {'code': 200, 'msg': '操作成功', 'info': result}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            else:
                dict_res = {'code': 500, 'msg': '操作失败'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            # params['fieldJson'] = {"client_ip": 1,"client_host": 1,"client_mac": 1,"log_time": 1,"create_time": 1}
            # params['groupJson'] = {"client_ip": 1, "lease":{"$avg": "lease"}}
            result = self.mysqldb.find_data(self.table_name, params)
            # print(result)

            if result:
                dict_res = {'code': 200, 'msg': '操作成功', 'limit': params['limit'], 'page': params['page'], 'count': result['count'], 'rows': result['rows']}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            else:
                dict_res = {'code': 500, 'msg': '操作失败'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

