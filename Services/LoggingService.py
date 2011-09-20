from Packages.mongodbsearch import mongodbsearch
from Services import Database
import datetime
from datetime import timedelta
from Services import ServicesTools
from Services import ApplicationService

SEVERITY_CRITICAL = 0
SEVERITY_ERROR = 1
SEVERITY_INFO = 2
SEVERITY_DEBUG = 3

def _validate_key(key):

    key = ServicesTools.convert_to_object_id(key)
    accounts = Database.Instance().accounts()
    account = accounts.find_one({'_id': key })

    if not account: return False

    return True


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

    d['application'] = ApplicationService.insert_application(d['key'], d['application'])

    if 'stacktrace' not in d:
        d['stacktrace'] = ''

    #Setup the string to be hashed
    hash_string = '%s\n%s\n%s\n%s\n%s\n%s' % (d['key'], 
                                   d['severity'],
                                   str(d['stacktrace']),
                                   d['message'],
                                   d['filename'],
                                   d['application'])
    
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


        applications.update({'_id': d['application'] }, {'$inc': {'count': 1 }})
        applications.update({'_id': d['application'] }, {'$inc': {str(d['severity']): 1 }})
    
    #Set the last seen_date
    group['last_seen_on'] = datetime.datetime.utcnow()

    #Save the exception group
    exception_group_id = exception_groups.save(group)

    increment_statistics(d)

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
            text.append(str(k))
            text.append(str(v))

    if 'params' in d:
        for k, v in d['params'].iteritems():
            text.append(str(k))
            text.append(str(v))
    
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

def increment_statistics(d):
    #Increment Statistics
    key_date = datetime.datetime.utcnow()
    key_date = datetime.datetime(key_date.year, key_date.month, key_date.day, key_date.hour)

    statistics = Database.Instance().statistics()
    
    key = '%s-%s-%s-%s' % (d['key'], d['severity'], datetime.datetime.strftime(key_date, "%Y%m%d%H"), str(d['application']))
    statistics.update({'_id': key, 'key': d['key'], 'severity': d['severity'], 'date': key_date, 'application_id': d['application']}, {'$inc': {'count': 1} }, upsert=True)

    key = '%s-%s-%s-%s' % (d['key'], d['severity'], datetime.datetime.strftime(key_date, "%Y%m%d%H"), d['filename'])
    statistics.update({'_id': key, 'key': d['key'], 'severity': d['severity'], 'date': key_date, 'filename': d['filename']}, {'$inc': {'count': 1} }, upsert=True)
    
    statistics.ensure_index([('key', 1), ('severity', 1), ('date', 1 ), ('application_id', 1), ('filename', 1)])

def get_statistics_for_application(application_id, severity=1, days_back=0):
    application_id = ServicesTools.convert_to_object_id(application_id)
    statistics = Database.Instance().statistics()

    key_date = datetime.datetime.utcnow() - timedelta(days=days_back) - timedelta(hours=24)
    key_date_start = datetime.datetime(key_date.year, key_date.month, key_date.day, key_date.hour, 0, 0)

    key_date = datetime.datetime.utcnow()
    key_date_end = datetime.datetime(key_date.year, key_date.month, key_date.day, key_date.day, 0, 0)

    results = list(statistics.find(
                                    {'application_id': application_id, 
                                    'severity': severity, 
                                    'date': {'$gt': key_date_start, '$lt': key_date_end } 
                                    }
                                  ).sort('date', -1))

    stats = []
    sd = key_date_start

    for i in range(0, 24):
        s = [r for r in results if r['date'] == sd]
        if s:
            stats.append({'date': sd, 'count': s[0]['count'] })
        else:
            stats.append({'date': sd, 'count': 0 })

        sd = sd + timedelta(hours=1)
   
    print stats
    return stats


def get_exceptions_groups(key, application, severity=None, status=False, start=0, maxrecs=20, since=None, sort='last_seen_on', sort_direction=-1):

    exception_groups = Database.Instance().exception_groups()

    application = ServicesTools.convert_to_object_id(application)

    query = {'key': key,
             'application': application,
             'status': status,
            }

    if severity is not None:
        query['severity'] = severity

    if since:
        if type(since) != type(datetime.datetime.utcnow()):
            raise Exception('The value for the "since" parameter must be a datetime object')

        query['last_seen_on'] = {'$gt': since }

    group_exceptions = exception_groups.find(query).sort(sort, sort_direction).skip(start).limit(maxrecs)

    return group_exceptions

def get_exception_group(exception_group_id):

    exception_group_id = ServicesTools.convert_to_object_id(exception_group_id)

    exception_groups = Database.Instance().exception_groups()
    return exception_groups.find_one({'_id': exception_group_id})

def archive_exception_group(unique_hash):
    group = get_exception_group(unique_hash)

    if not group: return
    
    if group['status']: return

    applications = Database.Instance().applications()
    applications.update({'_id': group['application'] }, {'$inc': {'count': -1 } })

    group['status'] = True

    exception_groups = Database.Instance().exception_groups()
    exception_groups.save(group)

def archive_all_exception_group(application_id):

    exception_groups = Database.Instance().exception_groups()
    
    application_id = ServicesTools.convert_to_object_id(application_id)


    exception_groups.update({
                            'application': application_id, 
                            'status': False 
                            }, 
                            {'$set': {'status': True}}, multi=True)

    applications = Database.Instance().applications()
    
    application = applications.find_one({'_id': application_id })
    application['count'] = 0
    application['0'] = 0
    application['1'] = 0
    application['2'] = 0
    application['3'] = 0
    applications.save(application)


def gex_exceptions_in_group(exception_group_id, start=0, maxrecs=10):

    exception_group_id = ServicesTools.convert_to_object_id(exception_group_id)

    exceptions = Database.Instance().exceptions()
    return exceptions.find({'exception_group_id': exception_group_id}).skip(start).limit(maxrecs).sort('insert_date', -1)



