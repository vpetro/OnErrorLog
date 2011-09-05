from pymongo import Connection
import datetime
import hashlib

def _encrypt_password(username, password):
    salt = username[:3] + password[2:]
    return hashlib.sha1(salt + password).hexdigest()

def create_user(username, password, email_address, company_name):
    
    db = Connection()['onerrorlog']

    account = db['accounts'].find_one({'username': username })
    if account: return None

    account = db['accounts'].find_one({'email_address': email_address })
    if account: return None
  
    password = _encrypt_password(username, password)

    d = {'username': username,
         'password': password,
         'email_address': email_address,
         'company_name': company_name,
         'insert_date': datetime.datetime.utcnow()
        }

    _id = db['accounts'].save(d)
    
    d['_id'] = _id

    return setup_account(d)

def verify_user(username, password):

    db = Connection()['onerrorlog']

    password = _encrypt_password(username, password)
    
    account = db['accounts'].find_one({
                  'username': username, 
                  'password': password
                  })
    
    if not account: return None

    return setup_account(account)
   

def setup_account(account):

    account.pop('insert_date')
    account['_id'] = str(account['_id'])

    return account
