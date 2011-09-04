from pymongo import Connection
import datetime

d = {   'application': 'TestApp',
    'exception': 'CompetitorHandler',
    'headers': {   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-us,en;q=0.5',
                   'Cache-Control': 'max-age=0',
                   'Connection': 'keep-alive',
                   'Cookie': '_ur=eyJVc2VybmFtZSI6ICJnYXphcm9iYiIsICJhdmFpbGFibGUiOiAxLCAiU3Vic2NyaWJlZFJlcG9ydHMiOiBbeyJxdWVyeSI6ICJjb21wZXRpdG9ycy1maWx0ZXJfY2F0ZWdvcnk9OCw5LDEwJmZpbHRlcl9tYW51ZmFjdHVyZXI9MTM4IiwgInRpdGxlIjogIlN0b3JlIFJlcG9ydDogQ2F0ZWdvcnkgKFNPIExBUkdFIFRWIDQ2In1dLCAiQ3VzdG9tZXJTdG9yZUlkIjogIjIwMSIsICJzaGlwcGluZyI6IDAsICJQZXJtaXNzaW9ucyI6IDAsICJFbWFpbEFkZHJlc3MiOiAiZG9taW5pY0BnYXphcm8uY29tIiwgIkZhdm9yaXRlcyI6IFt7InByb2R1Y3QiOiAiNGUwNDI5MGMxZDQxYzg3NzljMDAyODZlIiwgIm1hc3RlciI6ICI0ZTA0MjkwYTFkNDFjODc3OWMwMDI4NmQiLCAidGl0bGUiOiAiS0IgQ09WRVJTIC0gR1JFRU4gKExJTUUpIEtFWUJPQVJEIENPVkVSIn1dLCAiUGFzc3dvcmQiOiAiNjY4YzY1Mzc2NTFhYzdjM2Q3NDk4NDg2MjE1YWViYjMzNTAwZmYyMiIsICJtYXRjaGVkIjogMH0=|1314981449|c9d7ce6e9186ad1d5706f0bec03e515c00d96f6e',
                   'Host': '10.211.55.7:12001',
                   'If-None-Match': '"da39a3ee5e6b4b0d3255bfef95601890afd80709"',
                   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:6.0.1) Gecko/20100101 Firefox/6.0.1'},
    'key': None,
    'message': "invalid literal for int() with base 10: '1a'",
    'severity': 'Debug',
    'params': {   'filter_category': '1a'},
    'stacktrace': [   {   'filename': '/usr/local/lib/python2.6/dist-packages/tornado/web.py',
                          'function_name': '_execute',
                          'line_number': 927},
                      {   'filename': '/usr/local/lib/python2.6/dist-packages/tornado/web.py',
                          'function_name': 'wrapper',
                          'line_number': 1576},
                      {   'filename': '/media/psf/Projects/GazaroB2B/Controllers/ScorecardHandler.py',
                          'function_name': 'get',
                          'line_number': 132},
                      {   'filename': '/media/psf/Projects/GazaroB2B/Controllers/ScorecardHandler.py',
                          'function_name': '_generateScorecard',
                          'line_number': 76},
                      {   'filename': '/media/psf/Projects/GazaroB2B/Services/ScorecardGenerator.py',
                          'function_name': 'Generate',
                          'line_number': 65},
                      {   'filename': '/media/psf/Projects/GazaroB2B/Services/ScorecardGenerator.py',
                          'function_name': '_getFilters',
                          'line_number': 60}],
    'status_code': 500,
    'url': 'http://10.211.55.7:12001/competitors?filter_category=1a'}

SEVERITY_CRITICAL = 0
SEVERITY_ERROR = 1
SEVERITY_INFO = 2
SEVERITY_DEBUG = 3

def _validate_key(key):
    return True

def insert_exception(d):

    db = Connection()['onerrorlog']

    #Check for required keys
    required_fields = ['key', 'message', 'application', 'severity']
    if len(list(set(required_fields) & set(d))) != len(required_fields):
        raise KeyError('Some required fields are missing') 

    if d['severity'] not in [SEVERITY_CRITICAL, SEVERITY_ERROR, SEVERITY_INFO, SEVERITY_DEBUG]:
        raise KeyError('Severity has an invalid value')

    #Validate the key which was passed
    if not _validate_key(d['key']):
        raise KeyError('The key you specified is invalid')

    #Setup the string to be hashed
    hash_string = '%s/%s/%s/%s' % (d['key'], 
                                   d['severity'],
                                   str(d['stacktrace']),
                                   d['message'])

    #Has the string
    unique_hash = hash(hash_string)

    #Create and insert the exception record
    exception = d
    exception['insert_date'] = datetime.datetime.utcnow()
    exception['unique_hash'] = unique_hash

    exception_id = db['exception'].save(exception)

    #Check if the exception group exists
    group = db['_exception_group'].find_one({'unique_hash': unique_hash, 'status': False })
   
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
                  'insert_date': datetime.datetime.utcnow()
                }

    #Set the last seen_date
    group['last_seen_on'] = datetime.datetime.utcnow()

    #Save the exception group
    exception_group_id = db['_exception_group'].save(group)

    db['_exception_group'].ensure_index([('severity', 1), 
                                         ('application', 1), 
                                         ('key', 1), 
                                         ('unique_hash', 1), 
                                         ('status', 1 ), 
                                         ('last_seen_on', 0)
                                        ])

    db['_exception'].ensure_index([('severity', 1), 
                                   ('application', 1), 
                                   ('key', 1), 
                                   ('unique_hash', 1), 
                                   ('insert_date', 0)
                                  ])

    return exception_group_id, exception_id

def get_exceptions_groups(key, application, severity=SEVERITY_ERROR, status=False, start=0, maxrecs=10, since=None):

    db = Connection()['onerrorlog']

    query = {'key': key,
             'application': application,
             'severity': severity,
             'status': status,
            }

    if since:
        if type(since) != type(datetime.datetime.utcnow()):
            raise Exception('The value for the "since" parameter must be a datetime object')

        query['last_seen_on'] = {'$gt': since }

    group_exceptions = db['_exception_group'].find(query).skip(start).limit(maxrecs).sort({'last_seen_on': 0 })

    return group_exceptions

def gex_exceptions_in_group(unique_hash, start=0, maxrecs=10):
    db = Connection()['onerrorlog']

    return db['_exception'].find({'unique_hash': unique_hash}).skip(start).limit(maxrecs).sort({'insert_date': 0})

def resolve_exception_group(unique_hash):
    db = Connection()['onerrorlog']

    exception_group = db['_exception_group'].find_one({'unique_hash': unique_hash })
    exception_group['status'] = True

    db['_exception_group'].save(exception_group)

class CustomException(Exception):
       def __init__(self, value):
           self.parameter = value
       def __str__(self):
           return repr(self.parameter)


if __name__ == '__main__':
    print insert_exception(d)

