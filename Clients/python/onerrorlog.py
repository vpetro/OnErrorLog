import traceback
import json
import sys

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

    def  _build_initial_record(self, message, severity):
        d = {'application': self._application,
             'key': self._key,
             'message': message,
             'severity': severity,
             }
        return d

    def _add_optional_values(self, d, headers, url, status_code):
        values = {'headers': headers, 'url': url, 'status_code': status_code}
        for key, value in values.iteritems():
            if value:
                d[key] = value

        return d

    def _add_parameters(self, d, parameters):
        if not parameters:
            return d

        formatted_arguments = {}
        for key in parameters:
            if type(parameters[key]) == type([]):
                formatted_arguments[key] = ','.join(parameters[key])
            else:
                formatted_arguments[key] = parameters[key]
        d['params'] = formatted_arguments

        return d

    def _add_stacktrace(self, d):
        stacktrace = traceback.extract_stack()
        d['stacktrace'] = [{'filename': fname,
                            'line_number': line_number, 
                            'function_name': function_name,
                            'method': method
                            } 
                            for fname, line_number, function_name, method in stacktrace]
        return d
    def _add_exception_trace(self, d):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        trace = []
        for fname, line_number, function_name, text in traceback.extract_tb(exc_traceback):
            trace.append(
                    {'filename': fname,
                     'line_number': line_number,
                     'function_name': function_name,
                     'method': text,
                     }
            )
        d['stacktrace'] = trace
        return d

    def _add_filename(self, d, filename):
        if filename:
            d['filename'] = filename
        else:
            d['filename'] = self.__class__.__name__
        return d

    def _build_message(self,
            message,
            severity,
            filename=None,
            url=None,
            status_code=None,
            headers=None,
            parameters=None,
            stacktrace=False):

        d = self._build_initial_record(message, severity)
        d = self._add_optional_values(d, headers, url, status_code)
        d = self._add_parameters(d, parameters)
        d = self._add_filename(d, filename)
        return d


    def _build_url(self):
        return "%s%s" % (self._url, ACTION_ADD_EXCEPTION)

    def send_log(self,
            message,
            severity,
            filename=None,
            url=None,
            status_code=None,
            headers=None,
            parameters=None,
            stacktrace=False):

        d = self._build_message(
                message,
                severity,
                filename,
                url,
                status_code,
                headers,
                parameters,
                stacktrace)

        import urllib2
        headers = {'User-Agent': USER_AGENT }
        req = urllib2.Request(self._build_url(), json.dumps(d), headers)

        response = urllib2.urlopen(req)
        return response.read()

    def tsend_log(self,
            message,
            severity,
            filename=None,
            url=None,
            status_code=None,
            headers=None,
            parameters=None,
            stacktrace=False):
        from tornado.httpclient import AsyncHTTPClient

        d = self._build_message(
                message,
                severity,
                filename,
                url,
                status_code,
                headers,
                parameters,
                stacktrace)

        # want to use the better client here.
        AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

        AsyncHTTPClient().fetch(
                self._build_url(),
                lambda resp: None,
                method="POST",
                body=json.dumps(d),
                headers=headers)
