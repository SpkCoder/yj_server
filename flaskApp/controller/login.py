# -*- coding: utf-8 -*-
from flaskApp.config.config import *
from flask import make_response
from flaskApp.modules import db_mysql
from flaskApp.modules import my_pillow
import logging
import json
import time
import hashlib
import jwt
import re



# /python/login req_data {"action":"SignIn", "username":"admin","password":"123456"}  //登录
# /python/login req_data {"action":"SignOut", "username":"admin", "tocken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkZc"}    //退出
# /python/login req_data {"action":"updateData", "username":"admin", "tocken": "eyJhbGciOiiZpVwqZc", "updateJson":{"password":"123456"}}  //修改密码


class model(object):
    def __init__(self,req):
        self.req = req 
        self.table_name = 'user_list'
        self.mysqldb = db_mysql.model()

    # 分配方法
    def actions(self):
        # GET请求
        if self.req.method == 'GET':
            if self.req.dict_req['action'] == 'getCode':
                return self.get_code()
            else:
                dict_res = {'code': 500, 'msg': 'action错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
        
        # POST请求
        elif self.req.method == 'POST':
            if self.req.dict_req['action'] == 'SignIn':
                return self.sign_in()
            elif self.req.dict_req['action'] == 'SignOut':
                return self.sign_out()
            elif self.req.dict_req['action'] == 'updateData':
                return self.update_data()
            else:
                dict_res = {'code': 500, 'msg': 'action错误'}
                return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': 'method错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

    # 登录
    def sign_in(self):
        dict_req = self.req.dict_req
        # im_code = self.req.cookies['im_code'] if 'im_code' in self.req.cookies else ''
        # im_code2 = dict_req['code'] if 'code' in dict_req else ''
        # if not im_code:
        #     dict_res = {'code': 500, 'msg': '验证码已过期'}
        #     return make_response(json.dumps(dict_res, ensure_ascii=False))
        # if im_code != im_code2:
        #     dict_res = {'code': 500, 'msg': '验证码错误'}
        #     return make_response(json.dumps(dict_res, ensure_ascii=False))
        if re.search(r'^\w*$', dict_req['username']) and len(dict_req['password']) >= 6:
            password = "pw" + dict_req['password'] + dict_req['password'][0:3]
            md5 = hashlib.md5()
            md5.update(password.encode(encoding='utf-8'))
            md5_password = md5.hexdigest()
            dict_req['md5_password'] = md5_password
        else:
            dict_res = {'code': 500, 'msg': '用户名或密码格式错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        dict_req['username'] = dict_req['username'].lower()
        params = {
            'whereJson':{
                'username': dict_req['username'], 
                'password': dict_req['md5_password']
            },
            'fieldJson':{
                'username': 1, 
                'password': 1,
                'role_id': 1
            }
        }
        result = self.mysqldb.find_data(self.table_name, params)
        if result and result['count'] > 0:
            expire_time = int(time.time()+3600*8) #8小时
            str_tocken=jwt.encode( { 'username':result['rows'][0]['username'], 'password': dict_req['password'], 'role_id':result['rows'][0]['role_id'], 'exp':expire_time }, JWT_SECRET, algorithm='HS256' ).decode('utf-8')
            dict_res = {'code': 200, 'msg': '登录成功', 'tocken': str_tocken}
            logging.debug(dict_req['username'] + '登录成功')
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        else:
            dict_res = {'code': 500, 'msg': '用户名或密码错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))


    # 退出
    def sign_out(self):
        if 'username' not in self.req.dict_req:
            dict_res = {'code': 500, 'msg': 'miss username'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'tocken' not in self.req.dict_req:
            dict_res = {'code': 500, 'msg': 'miss tocken'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        str_tocken = self.req.dict_req['tocken']
        try:
            dict_tocken=jwt.decode(str_tocken,JWT_SECRET,algorithms='HS256')
            str_tocken=jwt.encode( { 'username':dict_tocken['username'], 'role_id':dict_tocken['role_id'], 'exp':0 }, JWT_SECRET, algorithm='HS256' ).decode('utf-8')
            dict_res = {'code': 200, 'msg': '退出成功'}
            logging.debug(self.req.dict_req['username'] + '退出成功')
        except Exception as e:
            print(e)
            dict_res = {'code': 500, 'msg': '没有登录或登录已经过期！'}
        return make_response(json.dumps(dict_res, ensure_ascii=False))


    # 修改密码
    def update_data(self):
        dict_req = self.req.dict_req
        if 'tocken' not in dict_req:
            dict_res = {'code': 500, 'msg': 'miss tocken'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'whereJson' not in dict_req:
            dict_res = {'code': 500, 'msg': 'miss whereJson'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'username' not in dict_req['whereJson'] or 'password' not in dict_req['whereJson']:
            dict_res = {'code': 500, 'msg': 'miss username or password'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if 'updateJson' not in dict_req:
            dict_res = {'code': 500, 'msg': 'miss updateJson'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        str_tocken = dict_req['tocken']
        try:
            dict_tocken=jwt.decode(str_tocken,JWT_SECRET,algorithms='HS256')
        except Exception as e:
            dict_res = {'code': 500, 'msg': '没有登录或登录已经过期！'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        dict_req['whereJson']['username'] = dict_req['whereJson']['username'].lower()
        if dict_req['whereJson']['password'] != dict_tocken['password']:
            dict_res = {'code': 500, 'msg': '密码错误！'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        if len(dict_req['updateJson']['password']) >= 6:
            password = "pw" + dict_req['updateJson']['password'] + dict_req['updateJson']['password'][0:3]
            md5 = hashlib.md5()
            md5.update(password.encode(encoding='utf-8'))
            md5_password = md5.hexdigest()
            dict_req['updateJson']['password'] = md5_password
        else:
            dict_res = {'code': 500, 'msg': '密码格式错误'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))

        whereJson = { 'username': dict_req['whereJson']['username']}
        updateJson = {
            'password': dict_req['updateJson']['password'],
            'update_name': dict_req['whereJson']['username'],
            'update_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        result = self.mysqldb.update_data(self.table_name, whereJson, updateJson)
        if result:
            dict_res = {'code': 200, 'msg': '操作成功'}
        else:
            dict_res = {'code': 500, 'msg': '操作失败'}
        return make_response(json.dumps(dict_res, ensure_ascii=False))


    # 获取二维码
    def get_code(self):
        mypillow = my_pillow.model()
        code,buf_image = mypillow.code_image('code.png')
        res = make_response(buf_image)
        res.headers['Content-Type'] = 'image/png'
        res.set_cookie('im_code', code, max_age=30)
        return res

