from flask import Flask,request,render_template
from otp import genotp
from cmail import send_mail
app=Flask(__name__)
@app.route('/',methods=['GET'])
def home():
    return render_template('welcome.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        print(request.form) #immutablemultidict
        username=request.form.get('username').strip()
        useremail=request.form['useremail'].strip()
        userpasswor=request.form['userpassword']
        server_otp=genotp() #'S6bE8m'
        subject=f'User verification otp for Simple Notes Management system '
        body=f'use the given otp for : {server_otp}'
        send_mail(to=useremail,subject=subject,body=body)
        return 'OTP has been sent to given mail'
    return render_template('register.html')
@app.route('/login',methods=['GET','POST'])
def login():
    return render_template('login.html')
@app.route('/otpverify',methods=['GET','POST'])
def otpverify():
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