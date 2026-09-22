from flask import Flask,request,render_template,redirect,url_for,flash
from otp import genotp
from cmail import send_mail
from datetime import datetime,timedelta
import mysql.connector
mydb=mysql.connector.connect(user='root',host='localhost',password='admin',database='snmprojectdb')
app=Flask(__name__)
app.secret_key=b'[\x99\xb2(\x82'
@app.route('/',methods=['GET'])
def home():
    return render_template('welcome.html')
@app.route('/register',methods=['GET','POST'])
def register():
    try:
        if request.method=='POST':
            print(request.form) #immutablemultidict
            username=request.form.get('username').strip()
            useremail=request.form['useremail'].strip()
            userpassword=request.form['userpassword']
            server_otp=genotp() #'S6bE8m'
            otp_expiry_time=datetime.now()+timedelta(minutes=5) #10+5==10.5
            cursor=mydb.cursor()
            cursor.execute('select userid,account_status,otp_expiry_time from userdata where useremail=%s',[useremail])
            db_response=cursor.fetchone() #(1,'active','')#case 1:101,'active',case2:101,'inactive','otp expired',case3:101,'inactive',otp has time
            print(db_response) #none
            if db_response:
                if db_response[1]=='active':
                    flash('user already existed')
                    return redirect(url_for('register'))
                elif db_response[1]=='inactive' and otp_expiry_time > db_response[2]:
                    cursor.execute('update userdata set username=%s,userpassword=%s,otp=%s,otp_expiry_time=%s,account_status=%s where useremail=%s',[username,userpassword,server_otp,otp_expiry_time,'inactive',useremail])
            else:
                cursor.execute('insert into userdata(username,useremail,userpassword,otp,otp_expiry_time,account_status) values(%s,%s,%s,%s,%s,%s)',[username,useremail,userpassword,server_otp,otp_expiry_time,'inactive'])
            mydb.commit()
            cursor.close()
            subject=f'User verification otp for Simple Notes Management system '
            body=f'use the given otp for : {server_otp}'
            send_mail(to=useremail,subject=subject,body=body)
            flash('OTP has been sent to given mail')
            return redirect(url_for('otpverify',useremail=useremail))
        return render_template('register.html')
    except Exception as e:
        print('Mysql Error',str(e))
        flash('Could not store user details')
        return redirect(url_for('register'))
@app.route('/login',methods=['GET','POST'])
def login():
    return render_template('login.html')
@app.route('/otpverify/<useremail>',methods=['GET','POST'])
def otpverify(useremail):
    if request.method=='POST':
        userotp=request.form['userotp']
        user_otp_time=datetime.now()
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select userid,account_status,otp,otp_expiry_time from userdata where useremail=%s',[useremail])
        db_response=cursor.fetchone() 
        print(db_response) #none
        if db_response:
            if db_response[1]=='active':
                flash('user already existed')
                return redirect(url_for('otpverify',useremail=useremail))
            elif db_response[1]=='inactive' and user_otp_time > db_response[3]:
                flash('OTP expired')
                return redirect(url_for('otpverify',useremail=useremail))
            elif db_response[1]=='inactive' and user_otp_time <db_response[3]:
                if db_response[2]==userotp:
                    cursor.execute('update userdata set otp=null,otp_expiry_time=null,account_status=%s where useremail=%s',['active',useremail])
                    mydb.commit()
                    flash('OTP Verified')
                    return redirect(url_for('login'))
                else:
                    flash('OTP Invalid pls try again')
                    return redirect(url_for('otpverify',useremail=useremail))
        else:
            flash('User Not found in DB')
            return redirect(url_for('otpverify',useremail=useremail))
    return render_template('otp.html')
@app.route('/dashboard',methods=['GET'])
def dashboard():
    return render_template('home.html')
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    return render_template('add_notes.html')
@app.route('/viewall_notes',methods=['GET','POST'])
def viewall_notes():
    return render_template('all_notes.html')
app.run(debug=True,use_reloader=True)