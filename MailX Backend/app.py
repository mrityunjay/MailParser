from flask import Flask
from flask import jsonify, request
from flask_cors import CORS
from email.parser import Parser
from db import execute_query
from email import message_from_bytes
from email import message_from_string
from hashlib import sha256
import pandas as pd
from flask_mysqldb import MySQL
import json
import random
import re
import os
import shutil

with open('./params.json') as param_file:
    params = json.loads(param_file.read())

host = params['DB_HOST']
user = params['DB_USER']
password = params['DB_PASS']
driver = params['DB_DRIVER']
database_name = params['DB_NAME']
connection_string = params['CONN_STRING']
cursor_class = params['MYSQL_CURSORCLASS']
data_src = params['DATA_SOURCE']
output_folder = params['OUTPUT_FOLDER']

GLOBAL_DATABASE = database_name

app = Flask(__name__)
CORS(app)
# config mysql
app.config['MYSQL_HOST'] = host
app.config['MYSQL_USER'] = user
app.config['MYSQL_PASSWORD'] = password
app.config['MYSQL_DB'] = database_name
app.config['MYSQL_CURSORCLASS'] = cursor_class

# init mysql
mysql = MySQL(app)

parser = Parser()


def classify(body):
    df = pd.read_csv('emails.csv')
    # df.head()

    df = df[pd.notnull(df['message'])]

    # df.info()

    col = ['Category', 'message']
    df = df[col]

    df.columns

    df.columns = ['Category', 'message']

    df['category_id'] = df['Category'].factorize()[0]
    from io import StringIO
    category_id_df = df[['Category', 'category_id']].drop_duplicates().sort_values('category_id')
    category_to_id = dict(category_id_df.values)
    id_to_category = dict(category_id_df[['category_id', 'Category']].values)

    # df.head()

    # import matplotlib.pyplot as plt
    # fig = plt.figure(figsize=(8, 6))
    # df.groupby('Category').message.count().plot.bar(ylim=0)
    # plt.show()

    from sklearn.feature_extraction.text import TfidfVectorizer

    tfidf = TfidfVectorizer(sublinear_tf=True, min_df=5, norm='l2', encoding='latin-1', ngram_range=(1, 2),
                            stop_words='english')

    features = tfidf.fit_transform(df.message).toarray()
    labels = df.category_id
    features.shape

    from sklearn.model_selection import train_test_split
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.feature_extraction.text import TfidfTransformer
    from sklearn.naive_bayes import MultinomialNB

    X_train, X_test, y_train, y_test = train_test_split(df['message'], df['Category'], random_state=0)
    count_vect = CountVectorizer()
    X_train_counts = count_vect.fit_transform(X_train)
    tfidf_transformer = TfidfTransformer()
    X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)

    clf = MultinomialNB().fit(X_train_tfidf, y_train)

    return (clf.predict(count_vect.transform([body])))


@app.route('/')
def mailx():
    return 'MailX API'


@app.route('/get_categories', methods=['POST', 'GET'])
def add_category():
    cat_list = []
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT `categories` from emails")
    res = cur.fetchall()
    print('res')
    cur.close()
    for row in res:
        cat_list.append(row['categories'])
    return jsonify({"categories":cat_list})


@app.route('/get_cat_mails/<category>', methods=['POST', 'GET'])
def get_cat_mails(category):
    print('get mails', category)
    cur = mysql.connection.cursor()
    cur.execute("SELECT * from emails WHERE `categories`=%s", [category])
    res = cur.fetchall()
    # print(type(res), ' ', res)
    cur.close()
    for row in res:
        try:
            labels = json.loads(row['labels'])
            labels = set(labels)
        except:
            labels = []
        label_str = ','.join(labels)
        row['labels'] = label_str
    r = {"mails": res}
    cur.close()
    return jsonify(r)

