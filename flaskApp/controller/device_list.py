# -*- coding: utf-8 -*-
from flask import make_response
from flaskApp.modules import db_mysql
from flaskApp.modules import my_csv
import json
import time
import re
import os
from datetime import datetime


#/python/device_list req_data { "action":"findData", "limit":10, "page":1, "whereJson":{}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //查询数据
#/python/device_list req_data { "action":"insertData", "dataArr":[{"class_name":"超级用户"}], "tocken": "eb2xlX2lkIj4gphmei4" }  //插入数据
#/python/device_list req_data { "action":"updateData", "whereJson":{"id":"1"}, "updateJson":{"class_name":"超级用户"}, "tocken": "eb2xlX2lkIj4gphmei4" }  //修改数据
#/python/device_list req_data { "action":"delData", whereJson={"id":[1,3]}, "tocken": "eyJhbGciOiJIUzIbmFtZSmei4" }  //删除数据


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'device_list'
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

        # POST请求
        elif self.req.method == 'POST':

            str_action = self.req.dict_req['action']
            if str_action == 'importData':
                str_action = 'insertData'
            # 判断权限
            if not self.mysqldb.get_power(self.req.dict_tocken['role_id'], self.table_name, str_action):
                dict_res = {'code': 500, 'msg': '没有权限'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            if self.req.dict_req['action'] == 'insertData':
                return self.insert_data()
            elif self.req.dict_req['action'] == 'updateData':
                return self.update_data()
            elif self.req.dict_req['action'] == 'delData':
                return self.del_data()
            elif self.req.dict_req['action'] == 'importData':
                return self.import_data()
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
        # 设备总览
        if 'type' in params['whereJson'] and params['whereJson']['type'] == 'device_list_icon':
            params['limit'] = -1
            params['sortJson'] = {"level": 1}
            params['whereJson'] = {}
            result = self.mysqldb.find_data(self.table_name, params)
            # print(result)

            if result:
                int_lt = int(datetime.now().timestamp())
                int_lt = int_lt - int_lt % 300
                str_lt = datetime.fromtimestamp(int_lt).strftime('%Y-%m-%d %H:%M:%S')
                str_gte = datetime.fromtimestamp(int_lt-300).strftime('%Y-%m-%d %H:%M:%S')
                # 查询在线设备
                sql = 'select client_ip from device_run_list where create_time < "'+str_lt+'" and create_time >= "'+str_gte+'" group by client_ip'
                result_online = self.mysqldb.find_data(self.table_name, params, sql)
                list_online = []
                if result_online:
                    for item in result_online['rows']:
                        list_online.append(item['client_ip'])
                # 查询告警设备
                sql = 'select client_ip from alarm_list where status = 1 group by client_ip'
                result_alarm = self.mysqldb.find_data(self.table_name, params, sql)
                list_alarm = []
                if result_alarm:
                    for item in result_alarm['rows']:
                        if item['client_ip'] not in list_alarm:
                            list_alarm.append(item['client_ip'])
                list_rows = []
                list_level = []
                for item in result['rows']:
                    if item['ip'] in list_online:
                        item['online_status'] = 'true'
                    else:
                        item['online_status'] = 'false'
                    if item['ip'] in list_alarm:
                        item['alarm_status'] = 'true'
                    else:
                        item['alarm_status'] = 'false'
                    if item['level'] not in list_level:
                        list_rows.append({'level': item['level'],'children': [item]})
                    elif item['level'] in list_level:
                        for item2 in list_rows:
                            if item['level'] == item2['level']:
                                item2['children'].append(item)
                    else:
                        pass
                    list_level.append(item['level'])
                dict_res = {'code': 200, 'msg': '操作成功', 'rows': list_rows}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            else:
                dict_res = {'code': 500, 'msg': '操作失败'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

        # 设备总览_监控详情
        if 'type' in params['whereJson'] and params['whereJson']['type'] == 'device_list_monitor':
            if 'time' not in params['whereJson']:
                dict_res = {'code': 500, 'msg': 'whereJson错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            if 'ip' not in params['whereJson']:
                dict_res = {'code': 500, 'msg': 'ip错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            str_gte = params['whereJson']['time'] + ' 00:00:00'
            date_gte = datetime.strptime(str_gte, '%Y-%m-%d %H:%M:%S')
            int_gte = int(date_gte.timestamp())
            int_now = int(time.time())
            int_now = int_now - int_now % 300
            if (int_now-int_gte)/3600/24 >= 1:
                date_lt = datetime.fromtimestamp(int_gte+3600*24)
                int_num = int(3600*24/300)
            else:
                date_lt = datetime.fromtimestamp(int_now)
                int_num = int((int_now-int_gte)/300)
            str_lt = date_lt.strftime('%Y-%m-%d %H:%M:00')
            whereStr = 'create_time < "'+str_lt+'" and create_time >= "'+str_gte+'"'+' and client_ip = "'+params['whereJson']['ip']+'"'
            sql = 'select client_ip, cpu_rate, net_flow_receive, net_flow_send, net_speed, ram_rate, create_time from device_run_list where '+whereStr+' group by create_time order by create_time asc'
            result = self.mysqldb.find_data(self.table_name, params, sql)
            # print(result)

            # 查询解析成功率
            whereStr = 'create_time < "'+str_lt+'" and create_time >= "'+str_gte+'"'+' and server_ip = "'+params['whereJson']['ip']+'"'
            whereStr2 = 'create_time < "'+str_lt+'" and create_time >= "'+str_gte+'"'+' and server_ip = "'+params['whereJson']['ip']+'"'+' and req_status = "SERVFAIL"'
            sql = 'select t1.server_ip, t1.num, t1.create_time, t2.num_err from (select server_ip, count(*) as num, create_time from dns_req_list where '+whereStr+' group by create_time) t1 left join (select server_ip, count(*) as num_err, create_time as create_time2 from dns_err_list where '+whereStr2+' group by create_time) t2 on t1.create_time=t2.create_time2 order by create_time asc'
            result_dns_success_rate = self.mysqldb.find_data(self.table_name, params, sql)
            
            if result:
                if len(result['rows']) > 0:
                    result['cpu_rate'] = result['rows'][len(result['rows'])-1]['cpu_rate']
                    result['ram_rate'] = result['rows'][len(result['rows'])-1]['ram_rate']
                    result['disk_rate'] = 0
                else:
                    result['cpu_rate'] = 0
                    result['ram_rate'] = 0
                    result['disk_rate'] = 0
                result['time'] = []
                result['net_flow_send'] = []
                result['qps'] = []
                result['dns_delay'] = []
                result['dns_success_rate'] = []
                result['dict_time_net'] = {}
                result['dict_time_dns'] = {}
                for item in result['rows']:
                    result['dict_time_net'][item['create_time']] = item['net_flow_send']
                for item in result_dns_success_rate['rows']:
                    item['num_err'] = item['num_err'] if item['num_err'] else 0
                    item['success_rate'] = round((item['num']-item['num_err'])/item['num'],2)
                    result['dict_time_dns'][item['create_time']] = item['success_rate']
                for i in range(int_num):
                    if i == 0:
                        continue
                    str_time = datetime.fromtimestamp(int_gte + 300*i).strftime('%Y-%m-%d %H:%M:00')
                    if str_time in result['dict_time_net']:
                        result['net_flow_send'].append(result['dict_time_net'][str_time])
                    else:
                        result['net_flow_send'].append(0)
                    if str_time in result['dict_time_dns']:
                        result['dns_success_rate'].append(result['dict_time_dns'][str_time])
                    else:
                        result['dns_success_rate'].append(0)
                    result['qps'].append(0)
                    result['dns_delay'].append(0)
                    result['time'].append(str_time.split(' ')[1])
                del result['count']
                del result['rows']
                del result['dict_time_net']
                del result['dict_time_dns']
                dict_res = {'code': 200, 'msg': '操作成功', 'info': result}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            else:
                dict_res = {'code': 500, 'msg': '操作失败'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))

        # 设备列表
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
        if type(self.req.dict_req['dataArr']) != list or len(self.req.dict_req['dataArr']) != 1:
            dict_res = {'code': 500, 'msg': 'dataArr错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        list_data = self.req.dict_req['dataArr']
        list_ip = []
        for item in list_data:
            item['create_name'] = self.req.dict_tocken['username']
            item['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            item['update_name'] = ''
            item['update_time'] = ''
            if 'ip' not in item or item['ip'] == '':
                dict_res = {'code': 500, 'msg': 'ip错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            list_ip.append(item['ip'])

        params = { 'whereJson':{ '$or': [{'ip':list_data[0]['ip']}, {'code':list_data[0]['code']}, {'name':list_data[0]['name']}] }, 'fieldJson':{'ip': 1, 'code': 1, 'name': 1 } }
        result = self.mysqldb.find_data(self.table_name, params)
        if result['count'] != 0:
            dict_res = {'code': 200, 'msg': 'code或name或ip已存在'}
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

        whereJson = self.req.dict_req['whereJson']
        updateJson = self.req.dict_req['updateJson']
        updateJson['update_name'] = self.req.dict_tocken['username']
        updateJson['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        list_or = []
        if 'ip' in updateJson:
            list_or.append({'ip':updateJson['ip']})
        if 'code' in updateJson:
            list_or.append({'code':updateJson['code']})
        if 'name' in updateJson:
            list_or.append({'name':updateJson['name']})
        params = { 'whereJson':{'id': {'$nin': [whereJson['id']]}, '$or': list_or }, 'fieldJson':{'ip': 1, 'code': 1, 'name': 1 } }
        result = self.mysqldb.find_data(self.table_name, params)
        if result['count'] != 0:
            dict_res = {'code': 500, 'msg': 'code或name或ip已存在'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

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


    # 导入数据
    def import_data(self):
        # dict_req = self.req.dict_req
        file = self.req.files.get('file')
        if not file:
            dict_res = {'code': 200, 'msg': 'file不能为空'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        file_path = os.path.dirname(os.path.dirname(__file__)) + '/static/uploadFile/'+ self.table_name +'_import.csv'
        file.save(file_path)
        mycsv = my_csv.model()
        list_title_en = ['code','name','ip','level','factory','device_type','os','os_version','cpu','ram','disk','power','address','message','online_time']
        result = mycsv.read(file_path,list_title_en)
        if result['msg']:
            dict_res = {'code': 500, 'msg': result['msg']}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        list_data = result['rows']
        list_ip = []
        for item in list_data:
            item['create_name'] = self.req.dict_tocken['username']
            item['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            item['update_name'] = ''
            item['update_time'] = ''
            if 'ip' not in item or item['ip'] == '':
                dict_res = {'code': 500, 'msg': 'ip错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
            list_ip.append(item['ip'])

        params = { 'whereJson':{ 'ip': {'$in':list_ip} }, 'fieldJson':{ 'id': 1, 'ip': 1 } }
        result = self.mysqldb.find_data(self.table_name, params)
        if result['count'] != 0:
            dict_res = {'code': 200, 'msg': 'ip已存在'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        result = self.mysqldb.insert_data(self.table_name, list_data)
        # print(result)

        if result:
            dict_res = {'code': 200, 'msg': '操作成功'}
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
            list_title = ['设备编号', '设备名称', 'IP地址', '所属节点', '所属厂商', '设备类型', '操作系统', '版本号', 'CPU', '内存', '磁盘空间', '功率', '地址', '备注', '上线时间']
            list_title_en = ['code','name','ip','level','factory','device_type','os','os_version','cpu','ram','disk','power','address','message','online_time']
            mycsv = my_csv.model()
            result = mycsv.write(file_path,list_title,list_title_en,result['rows'])
            str_url = result['url']
            str_url = '/uploadFile' + str_url[str_url.rindex('/'):]
            dict_res = {'code': 200, 'msg': '操作成功', 'url': str_url}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

