from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
from io import BytesIO
import flask_excel as excel
from flask_session import Session #security layer to create server side session
from otp import genotp
from cmail import send_mail
from datetime import datetime,timedelta
import mysql.connector
import re
mydb=mysql.connector.connect(user='root',host='localhost',password='admin',database='snmprojectdb')
app=Flask(__name__)
excel.init_excel(app) #initialize app with excel
app.secret_key=b'[\x99\xb2(\x82'
app.config['SESSION_TYPE']='filesystem'
Session(app)
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
    if request.method=='POST':
        login_email=request.form['useremail']
        login_password=request.form['userpassword']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select account_status,userpassword from userdata where useremail=%s',[login_email])
        data=cursor.fetchone() #('active','123')
        if data:
            if data[0]=='active':
                if data[1]==login_password:
                    print(session,'before login')
                    session['user']=login_email #creating session data like dictionary 
                    print(session,'after session creation') 
                    flash('Login Successfull')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Password Invalid')
                    return redirect(url_for('login'))
            elif data[0]=='inactive':
                flash('pls verify account using otp')
                return redirect(url_for('otpverify',useremail=login_email))
        else:
            flash('No user found')
            return redirect(url_for('register'))
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
    if not session.get('user'):
        return redirect(url_for("login"))
    return render_template('home.html')
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    try:
        if not session.get('user'):
            flash('pls login to add notes')
            return redirect(url_for('login'))
        if request.method=='POST':
            title=request.form['noteTitle']
            content=request.form['noteContent']
            useremail=session.get('user')
            mydb.ping(reconnect=True)
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into notesdata(title,Content,userid) values(%s,%s,(select userid from userdata where useremail=%s))',[title,content,useremail])
            mydb.commit()
            flash('Notes added successfully')
            return redirect(url_for('addnotes'))
        return render_template('add_notes.html')
    except Exception as e:
        print(e)
        flash('Could not add notes to Db ',str(e))
        return redirect(url_for('dashboard'))
@app.route('/viewall_notes',methods=['GET'])
def viewall_notes():
    try:
        if not session.get('user'):
            flash('pls login to add notes')
            return redirect(url_for('login'))
        useremail=session.get('user')
        mydb.ping(reconnect=True)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select notesid,title,created_at from notesdata where userid=(select userid from userdata where useremail=%s)',[useremail])
        notesdata=cursor.fetchall() #list of tuple[(2 , python ,2026-09-24 10:26:40 ),(3, mysql,2026-09-24 10:43:58)] or []
        print(notesdata)
        return render_template('all_notes.html',notesdata=notesdata)
    except Exception as e:
        print(e)
        flash('Could not all notes data from Db ',str(e))
        return redirect(url_for('dashboard'))

@app.route('/viewnotes/<notesid>',methods=['GET'])
def viewnotes(notesid):
    try:
        if not session.get('user'):
            flash('pls login to add notes')
            return redirect(url_for('login'))
        useremail=session.get('user')
        mydb.ping(reconnect=True)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select notesid,title,content,created_at from notesdata where userid=(select userid from userdata where useremail=%s) and notesid=%s',[useremail,notesid])
        notesdata=cursor.fetchone() #[(2 , python ,2026-09-24 10:26:40 )]
        print(notesdata)
        return render_template('viewnotes.html',notesdata=notesdata)
    except Exception as e:
        print(e)
        flash('Could not view notes from Db ',str(e))
        return redirect(url_for('viewallnotes'))
@app.route('/deletenotes/<notesid>',methods=['GET'])
def deletenotes(notesid):
    try:
        if not session.get('user'):
            flash('pls login first')
            return redirect(url_for('login'))
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from notesdata where notesid=%s and userid=(select userid from userdata where useremail=%s)',[notesid,session.get('user')])
        notescount=cursor.fetchone() #(1,)
        if not notescount:
            flash('No Notes found in DB')
            return redirect(url_for('viewall_notes'))
        cursor.execute('delete from notesdata where notesid=%s and userid=(select userid from userdata where useremail=%s)',[notesid,session.get('user')])
        mydb.commit()
        flash('Notes deleteed successfully')
        return redirect(url_for('viewall_notes'))
    except Exception as e:
        print(e)
        flash('Could not delete from Db ',str(e))
        return redirect(url_for('viewallnotes'))