@app.route('/extract', methods=['POST', 'GET'])
def extract():
    files = os.listdir(data_src)
    for file in files:
        s = open(data_src+'/'+file, 'r')
        s = s.read()
        mail = parser.parsestr(s)
        # print('mail is ', mail)
        email_from = mail.get('From')
        email_to = mail.get('To')
        subject = mail.get('Subject')
        # print('mail is ', mail.get('Date'))
        # print('From is ', mail.get('From'))
        # print('To is ', mail.get('To'))
        # print('Subject is ', mail.get('Subject'))
        if mail.is_multipart():
            for part in mail.get_payload():
                print(part.get_payload())
        else:
            body = mail.get_payload()
            print('Non multi is ', body)
        category = classify(body)
        try:
            category = category[0]
        except Exception as e:
            print('Category error ', e)
            category = ''
        try:
            labels = get_labels(body, subject)
            labels = json.dumps(labels)
        except Exception as e:
            print('Error getting labels ', e)
            labels = '[]'
        cur = mysql.connection.cursor()
        cur.execute('INSERT into emails(`case_id`, `subject`, `email_from`, `email_to`, `body`, `categories`, `labels`) values(%s,%s,%s,%s,%s,%s,%s)', (generate_caseid(subject), subject, email_from, email_to, body.strip(), category, labels))
        mysql.connection.commit()
        try:
            shutil.move(data_src+'/'+file, output_folder+'/'+file)
        except Exception as e:
            print('move error ',e)
            shutil.move(data_src + '/' + file, output_folder + '/' + file+str(random.randint(1,10000)))
    # cur.close()
    # # print('s is ', s)
    # m = message_from_string(s)
    # # print('From is ', m['from'])
    # print('to is ', m['body'])
    # print('m is ',m)
    # print('subject is  ', m['subject'])
    # p = parser.BytesParser()
    # b = p.parse(fp)
    # # print(m.get_body('plain'))
    # # print(type(m))
    # if b.is_multipart():
    #     for payload in b.get_payload():
    #         # if payload.is_multipart(): ...
    #         print('Multi is')
    #         print(payload.get_payload())
    # else:
    #     print('non multi is')
    #     print(b.get)
    #     print(b.get_payload())
    #     print('$$$$$ BODY IS ', b.get_payload().get_body())
    if files:
        cur.execute('SELECT * from emails')
        res = cur.fetchall()
        print(type(res), ' ', res)
        cur.close()
        r = {"data": res}
        return jsonify(r)
    else:
        return jsonify({"message": "Nothing to extract"})

def get_hex_code(file_path):

    file = open(file_path, 'rb')
    hasher = sha256()
    hasher.update(file.read())
    hex = hasher.hexdigest()
    file.close()
    return hex

@app.route('/add_label/<case_id>/<label>', methods=['POST', 'GET'])
def add_label(case_id, label):
    print('caseid is ', case_id)
    print('label is ', label)
    cur = mysql.connection.cursor()
    cur.execute(
        'SELECT `labels` FROM `emails` WHERE `case_id` = %s', [case_id])
    res = cur.fetchall()
    labels = res[0]['labels']
    try:
        labels = json.loads(labels)
    except:
        labels = []

    labels.append(label)
    cur = mysql.connection.cursor()
    cur.execute(
        'UPDATE emails SET `labels` = (%s) WHERE `case_id`=%s', [json.dumps(labels), case_id])
    mysql.connection.commit()
    cur.close()
    return jsonify({"message":"Label added successfully"})


def generate_caseid(subject):
    return subject+str(random.randint(1, 600000)).strip()

def parse_categories(category):
    return json.loads(category)


@app.route('/delete_label/<case_id>')
def delete_label(case_id):
    print('caseid is ', case_id)
    # print('label is ', label)
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            'UPDATE emails SET `labels` = %s WHERE `case_id`=%s', [json.dumps([]), case_id])
    except Exception as e:
        print('Error removing label ', e)
        return jsonify({"message": "Could not delete Label"})

    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "All labels deleted successfully"})


@app.route('/get_mails/<num>', methods=['POST', 'GET'])
def get_emails(num):
    print('num', num)
    print(type(num))
    num = num.strip()
    cur = mysql.connection.cursor()
    cur.execute("SELECT * from emails LIMIT %s", [int(num)])
    res = cur.fetchall()
    print('res')
    # print(type(res), ' ', res)
    cur.close()
    r = {"data": res}
    return jsonify(r)


def get_labels(message_body, subject):
    import requests

    # defining the api-endpoint
    API_ENDPOINT = "https://www.twinword.com/api/v6/text/classify/"

    body = message_body
    if not subject:
        subject = ""


    data = {'text': body,
            'title': subject}

    # sending post request and saving response as response object
    r = requests.post(url=API_ENDPOINT, data=data)

    # extracting response text
    data = r.json()

    return data['keywords']

if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0', debug=True)
