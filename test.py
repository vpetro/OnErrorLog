import traceback
import sys
import pprint

#API_Key
#Application
#Mode
#Exception
#StackTrace
#Message
#Host
#CGI_Variables
#Headers
#File
#Date
#Similar Errors

pp = pprint.PrettyPrinter(indent=4)

def _create_document(e, url=None, headers=None, variables=None):
    _,_,trace = sys.exc_info()

    pp.pprint(dir(req))

    print e.args

    d = {
            'key': None,
            'application': 'TestApp',
            'mode': 'Debug',
            'exception': e.__class__.__name__,
            'stacktrace': [{'filename': filename,
                            'line_number': line_number, 
                            'function_name': function_name 
                           } 
                           for filename, line_number, function_name, _ in traceback.extract_tb(trace)],
            'message': str(e),
         }


    pp.pprint(d)

if __name__ == '__main__':

    import urllib2
    headers = { 'User-Agent' : 'Mozilla/5.0', 'aadf': 'bbbb' }
    req = urllib2.Request('www.example.com', None, headers)
    
    try:
        
        html = urllib2.urlopen(req).read()
    except Exception, e:
        _create_document(e, req)