@app.route('/updatenotes/<notesid>',methods=['GET','POST'])
def updatenotes(notesid):
    try:
        if not session.get('user'):
            flash('pls login to add notes')
            return redirect(url_for('login'))
        useremail=session.get('user')
        mydb.ping(reconnect=True)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select notesid,title,content,created_at from notesdata where userid=(select userid from userdata where useremail=%s) and notesid=%s',[useremail,notesid])
        notesdata=cursor.fetchone() #[(2 , python ,2026-09-24 10:26:40 )]
        print(notesdata)
        if request.method=='POST':
            updated_title=request.form['noteTitle']
            updated_content=request.form['noteContent']
            cursor.execute('update notesdata set title=%s,content=%s where notesid=%s and userid=(select userid from userdata where useremail=%s)',[updated_title,updated_content,notesid,session.get('user')])
            mydb.commit()
            flash('Notes updated successfully')
            return redirect(url_for('viewnotes',notesid=notesid))
        return render_template('updatenotes.html',notesdata=notesdata)
    except Exception as e:
        print(e)
        flash('Could not Update from Db ',str(e))
        return redirect(url_for('viewallnotes'))
@app.route('/fileupload',methods=['GET','POST'])
def uploadfile():
    try:
        if not session.get('user'):
            flash('pls login first')
            return redirect(url_for('login'))
        if request.method=='POST':
            filedata=request.files.get('userfile')
            fdata=filedata.read()
            fname=filedata.filename
            mydb.ping(reconnect=True)
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into filesdata(filename,filedata,userid) values(%s,%s,(select userid from userdata where useremail=%s))',[fname,fdata,session.get('user')])
            mydb.commit()
            flash('file uploaded successfully')
            return redirect(url_for('uploadfile'))
        return render_template('uploadfile.html')
    except Exception as e:
        print(e)
        flash('Could not upload filke into Db ',str(e))
        return redirect(url_for('uploadfile'))
@app.route('/viewall_files',methods=['GET'])
def viewall_files():
    try:
        if not session.get('user'):
            flash('pls login to add notes')
            return redirect(url_for('login'))
        useremail=session.get('user')
        mydb.ping(reconnect=True)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select fileid,filename,created_at from filesdata where userid=(select userid from userdata where useremail=%s)',[useremail])
        filesdata=cursor.fetchall() #list of tuple[(2 , python ,2026-09-24 10:26:40 ),(3, mysql,2026-09-24 10:43:58)] or []
        return render_template('all_files.html',filesdata=filesdata)
    except Exception as e:
        print(e)
        flash('Could not viewallfiles from Db ',str(e))
        return redirect(url_for('dashboard'))
@app.route('/viewfile/<fileid>',methods=['GET'])
def viewfile(fileid):
    try:
        if not session.get('user'):
            flash('pls login to add notes')
            return redirect(url_for('login'))
        useremail=session.get('user')
        mydb.ping(reconnect=True)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select fileid,filename,filedata,created_at from filesdata where userid=(select userid from userdata where useremail=%s) and fileid=%s',[useremail,fileid])
        file_data=cursor.fetchone() 
        fdata=BytesIO(file_data[2])
        return send_file(fdata,as_attachment=False,download_name=file_data[1])
    except Exception as e:
        print(e)
        flash('Could not view file from Db ',str(e))
        return redirect(url_for('viewallfiles'))
@app.route('/downloadfile/<fileid>',methods=['GET'])
def downloadfile(fileid):
    try:
        if not session.get('user'):
            flash('pls login to add notes')
            return redirect(url_for('login'))
        useremail=session.get('user')
        mydb.ping(reconnect=True)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select fileid,filename,filedata,created_at from filesdata where userid=(select userid from userdata where useremail=%s) and fileid=%s',[useremail,fileid])
        file_data=cursor.fetchone() 
        fdata=BytesIO(file_data[2])
        return send_file(fdata,as_attachment=True,download_name=file_data[1])
    except Exception as e:
        print(e)
        flash('Could not download file from Db ',str(e))
        return redirect(url_for('viewallfiles'))
