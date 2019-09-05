# -*- coding:utf-8 -*-

from flaskApp.modules import db_mysql
from flaskApp.modules import my_email
from datetime import datetime, timedelta, timezone
from multiprocessing import Process
import logging
import json
import re


class model():

    def __init__(self, gt_str, lt_str):
        self._gt_str = gt_str
        self._lt_str = lt_str
        # self._gt_str = '2019-08-05 14:45:00'
        # self._lt_str = '2019-08-05 14:50:00'
        self.list_receive = []
        self.mysqldb = db_mysql.model()
        self.myemail = my_email.model()

    # 发送邮件
    def sendemail(self, obj):
        str_html = ''
        str_html+='<p>告警开始时间：'+obj['first_alarm_time']+'</p>'
        str_html+='<p>IP：'+obj['client_ip']+'</p>'
        str_html+='<p>告警类型：'+obj['alarm_type']+'</p>'
        str_html+='<p>告警信息：'+obj['alarm_msg']+'</p>'
        dict_option = { 'to': self.list_receive, 'subject': '告警：'+obj['client_ip'], 'html': str_html }
        self.myemail.send(dict_option)

    # 查询该段时间的数据是否超过阀值
    def run(self):
        #查询阀值
        params = {}
        table_name = 'alarm_type_list'
        sql = 'select * from alarm_type_list order by id asc'
        alarm_result = self.mysqldb.find_data(table_name, params, sql)
        # print(alarm_result)

        #查询收件人
        params = {}
        table_name = 'email_user_list'
        sql = 'select * from email_user_list'
        receive_result = self.mysqldb.find_data(table_name, params, sql)
        # print(receive_result)
        if receive_result:
            for item in receive_result['rows']:
                self.list_receive.append(item['email'])
        # self.list_receive = ['yuxian@suqueen.com']
        # print(receive_result)

        #查询设备列表
        params = {}
        table_name = 'device_list'
        sql = 'select id, code, name, ip, level from device_list'
        device_result = self.mysqldb.find_data(table_name, params, sql)
        # print(device_result)

        #cpu_rate ram_rate 告警
        params = {}
        table_name = 'device_run_list'
        whereStr = ' where create_time>="'+self._gt_str+'" and create_time<"'+self._lt_str+'"'
        sql = 'select client_ip, cpu_rate, ram_rate, log_time, create_time from device_run_list'+whereStr+' group by create_time, client_ip order by log_time desc limit 0,10'
        result = self.mysqldb.find_data(table_name, params, sql)
        # print(result)
        if result:
            for item in result['rows']:
                if int(item['cpu_rate']*100) >= int(alarm_result['rows'][6]['tvalue']) and alarm_result['rows'][6]['status']=='ON':
                    alarm_msg = 'CPU使用率'+str(int(item['cpu_rate']*100))+'%'
                    list_data = [{'client_ip': item['client_ip'], 'alarm_type_id': alarm_result['rows'][6]['id'], 'alarm_time': item['log_time'], 'alarm_msg': alarm_msg, 'status': 1}]
                    print(list_data)
                    result2 = self.mysqldb.insert_data('alarm_list',list_data)
                    sql = 'select alarm_list.client_ip, alarm_list.alarm_type_id, min(alarm_list.alarm_time) as first_alarm_time, max(alarm_list.alarm_time) as last_alarm_time, alarm_list.alarm_msg, alarm_list.status, alarm_type_list.alarm_type from alarm_list left join alarm_type_list on alarm_list.alarm_type_id = alarm_type_list.id where alarm_list.status = 1 and alarm_list.client_ip="'+item['client_ip']+'" and alarm_list.alarm_type_id='+alarm_result['rows'][6]['id']+' group by client_ip, alarm_type_id order by alarm_time desc'
                    result = self.mysqldb.find_data(table_name, params, sql)
                    if result and len(result['rows'])>0:
                        # self.sendemail(result['rows'][0])
                        p = Process(target=self.sendemail, args=(result['rows'][0],))
                        p.start()
                if int(item['ram_rate']*100) >= int(alarm_result['rows'][5]['tvalue']) and alarm_result['rows'][5]['status']=='ON':
                    alarm_msg = '内存使用率'+str(int(item['ram_rate']*100))+'%'
                    list_data = [{'client_ip': item['client_ip'], 'alarm_type_id': alarm_result['rows'][5]['id'], 'alarm_time': item['log_time'], 'alarm_msg': alarm_msg, 'status': 1}]
                    print(list_data)
                    result2 = self.mysqldb.insert_data('alarm_list',list_data)
                    sql = 'select alarm_list.client_ip, alarm_list.alarm_type_id, min(alarm_list.alarm_time) as first_alarm_time, max(alarm_list.alarm_time) as last_alarm_time, alarm_list.alarm_msg, alarm_list.status, alarm_type_list.alarm_type from alarm_list left join alarm_type_list on alarm_list.alarm_type_id = alarm_type_list.id where alarm_list.status = 1 and alarm_list.client_ip="'+item['client_ip']+'" and alarm_list.alarm_type_id='+alarm_result['rows'][5]['id']+' group by client_ip, alarm_type_id order by alarm_time desc'
                    result = self.mysqldb.find_data(table_name, params, sql)
                    if result and len(result['rows'])>0:
                        # self.sendemail(result['rows'][0])
                        p = Process(target=self.sendemail, args=(result['rows'][0],))
                        p.start()
        else:
            print('操作失败')


        #解析成功率 告警
        params = {}
        table_name = 'dns_err_list'
        whereStr = ''
        sql = 'select t3.client_ip, t3.num_host, t3.num, t2.num_err from (select t1.client_ip, count(*) as num_host, sum(t1.num_host) as num from (select client_ip, client_host, count(*) as num_host from dns_req_list group by client_ip, client_host) t1 group by t1.client_ip) t3 left join (select client_ip, count(*) as num_err from dns_err_list where req_status = "SERVFAIL" group by client_ip) t2 on t3.client_ip=t2.client_ip order by num desc'
        result = self.mysqldb.find_data(table_name, params, sql)
        # print(result)
        if result:
            for item in result['rows']:
                item['num_err'] = item['num_err'] if item['num_err'] else 0
                item['err_rate'] = round(item['num_err']/item['num'],2)
                item['log_time'] = self._gt_str
                if int(100-item['err_rate']*100) <= int(alarm_result['rows'][1]['tvalue']) and alarm_result['rows'][1]['status']=='ON':
                    alarm_msg = '解析成功率'+str(int(100-item['err_rate']*100))+'%'
                    list_data = [{'client_ip': item['client_ip'], 'alarm_type_id': alarm_result['rows'][1]['id'], 'alarm_time': item['log_time'], 'alarm_msg': alarm_msg, 'status': 1}]
                    print(list_data)
                    result2 = self.mysqldb.insert_data('alarm_list',list_data)
                    whereStr = ' where alarm_list.status = 1 and alarm_list.client_ip="'+item['client_ip']+'" and alarm_list.alarm_type_id=2'
                    sql = 'select alarm_list.client_ip, alarm_list.alarm_type_id, min(alarm_list.alarm_time) as first_alarm_time, max(alarm_list.alarm_time) as last_alarm_time, alarm_list.alarm_msg, alarm_list.status, alarm_type_list.alarm_type from alarm_list left join alarm_type_list on alarm_list.alarm_type_id = alarm_type_list.id'+whereStr+' group by client_ip, alarm_type_id order by alarm_time desc'
                    result2 = self.mysqldb.find_data(table_name, params, sql)
                    if result2 and len(result2['rows'])>0:
                        # self.sendemail(result2['rows'][0])
                        p = Process(target=self.sendemail, args=(result2['rows'][0],))
                        p.start()

        else:
            print('操作失败')


        #设备离线 告警
        params = {}
        table_name = 'device_run_list'
        whereStr = ''
        sql = 'select id, client_ip, log_time from device_run_list where create_time < "'+self._lt_str+'" and create_time >= "'+self._gt_str+'" group by client_ip'
        result = self.mysqldb.find_data(table_name, params, sql)
        # print(result)
        if result:
            list_online = []
            for item in result['rows']:
                list_online.append(item['client_ip'])
            for item in device_result['rows']:
                if item['ip'] not in list_online and alarm_result['rows'][3]['status']=='ON':
                    alarm_msg = '设备离线'
                    list_data = [{'client_ip': item['ip'], 'alarm_type_id': alarm_result['rows'][3]['id'], 'alarm_time': self._gt_str, 'alarm_msg': alarm_msg, 'status': 1}]
                    result2 = self.mysqldb.insert_data('alarm_list',list_data)
                    whereStr = ' where alarm_list.status = 1 and alarm_list.client_ip="'+item['ip']+'" and alarm_list.alarm_type_id=4'
                    sql = 'select alarm_list.client_ip, alarm_list.alarm_type_id, min(alarm_list.alarm_time) as first_alarm_time, max(alarm_list.alarm_time) as last_alarm_time, alarm_list.alarm_msg, alarm_list.status, alarm_type_list.alarm_type from alarm_list left join alarm_type_list on alarm_list.alarm_type_id = alarm_type_list.id'+whereStr+' group by client_ip, alarm_type_id order by alarm_time desc'
                    result2 = self.mysqldb.find_data(table_name, params, sql)
                    if result2 and len(result2['rows'])>0:
                        # self.sendemail(result2['rows'][0])
                        p = Process(target=self.sendemail, args=(result2['rows'][0],))
                        p.start()

        else:
            print('操作失败')