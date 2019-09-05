# -*- coding:utf-8 -*-
#!/usr/bin/python

from flaskApp.config.config import *
from elasticsearch import Elasticsearch
import logging


class model():

	def __init__(self):
		self._db_connect()

    # 连接数据库ESDB
	def _db_connect(self):
		try:
			self._es = Elasticsearch([{'host':ESDB_HOST,'port':ESDB_PORT}], timeout=3600)
		except Exception as e:
			logging.debug('连接数据库ESDB: ' + str(e))
			exit()

	# ESDB查询
	def find_data(self,index_name,body):
		try:
			result = self._es.search(index=index_name, body=body)
			return result
		except Exception as e:
			logging.debug('ESDB查询: ' + str(e))
			exit()
