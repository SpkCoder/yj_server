# -*- coding:utf-8 -*-
#!/usr/bin/python

from flaskApp.config.config import *
import pymysql
import logging
import re


class model():

	def __init__(self):
		self._db = None
		self._db_connect()
		self._db.close()

	# 连接数据库mysql
	def _db_connect(self):
		try:
			self._db = pymysql.connect( host = DB_HOST, user = DB_USER_NAME, password = DB_PASSWORD, port = DB_PORT, db = DB_NAME, charset = DB_CHARSET, cursorclass = pymysql.cursors.DictCursor )
		except Exception as e:
			logging.debug('连接数据库mysql: ' + str(e))
			exit()

	# 返回fieldStr
	def get_fieldStr(self, params):
		fieldStr = ''
		for k in params['fieldJson']:
			if re.search(r'^.*\..*$', k):
				fieldStr += ''+k+''+', '
			else:
				fieldStr += '`'+k+'`'+', '
		# fieldStr = fieldStr[0:len(fieldStr)-2]
		return fieldStr

	# 返回whereStr
	def get_whereStr(self, params):
		whereStr = ''
		for k in params['whereJson']:
			value = params['whereJson'][k]
			if type(value) == str:
				if re.search(r'^\/.*\/$', value):
					whereStr += k+' like "%'+re.sub(r'^\/|\/$', '', value)+'%" and '
				elif re.search(r'^\/\^.*', value):
					whereStr += k+' like "'+re.sub(r'^\/|\/$', '', value)+'%" and '
				elif re.search(r'.*\$\/$', value):
					whereStr += k+' like "%'+re.sub(r'^\/|\/$', '', value)+'" and '
				else:
					whereStr += k+' = "'+value+'" and '
			elif type(value) == int or type(value) == float:
				whereStr += k+' = '+str(value)+' and '
			elif type(value) == dict:
				if '$gt' in value:
					if type(value['$gt']) == str:
						whereStr += k+' > "'+value['$gt']+'" and '
					else:
						whereStr += k+' > '+value['$gt']+' and '
				if '$lt' in value:
					if type(value['$lt']) == str:
						whereStr += k+' < "'+value['$lt']+'" and '
					else:
						whereStr += k+' < '+value['$lt']+' and '
				if '$gte' in value:
					if type(value['$gte']) == str:
						whereStr += k+' >= "'+value['$gte']+'" and '
					else:
						whereStr += k+' >= '+value['$gte']+' and '
				if '$lte' in value:
					if type(value['$lte']) == str:
						whereStr += k+'<= "'+value['$lte']+'" and '
					else:
						whereStr += k+'<= '+value['$lte']+' and '
				if '$ne' in value:
					if type(value['$ne']) == str:
						whereStr += k+'!= "'+value['$ne']+'" and '
					else:
						whereStr += k+'!= '+value['$ne']+' and '
				if '$in' in value:
					if type(value['$in']) == list:
						if len(value['$in']) > 1:
							whereStr += k+' in '+re.sub(r'\'', '"', str(tuple(value['$in'])))+' and '
						else:
							str_in = str(tuple(value['$in']))
							str_in = re.sub(r'\'', '"', str_in)
							str_in = re.sub(r'\,', '', str_in)
							whereStr += k+' in '+str_in+' and '
				if '$nin' in value:
					if type(value['$nin']) == list:
						if len(value['$nin']) > 1:
							whereStr += k+' not in '+re.sub(r'\'', '"', str(tuple(value['$nin'])))+' and '
						else:
							str_in = str(tuple(value['$nin']))
							str_in = re.sub(r'\'', '"', str_in)
							str_in = re.sub(r'\,', '', str_in)
							whereStr += k+' not in '+str_in+' and '
			elif type(value) == list and k == '$or':
				str_or = ''
				for item in value:
					for k3 in item:
						if type(item[k3]) == str:
							if re.search(r'^\/.*\/$', item[k3]):
								str_or += k3+' like "%'+re.sub(r'^\/|\/$', '', item[k3])+'%" or '
							elif re.search(r'^\/\^.*', item[k3]):
								str_or += k3+' like "'+re.sub(r'^\/|\/$', '', item[k3])+'%" or '
							elif re.search(r'.*\$\/$', item[k3]):
								str_or += k3+' like "%'+re.sub(r'^\/|\/$', '', item[k3])+'" or '
							else:
								str_or += k3+' = "'+item[k3]+'" or '
						elif type(item[k3]) == int or type(item[k3]) == float:
							str_or += k3+' = '+str(item[k3])+' or '
				str_or= str_or[0:len(str_or)-4]
				if str_or:
					whereStr += '('+str_or+')'+' and '
			else:
				pass
		whereStr= whereStr[0:len(whereStr)-5]
		return whereStr

	# 返回sortStr
	def get_sortStr(self, params):
		sortStr = ''
		for k in params['sortJson']:
			if params['sortJson'][k] > 0:
				sortStr += k+' asc, '
			else:
				sortStr += k+' desc, '
		sortStr= sortStr[0:len(sortStr)-2]
		return sortStr

	# 获取权限
	def get_power(self, role_id, table_name, action):
		self._db_connect()
		try:
			cursor = self._db.cursor()
			str_where = 'role_id=' + str(role_id) + ' and table_name="' + table_name + '"' + ' and function_en="' + action + '"'
			sql = 'select power_list.role_id,power_list.fn_id,model_list_fn.table_name,model_list_fn.function_en from power_list LEFT JOIN model_list_fn ON power_list.fn_id = model_list_fn.id where ' + str_where
			cursor.execute(sql)
			result = cursor.fetchall()
			self._db.close()
			del cursor
			return len(result)
		except Exception as e:
			self._db.close()
			logging.debug('find_data: ' + str(e))
			exit()
	
	#查询数据
	def find_data(self, table_name, params={}, sql='', sql_count=''):
		# params = {
        #     "limit":10,
        #     "page":1,
        #     "fieldJson":{"id": 1,"time": 1,"cdnip": 1,"bras": 1,"cdnarea": 1,"ct_count": 1},
        #     "whereJson":{"cdnarea": "温州"},
        #     "sortJson":{"cdnip": 1, "time": -1},
        #     "groupJson":{"cdnip": 1, "ct_count2":{"$sum": "ct_count"}}
        # }
		# 初始化params
		params['limit'] = int(params['limit']) if 'limit' in params else 10
		params['offset'] = params['limit'] * (int(params['page']) - 1) if 'page' in params else 0
		params['fieldJson'] = params['fieldJson'] if 'fieldJson' in params else {}
		params['whereJson'] = params['whereJson'] if 'whereJson' in params else {}
		params['sortJson'] = params['sortJson'] if 'sortJson' in params else {}
		params['groupJson'] = params['groupJson'] if 'groupJson' in params else {}
		self._db_connect()
		if sql:
			#sql查询
			try:
				logging.debug('sql_count: ' + sql_count)
				logging.debug('sql: ' + sql)
				cursor = self._db.cursor()
				#获取count
				if sql_count:
					cursor.execute(sql_count)
					count = cursor.fetchone()['number']
				else:
					count = 0
				#获取rows
				cursor.execute(sql)
				result = cursor.fetchall()
				self._db.close()
				del cursor
				return {'count': count, 'rows': result}
			except Exception as e:
				self._db.close()
				logging.debug('find_data: ' + str(e))
				exit()
		else:
			#json查询
			try:
				fieldStr = '*'
				whereStr = ''
				sortStr = ''
				groupStr = ''
				if params['fieldJson']:
					fieldStr = self.get_fieldStr(params)
				if params['whereJson']:
					whereStr = self.get_whereStr(params)
				if params['sortJson']:
					sortStr = self.get_sortStr(params)
				if params['groupJson']:
					for k in params['groupJson']:
						value = params['groupJson'][k]
						if type(value) == dict:
							if '$sum' in value:
								fieldStr += 'sum('+value['$sum']+') as '+k+', '
							if '$avg' in value:
								avg_point = int(value['$avg_point']) if '$avg_point' in value else 0 
								fieldStr += 'round(avg('+value['$avg']+'),'+str(avg_point)+') as '+k+', '
						else:
							groupStr += k+', '
					groupStr = groupStr[0:len(groupStr)-2]
				fieldStr = fieldStr[0:len(fieldStr)-2] if len(fieldStr)>1 else '*'
				sql_count = 'select count(*) as number from '+table_name
				sql = 'select '+fieldStr+' from '+table_name
				if whereStr:
					sql_count += ' where ' + whereStr
					sql += ' where ' + whereStr
				if groupStr:
					sql_count += ' group by ' + groupStr
					sql_count = 'select count(*) as number from ('+sql_count+') gyd'
					sql += ' group by ' + groupStr
				if sortStr:
					sql += ' order by ' + sortStr
				if params['limit']>0:
					sql += ' limit '+str(params['offset'])+','+str(params['limit'])
				
				logging.debug('sql_count: ' + sql_count)
				logging.debug('sql: ' + sql)
				cursor = self._db.cursor()
				#获取count
				cursor.execute(sql_count)
				count = cursor.fetchone()['number']
				#获取rows
				cursor.execute(sql)
				result = cursor.fetchall()
				self._db.close()
				del cursor
				return {'count': count, 'rows': result}
			except Exception as e:
				self._db.close()
				print(e)
				logging.debug('find_data: ' + str(e))
				exit()

	#插入数据
	def insert_data(self, table_name, list_data):
		self._db_connect()
		try:
			sql = 'insert into ' + table_name
			tuple_title = tuple(list_data[0].keys())
			str_title = re.sub(r'\'', '`', str(tuple_title))
			sql += str_title
			sql += ' values '
			int_num = 1
			for item in list_data:
				tuple_data = tuple(item.values())
				str_data = str(tuple_data)
				sql += str_data
				if int_num < len(list_data):
					sql += ', '
				int_num += 1
			logging.debug('sql: ' + sql)

			cursor = self._db.cursor()
			cursor.execute(sql)
			self._db.commit()
			self._db.close()
			del cursor
			return True

		except Exception as e:
			self._db.rollback()
			self._db.close()
			logging.debug('insert_data: ' + str(e))
			exit()	
	
	#修改数据
	def update_data(self, table_name, whereJson, updateJson):
		self._db_connect()
		try:
			sql = 'update ' + table_name
			int_num = 1
			updateStr = ''
			whereStr = ''
			for k in whereJson:
				value = whereJson[k]
				if type(value) == int or type(value) == float:
					whereStr += k+' = '+str(value)+' and '
				elif type(value) == str:
					whereStr += k+' = "'+value+'" and '
				else:
					pass
			whereStr = whereStr[0:len(whereStr)-5]
			for key in updateJson.keys():
				if type(updateJson[key]) == int or type(updateJson[key]) == float:
					updateStr += '`' + key + '`' + '=' + str(updateJson[key])
				else:
					updateStr += '`' + key + '`' + '=\'' + updateJson[key] + '\''
				if int_num < len(updateJson):
					updateStr += ','
				int_num += 1

			sql += ' set ' + updateStr + ' where ' + whereStr
			logging.debug('sql: ' + sql)
			cursor = self._db.cursor()
			cursor.execute(sql)
			self._db.commit()
			self._db.close()
			del cursor
			return True
		except Exception as e:
			self._db.rollback()
			self._db.close()
			logging.debug('update_data: ' + str(e))
			exit()	
	
	#del_data
	def del_data(self, table_name, dict_where):
		self._db_connect()
		try:
			field = ''
			for key in dict_where:
				field = key
			str_data = '('
			int_num = 1
			for item in dict_where[field]:
				if type(item) == int:
					str_data += str(item)
				else:
					str_data += ('"' + item + '"')
				if int_num < len(dict_where[field]):
					str_data += ','
				int_num += 1
			str_data += ')'
			sql = 'delete from ' + table_name + ' where ' + field + ' in ' + str_data
			logging.debug('sql: ' + sql)
			
			cursor = self._db.cursor()
			cursor.execute(sql)
			self._db.commit()
			self._db.close()
			del cursor
			return True

		except Exception as e:
			self._db.rollback()
			self._db.close()
			logging.debug('del_data: ' + str(e))
			exit()

# if __name__ == "__main__":
#     mymodel = model()
