# -*- coding: utf-8 -*-
import csv
import os


class model():
    def __init__(self):
        self.name = '' 

    #读取csv
    def read(self,path,list_title_en):
        dict_res = {'msg': '', 'rows': []}
        with open(path, encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)  # 使用csv.reader读取csvfile中的文件
            list_title = next(csv_reader)  # 读取第一行每一列的标题
            index = 1
            if len(list_title) != len(list_title_en):
                dict_res['msg'] = '第'+str(index)+'行错误'
                return dict_res
            for row in csv_reader:  #遍历每行数据
                index +=1
                if len(row) != len(list_title_en):
                    dict_res['msg'] = '第'+str(index)+'行错误'
                    return dict_res
                obj = {}
                for i, value in enumerate(list_title_en):
                    obj[value] = row[i]
                dict_res['rows'].append(obj)
        # print(list_title)
        # print(dict_res)
        return dict_res

    #写入csv
    def write(self,path,list_title,list_title_en,rows):
        dict_res = {'msg': '', 'url': ''}
        list_data = []
        for obj in rows:
            arr = []
            for item in list_title_en:
                arr.append(obj[item])
            list_data.append(arr)
        with open(path, "w", newline='', encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows([list_title])
            if len(list_data) > 0:
                writer.writerows(list_data)
        dict_res['url'] = path

        # print(list_data)
        # print(dict_res)
        return dict_res



if __name__ == "__main__":
    mycsv = model()

    # 读取数据
    # csv_path = os.path.join(os.path.dirname(__file__), 'export.csv')
    # list_title_en = ['code','name','ip','lever','factory','device_type','os','os_version','cpu','ram','disk','power','address','message','online_time']
    # result = mycsv.read(csv_path,list_title_en)
    # print(result)

    # 写入数据
    # csv_path = os.path.join(os.path.dirname(__file__), 'export.csv')
    # list_title = ['设备编号', '设备名称', 'IP地址', '所属节点', '所属厂商', '设备类型', '操作系统', '版本号', 'CPU', '内存', '磁盘空间', '功率', '地址', '备注', '上线时间']
    # list_title_en = ['code','name','ip','lever','factory','device_type','os','os_version','cpu','ram','disk','power','address','message','online_time']
    # rows = [{'code': 'A00001', 'name': '设备一', 'ip': '192.168.200.3', 'lever': '浙江', 'factory': '华为', 'device_type': 'infoblox', 'os': 'window', 'os_version': '10.0.1', 'cpu': '酷睿8核', 'ram': '4G', 'disk': '500G', 'power': '100W', 'address': '杭州市西湖区xx街道', 'message': 'xx', 'online_time': '2019-07-20'}, {'code': 'A00002', 'name': '设备二', 'ip': '192.168.200.199', 'lever': '浙江', 'factory': '华为', 'device_type': 'infoblox', 'os': 'window', 'os_version': '10.0.1', 'cpu': '酷睿8核', 'ram': '4G', 'disk': '500G', 'power': '100W', 'address': '杭州市西湖区xx街道', 'message': 'xx', 'online_time': '2019-07-20'}]
    # result = mycsv.write(csv_path,list_title,list_title_en,rows)
    # print(result)
