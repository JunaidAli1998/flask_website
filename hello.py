from flask import Flask,render_template,request,session,redirect
import pyodbc
from flask_mail import Mail
from werkzeug import secure_filename
import os
import json
import pandas as pd
from datetime import datetime

with open('config.json','r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'flask-secret-key'
app.config['UPLOAD_FOLDER'] = params['uploader_location']
app.config.update(
    MAIL_SERVER ='smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)

mail= Mail(app)

if(local_server):
    connStr = pyodbc.connect('DRIVER={ODBC Driver 13 for SQL Server};SERVER=DESKTOP-CF5EPQL\SQLEXPRESS;'
                             'DATABASE=Students;Trusted_Connection=yes')
else:
    connStr = pyodbc.connect('DRIVER={ODBC Driver 13 for SQL Server};SERVER=DESKTOP-CF5EPQL\SQLEXPRESS;'
                             'DATABASE=Students;Trusted_Connection=yes')
cursor = connStr.cursor()

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        cursor.execute("Select * from dbo.post")
        posts = cursor.fetchall()
        return render_template('dashboard.html',params = params,posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params['admin_user'] and userpass == params['admin_password']):
            session['user'] = username
            cursor.execute("Select * from dbo.post")
            posts = cursor.fetchall()
            return render_template('dashboard.html', params=params,posts=posts)
    else:
        return render_template('login.html',params=params)

@app.route("/")
def home():
    cursor.execute("Select * from dbo.post where [sno] <= '16'")
    posts=cursor.fetchall()
    return render_template('index.html',params=params,posts=posts)

@app.route("/uploader", methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "uploaded successfully"

@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            title = request.form.get('Title')
            body = request.form.get('Body')
            slug = request.form.get('slug')
            Image = request.form.get('img_file')

            if sno == '0':
               cursor.execute("INSERT INTO dbo.post([title],[body],[date],[slug],[url_image]) "
                              "values  (?,?,?,?,?)", title, body, datetime.now(), slug, Image)
               connStr.commit()
            else:
                cursor.execute("update dbo.post set title=?,body=?,date=?,slug=?,url_image=? where sno=?",
                               title,body,datetime.now(), slug, Image, sno)
                connStr.commit()
                return redirect('/edit/'+sno)
        cursor.execute("Select * from dbo.post where [sno] = '" + sno + "'")
        post =cursor.fetchone()

        return render_template('edit.html', params=params,post=post)




@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    cursor.execute("update dbo.post set date =?", datetime.now())
    connStr.commit()

    query = "Select * from dbo.post where [slug] = '"+ post_slug+"'"
    df=pd.read_sql(query,connStr)
    post=df.iloc[0]

    return render_template('post.html',params=params, post=post)

@app.route("/about")

def about():
    return render_template('about.html',params=params)



@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if (request.method == 'POST'):

        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        # entry = Contacts(name=name, phone_num=phone, msg=message, date=datetime.now(), email=email)
        cursor.execute("INSERT INTO dbo.Contacts([name],[phone_num],[date],[msj],[email]) "
                       "values  (?,?,?,?,?)",name,phone,datetime.now(),message,email)

        connStr.commit()
        mail.send_message('New message from '+ name ,
                          sender = email,
                          recipients = [params['gmail-user']],
                          body = message + "\n" + phone
                            )


    return render_template('contact.html',params=params)

@app.route("/logout")

def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        cursor.execute("Delete from dbo.post where sno = '"+sno+"'")
        connStr.commit()
    return  redirect('/dashboard')

@app.route("/add", methods=['GET','POST'])
def add():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            title = request.form.get('Title')
            body = request.form.get('Body')
            slug = request.form.get('slug')
            Image = request.form.get('img_file')
            cursor.execute("INSERT INTO dbo.post([title],[body],[date],[slug],[url_image]) "
                              "values  (?,?,?,?,?)", title, body, datetime.now(), slug, Image)
            connStr.commit()

        return render_template('add.html', params=params)

app.run(debug=True)