@app.route('/deletefile/<fileid>',methods=['GET'])
def deletefile(fileid):
    try:
        if not session.get('user'):
            flash('pls login first')
            return redirect(url_for('login'))
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from filesdata where fileid=%s and userid=(select userid from userdata where useremail=%s)',[fileid,session.get('user')])
        filecount=cursor.fetchone() #(1,)
        if not filecount:
            flash('No file found in DB')
            return redirect(url_for('viewall_files'))
        cursor.execute('delete from filesdata where fileid=%s and userid=(select userid from userdata where useremail=%s)',[fileid,session.get('user')])
        mydb.commit()
        flash('file deleted successfully')
        return redirect(url_for('viewall_files'))
    except Exception as e:
        print(e)
        flash('Could not delete from Db ',str(e))
        return redirect(url_for('viewall_files'))
@app.route('/getexceldata',methods=['GET'])
def getexceldata():
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    mydb.ping(reconnect=True)
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from notesdata where userid=(select userid from userdata where useremail=%s)',[session.get('user')])
    user_notesdata=cursor.fetchall()
    if not user_notesdata:
        flash('No notes found')
        return redirect(url_for('dashboard'))
    array_data=[list(i) for i in user_notesdata] #convert into listoflist
    headings=['Notesid','Title','Content','Created_at','added_by']
    array_data.insert(0,headings)
    return excel.make_response_from_array(array_data,'xlsx',download_name='Exceldata')
@app.route('/searchdata',methods=['POST'])
def searchdata():
    try:
        user_searchdata=request.form['sdata'] #'a'
        strg=['A-Za-z0-9']
        pattern=re.compile(f'^{strg}',re.IGNORECASE) #'asds 8 SDFG'
        if pattern.match(user_searchdata):
            mydb.ping(reconnect=True)
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select notesid,title,created_at from notesdata where (notesid like %s or title like %s or created_at like %s) and userid=(select userid from userdata where useremail=%s)',[user_searchdata+'%',user_searchdata+'%',user_searchdata+'%',session.get('user')])
            search_result=cursor.fetchall() #[(),()]
            if not search_result:
                flash('no search data')
                return redirect(url_for('dashboard'))
            return render_template('searchresult.html',search_result=search_result)
        else:
            flash('Invalid searchdata')
            return redirect(url_for('dashboard'))
    except Exception as e:
        print(e)
        flash('Could not fetch search data',str(e))
        return redirect(url_for('dashboard'))

@app.route('/forgot',methods=['GET','POST'])
def forgot():
    try:
        if request.method=='POST':
            forgot_email=request.form['useremail']
            mydb.ping(reconnect=True)
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select account_status from userdata where useremail=%s',[forgot_email])
            user_status=cursor.fetchone()
            if not user_status:
                flash('could not connect to db')
                return redirect(url_for('forgot'))
            if user_status[0]=='inactive':
                flash('User not verified')
                return redirect(url_for('register'))
            if user_status[0]=='suspended':
                flash('User is Suspended')
                return redirect(url_for('home'))
            if user_status[0]=='active':
                resetlink=f"Use the given link for forgot password {url_for('newpassword',useremail=forgot_email,_external=True)}"
                subject='ResetLink for SNM Project'
                send_mail(to=forgot_email,body=resetlink,subject=subject)
                flash('Resetlink has been sent to given mail')
                return redirect(url_for('forgot'))
            
        return render_template('forgot.html')
    except Exception as e:
        print(str(e))
        flash('Could not send resetlink')
        return redirect(url_for('forgot'))
@app.route('/newpassword/<useremail>')
def newpassword(useremail):
    return 'hi'
app.run(debug=True,use_reloader=True)