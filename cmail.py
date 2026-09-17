import smtplib
from email.message import EmailMessage
def send_mail(to,subject,body):
    server=None
    try:
        server=smtplib.SMTP_SSL('smtp.gmail.com',465) #creating object to gmail server using port number
        server.login('anusha@codegnan.com','xfjg nbej hirf lqbi')
        msg=EmailMessage()
        msg['FROM']='anusha@codegnan.com'
        msg['TO']=to
        msg['SUBJECT']=subject
        msg.set_content(body)
        server.send_message(msg)
        print('otp sent')
    except Exception as e:
        print('Error in email automation',str(e))
    finally:
        if server:
            server.close()
