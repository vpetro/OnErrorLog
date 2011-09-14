from Controllers.BaseHandler import BaseHandler
from Services import LoggingService
import json

class AddExceptionHandler(BaseHandler):
    def post(self):

        try:
            body = json.loads(self.request.body)
        except Exception, e:
            self.set_error_json(str(e), 500)

        try:
            LoggingService.insert_exception(body)
        except KeyError, e:
            if str(e) == 'Some required fields are missing':
                self.set_error_json(str(e), 400)
            elif str(e) == 'The key you specified is invalid':
                self.set_error_json(str(e), 403)
            elif str(e) == 'Severity has an invalid value':
                self.set_error_json(str(e), 400)
        except Exception, e:
            print str(e)
            self.set_error_json(str(e), 500)


class ListExceptionGroupsHandler(BaseHandler):
    def get(self):
        
        key = self.get_argument('key', None)
        application = self.get_argument('application', None)

        if not key or not application:
            self.set_error_json('Some required fields are missing', 400)

        is_key_valid = LoggingService._validate_key(key)
        if not is_key_valid:
            self.set_error_json('The key you specified is invalid', 403)

        application_id = LoggingService.get_application_id(key, application)

        maxrecs = int(self.get_argument('maxrecs', 10))
        start = int(self.get_argument('start', 0))
        severity = self.get_argument('severity', None)
        if severity is not None:
            severity = int(severity)

            try:
                LoggingService.check_severity(severity)
            except Exception, e:
                self.set_error_json(str(e), 400)


        exception_groups = LoggingService.get_exceptions_groups(key, application_id, severity=severity, start=start, maxrecs=maxrecs)
        
        groups = [] 
        for ex in exception_groups:
            d = {'status': ex['status'],
                 'id': ex['unique_hash'],
                 'insert_date': str(ex['insert_date']),
                 'last_seen_on': str(ex['last_seen_on']),
                 'application': application,
                 'message': ex['message'],
                 'file': ex['exception'],
                 'severity': ex['severity'],
                 'exception_count': ex['count'],
                 'exceptions': []
                }
            for inner in ex['exceptions']:
                d['exceptions'].append(str(inner))

            groups.append(d)

        self.render_json({'onerrorlog': {
                                        'status': self.get_status(),
                                        'count': len(groups),
                                        'groups': groups
                                       }
                        })


