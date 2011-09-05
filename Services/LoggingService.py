from pymongo import Connection
from pymongo.objectid import ObjectId
from Packages.mongodbsearch import mongodbsearch
from Services import Database
import datetime

SEVERITY_CRITICAL = 0
SEVERITY_ERROR = 1
SEVERITY_INFO = 2
SEVERITY_DEBUG = 3

def _validate_key(key):
    accounts = Database.Instance().accounts()
    account = accounts.find_one({'_id': ObjectId(key) })

    if not account: return False

    return True

def insert_application(key, application):
    applications = Database.Instance().applications()

    d = {'key': key, 'application': application }
    app = applications.find_one(d)

    if not app:
        d['count'] = 1
        return applications.save(d)

    return app['_id']

def get_application_by_id(key, application_id):
    applications = Database.Instance().applications()

    if type(application_id) == type(u'') or type(application_id) == type(''):
        application_id = ObjectId(application_id)

    d = {'key': key, '_id': application_id }
    app = applications.find_one(d)

    if not app:
        return None

    return app

def get_applications(key):
    applications = Database.Instance().applications()

    return applications.find({'key': key })

def get_first_application(key):
    applications = Database.Instance().applications()

    return applications.find_one({'key': key })

def get_severity_string(severity):
    severity = int(severity)

    if severity == SEVERITY_CRITICAL:
        return 'Critical'
    elif severity == SEVERITY_ERROR:
        return 'Error'
    elif severity == SEVERITY_INFO:
        return 'Info'
    
    return 'Debug'

def check_severity(severity):
    if int(severity) not in [SEVERITY_CRITICAL, SEVERITY_ERROR, SEVERITY_INFO, SEVERITY_DEBUG]:
        raise KeyError('Severity has an invalid value')

def insert_exception(d):

    exceptions = Database.Instance().exceptions()
    exception_groups = Database.Instance().exception_groups()
    applications = Database.Instance().applications()

    #Check for required keys
    required_fields = ['key', 'message', 'application', 'severity']
    if len(list(set(required_fields) & set(d))) != len(required_fields):
        raise KeyError('Some required fields are missing') 

    check_severity(d['severity'])

    #Validate the key which was passed
    if not _validate_key(d['key']):
        raise KeyError('The key you specified is invalid')

    application_name = d['application']
    d['application'] = insert_application(d['key'], d['application'])


    if 'stacktrace' not in d:
        d['stacktrace'] = ''

    #Setup the string to be hashed
    hash_string = '%s\n%s\n%s\n%s' % (d['key'], 
                                   d['severity'],
                                   str(d['stacktrace']),
                                   d['message'])

    #Has the string
    unique_hash = hash(hash_string)

    #Create and insert the exception record
    exception = d
    exception['insert_date'] = datetime.datetime.utcnow()
    exception['unique_hash'] = unique_hash

    exception_id = exceptions.save(exception)

    #Check if the exception group exists
    group = exception_groups.find_one({'unique_hash': unique_hash, 'status': False })
   
    #If Exception already exists, increment count
    if group:
        group['count'] += 1
        group['exceptions'].append(exception_id)
        group['status'] = False

    #Otherwise, create the exception group record
    else:
        group = { 'message': d['message'],
                  'severity': d['severity'],
                  'key': d['key'],
                  'application': d['application'],
                  'exceptions': [ exception_id ],
                  'unique_hash': unique_hash,
                  'status': False,
                  'count': 1,
                  'insert_date': datetime.datetime.utcnow(),
                  'filename': d['filename'],
                  'stacktrace': d['stacktrace'],
                }

        applications.update({'_id': d['application'] }, {'$inc': {'count': 1 } })

    #Set the last seen_date
    group['last_seen_on'] = datetime.datetime.utcnow()

    #Save the exception group
    exception_group_id = exception_groups.save(group)

    #Update the Exception with the Exception Group Id
    exception['exception_group_id'] = exception_group_id
    exceptions.save(exception)

    exception_groups.ensure_index([('severity', 1), 
                                         ('application', 1), 
                                         ('key', 1), 
                                         ('unique_hash', 1), 
                                         ('status', 1 ), 
                                         ('last_seen_on', -1)
                                        ])

    exceptions.ensure_index([('severity', 1), 
                                   ('application', 1), 
                                   ('key', 1), 
                                   ('unique_hash', 1), 
                                   ('insert_date', -1),
                                  ])

    #Index the Document
    mdb_search = mongodbsearch.mongodb_search(Database.Instance().db())
    
    text = [d['message']]
    if 'headers' in d:
        for k, v in d['headers'].iteritems():
            text.append(k)
            text.append(v)

    if 'params' in d:
        for k, v in d['params'].iteritems():
            text.append(k)
            text.append(v)
    
    for s in d['stacktrace']:
        text.extend([str(x) for x in s.values()])

    kwargs = {'key': d['key'],
              'application': str(d['application']),
              'severity': d['severity'],
              'last_seen_on': group['last_seen_on'],
              'filename': d['filename'],
              'unique_hash': unique_hash
             }

    mdb_search.index_document(str(exception_group_id), ' '.join(text), ensureindex=kwargs.keys(), **kwargs)


    return exception_group_id, exception_id

def get_exceptions_groups(key, application, severity=None, status=False, start=0, maxrecs=10, since=None):

    exception_groups = Database.Instance().exception_groups()

    if type(application) == type(u''):
        application = ObjectId(application)

    query = {'key': key,
             'application': application,
             'status': status,
            }

    if severity:
        query['severity'] = severity

    if since:
        if type(since) != type(datetime.datetime.utcnow()):
            raise Exception('The value for the "since" parameter must be a datetime object')

        query['last_seen_on'] = {'$gt': since }

    group_exceptions = exception_groups.find(query).sort('last_seen_on', -1).skip(start).limit(maxrecs)

    return group_exceptions

def get_exception_group(exception_group_id):
    if type(exception_group_id) == type(u'') or type(exception_group_id) == type(''):
        exception_group_id = ObjectId(exception_group_id)

    exception_groups = Database.Instance().exception_groups()
    return exception_groups.find_one({'_id': exception_group_id})

def archive_exceptiong_roup(unique_hash):
    group = get_exception_group(unique_hash)

    if not group: return
    
    if group['status']: return

    applications = Database.Instance().applications()
    applications.update({'_id': group['application'] }, {'$inc': {'count': -1 } })

    group['status'] = True

    exception_groups = Database.Instance().exception_groups()
    exception_groups.save(group)

def gex_exceptions_in_group(exception_group_id, start=0, maxrecs=10):
    if type(exception_group_id) == type(u'') or type(exception_group_id) == type(''):
        exception_group_id = ObjectId(exception_group_id)

    exceptions = Database.Instance().exceptions()
    return exceptions.find({'exception_group_id': exception_group_id}).skip(start).limit(maxrecs).sort('insert_date', -1)

