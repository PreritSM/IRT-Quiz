from flask import Flask,request,render_template,redirect,url_for,flash,session
import time
from werkzeug.utils import secure_filename
import os
from sklearn.preprocessing import OneHotEncoder
import itertools
from flaskext.mysql import MySQL
import pymysql
import numpy as np
import tensorflow as tf
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import random
from datetime import timedelta
import re
from girth import ability_mle



model = tf.keras.models.load_model('paper-gen-model')


SESSION_PERMANENT= True



app = Flask(__name__)
mysql = MySQL(app, prefix="our_database", host="localhost", user="root",
    password="Psmballer@29", db="TarahTech",
    autocommit=True)

app.config['UPLOAD_FOLDER'] = 'UPLOAD_FOLDER'
app.secret_key = 'tarahtech'
app.permanent_session_lifetime = timedelta(minutes=7)

mysql.init_app(app)

cursor = mysql.connect().cursor()
cursor.execute("SELECT * from Questions")
records=cursor.fetchall()


"""columns = ('Id','Questions','A','B','C','D','Correct','Subjects','Difficulty')
res = {columns[i] : test_tup2[i] for i, _ in enumerate(test_tup2)}"""
def quiz_generator(response,time,subject,present_difficulty):
    result=[response,present_difficulty,time]


    cateries=np.asarray([['ML'],
 ['DL'],
 ['DataViz'],
 ['Statistics'],
 ['Numpy'],
 ['Pandas'],
 ['Pattern Recognition'],
 ['Data Mining'],
 ['Basics']])
    onehot_encoder = OneHotEncoder(sparse=False)
    onehot_encoded = onehot_encoder.fit_transform(cateries)
    k=onehot_encoder.transform(subject)
    k=k.flatten().tolist()
    ans=[]
    for i in itertools.chain(result,k):
        ans.append(round(i))
    ans=np.asarray(ans)
    ans=np.asarray([ans])
    return ans


@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/paper-upload",methods=["GET","POST"])
def upload():

    if request.method == 'POST':
        if 'csvfile' not in request.form:
            flash('there is no csv in form!')
        csvfile = request.files['csvfile']
        filename = secure_filename(csvfile.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
        csvfile.save(path)
        return render_template("upload.html")

    else :
        return render_template("upload.html")


@app.route("/student_comp",methods=["GET","POST"])
def compare():
    if request.method == 'POST':
        number=request.form['quantity']
        session['numbers']=number
        print(number)
        names=request.form['USERNAMES']
        names=names.split(',')
        traits={}
        for i in names:
            cursor.execute('SELECT * FROM Response WHERE username = %s ', (i))
            details = cursor.fetchall()
            print(details)
            res_ac=[]
            for i in details:
                res_ac.append(i[1])
            res_a=[]
            for i in res_ac:
                if i == '1':
                    res_a.append(True)
                else:
                    res_a.append(False)
            res_a=np.asarray(res_a)
            res_a=res_a[:,None]
            print(res_a.shape)
            print(res_a.dtype)
            irt_res = res_a
            diff_a=[]
            for i in details:
                diff_a.append(i[2])
            diff_a= np.asarray(diff_a)
            irt_dc=np.ones(len(diff_a))
            print(irt_res)
            print(irt_res.shape)
            print(diff_a)
            print(irt_dc)
            as1=ability_mle(irt_res, diff_a, irt_dc)[0]
            as1 = 1/(1+np.exp(-as1))
            print("Ability of student is :", 5*as1)
            traits[i[0]]=round(5*as1,2)
        print(traits)
        return render_template("comp_display.html",traits=traits)

    else:
        return render_template("comp.html")

@app.route("/test",methods=["GET", "POST"])
def test_paper():
    if 'marks' not in session.keys():
        session['marks']=0
        session.permanent=True

    print('ite' in session.keys())
    if 'ite' not in session.keys():
        session['ite']=0
        session.permanent=True
    if request.method =='GET':
        print(session['ite'])
        if session['ite']==0:
            session['start_time']=time.time()
            question=records[0]
            session['questions_set']=question
            return render_template("paper.html",data=question[1],options=question[2:6])
        elif session['ite']<5:
            session['start_time']=time.time()
            return render_template("paper.html",data=session['questions_set'][1],options=session['questions_set'][2:6])
        else :
            session.pop('ite')
            session.pop("questions_set")
            session.pop("start_time")
            score=session['marks']
            session.pop('marks')
            return render_template('results.html',score=score)
    else:
        time_diff=time.time()-session['start_time']
        value = request.form["answer"]
        if value == session['questions_set'][6]:
            response=1
            val_res=True
            session['marks']=session['marks']+1
        else:
            response=0
            val_res=False
        print('response={}'.format(response))
        cursor.execute('INSERT INTO Response VALUES (%s,%s,%s)',(session['username'],val_res,int(session['questions_set'][-1])))
        inputs=quiz_generator(response,time_diff,[[session['questions_set'][7]]],session['questions_set'][8])
        fut_diff=model.predict(inputs)
        fut_diff=np.argmax(np.round(fut_diff),axis=1)
        if fut_diff[-1]==0:
            tough=1
        else:
            tough=fut_diff[-1]
        ans=[i for i, n in enumerate(records) if n[8]==tough]

        r1=random.randint(0,len(ans))
        print(r1)
        print(session['questions_set'])
        session['questions_set']=records[ans[r1]]
        print(session['questions_set'])
        session['ite']=session['ite']+1
        return redirect('/test')

@app.route("/")
@app.route('/login', methods=['GET', 'POST'])
def login():

    msg = ''

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:

        username = request.form['username']
        password = request.form['password']


        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))

        account = cursor.fetchone()

        if account:
            print(account)
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]

            msg= 'Logged in successfully!'
            return redirect(url_for('home'))
        else:

            msg = 'Incorrect username/password!'

    return render_template('newlogin.html', msg=msg)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('home'))

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts (username,password,email) VALUES (% s, % s, % s)', (username, password, email))
            msg = 'You have successfully registered !'
            return redirect(url_for('login'))
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('newregister.html', msg = msg)


if __name__ == "__main__":
    app.run(debug=True)

