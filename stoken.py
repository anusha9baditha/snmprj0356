from itsdangerous import URLSafeTimedSerializer
secret_key='Code@789'
def endata(data):
    obj=URLSafeTimedSerializer(secret_key)
    return obj.dumps(data)
def dndata(data):
    obj=URLSafeTimedSerializer(secret_key)
    return obj.loads(data,max_age=180)
