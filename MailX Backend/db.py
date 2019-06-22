"""
Author: Harshavardhan
"""
import json
import pymysql

with open('./params.json') as param_file:
    params = json.loads(param_file.read())

host = params['DB_HOST']
user = params['DB_USER']
password = params['DB_PASS']
driver = params['DB_DRIVER']
database_name = params['DB_NAME']
connection_string = params['CONN_STRING']
cursor_class = params['MYSQL_CURSORCLASS']


GLOBAL_DATABASE = 'mailx'


def execute_query(sql, database=GLOBAL_DATABASE):
    data = None
    conn = pymysql.connect(host=host, user=user, password=password, db=database)
    try:
        a = conn.cursor()
        a.execute(sql)
        data = a.fetchall()
        conn.commit()
    except Exception as e:
        print("Query execution exception ", e)
        conn.rollback()
    conn.close()
    return data
