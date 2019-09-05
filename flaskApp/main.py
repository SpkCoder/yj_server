# -*- coding: utf-8 -*-
from flaskApp.config.config import *
from flaskApp import app
from flask import request, redirect, make_response
from flaskApp.urls import dict_url
from flask_cors import CORS
from datetime import timedelta
import logging
import os
import json
import jwt

#config
app.config['ENV'] = env_name
app.config['DEBUG'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)  #设置缓存时间1s
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024            #设置上传文件100M
app.config['UPLOAD_FOLDER'] = './flaskApp/static/uploadFile'     #设置上传文件路径

#logging config
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename= './logs/out.log',
                filemode='w'
                )

# 允许跨越
CORS(app, supports_credentials=True)

@app.route('/')
def index():
    file_path = os.path.join(os.path.dirname(__file__), 'static/index2.html')
    with open(file_path, encoding='utf-8') as file:
        data = file.read()
        return data


@app.route('/favicon.ico')
def favicon():
    return redirect('/static/favicon.ico')


@app.route('/api/python/<arg>', methods=['GET', 'POST'])
def require(arg):
    #验证request json
    logging.info('request arg: ' + str(arg))
    try:
        if request.args:
            dict_req = json.loads(request.args['params'])
        elif request.form:
            dict_req = json.loads(request.form['params'])
        else:
            dict_req = json.loads(request.get_data())
        print(dict_req)
    except Exception as e:
        logging.debug('request json error: ' + str(e))
        dict_res = {'code': 500, 'msg': 'request json error'}
        return make_response(json.dumps(dict_res, ensure_ascii=False))
    request.dict_req = dict_req
    if arg == 'login':
        import_module = __import__(dict_url['/api/python/login'], fromlist=["*"])
        return import_module.model(request).actions()
    else:
        if 'tocken' not in dict_req:
            dict_res = {'code': 500, 'msg': 'miss tocken'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        #验证tocken
        try:
            dict_tocken=jwt.decode(dict_req['tocken'],JWT_SECRET,algorithms='HS256')
            pass
        except Exception as e:
            dict_res = {'code': 500, 'msg': '没有登录或登录已经过期！'}
            return make_response(json.dumps(dict_res, ensure_ascii=False))
        request.dict_tocken = dict_tocken
        req_url = '/api/python/' + arg
        if req_url in dict_url:
            import_module = __import__(dict_url[req_url], fromlist=["*"])
            return import_module.model(request).actions()
        else:
            return redirect('/static/error.html')

@app.errorhandler(404)
def page_not_found(error):
    return redirect('/static/error.html')