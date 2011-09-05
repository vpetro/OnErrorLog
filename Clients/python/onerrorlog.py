import traceback
import json

USER_AGENT = 'Python OnErrorLog Client v0.1'

SEVERITY_CRITICAL = 0
SEVERITY_ERROR = 1
SEVERITY_INFO = 2
SEVERITY_DEBUG = 3

ACTION_ADD_EXCEPTION = '/v1/exception/add'

class OnErrorLog():
    
    def __init__(self, url, key, application):
        if url[-1] == '/': url = url[0:-1]
        
        self._url = url
        self._key = key
        self._application = application

    def send_log(self, message, severity, filename=None, url=None,status_code=None, headers=None, parameters=None):

        d = {'application': self._application,
             'key': self._key,
             'message': message,
             'severity': severity,
             }

        if headers:
            d['headers'] = headers
        
        if url:
            d['url'] = url

        if status_code:
            d['status_code'] = status_code

        if parameters:
            formatted_arguments = {}
            for key in parameters:
                formatted_arguments[key] = ','.join(parameters[key])

            d['params'] = formatted_arguments

        stacktrace = traceback.extract_stack()
        d['stacktrace'] = [{'filename': fname,
                            'line_number': line_number, 
                            'function_name': function_name,
                            'method': method
                            } 
                            for fname, line_number, function_name, method in stacktrace]

        if filename:
            d['filename'] = filename
        else:
            d['filename'] = self.__class__.__name__


        import urllib2
        headers = {'User-Agent': USER_AGENT }
        req = urllib2.Request('%s%s' % (self._url, ACTION_ADD_EXCEPTION), json.dumps(d), headers)
        
        response = urllib2.urlopen(req)
        return response.read()
