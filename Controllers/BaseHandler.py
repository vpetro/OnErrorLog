import tornadotoad
import tornado.web
import tornado.template
import json
import os

class BaseHandler(tornado.web.RequestHandler):

    def initialize(self):

        self._data = {
                        'user': None,
                        'pretty_date': self._pretty_date
                     }
        
        user = self.get_current_user()
        if user:
            self._data['user'] = user


    def get_current_user(self):
        if hasattr(self, 'User'):
            return self.User

        u = self.get_secure_cookie('_ur')
        if not u:
            self.User = None
        else:
            self.User = json.loads(u)
        return self.User

    def delete_current_user(self):
        self.clear_cookie('_ur')

    #@property
    #def Customer(self):
    #    return int(self.User['CustomerStoreId'])

    @property
    def Username(self):
        return self.User['Username']

    def render_view(self, name, kwargs):
        args = getattr(self, '_data', {}).copy()
        args.update(kwargs)

        return self.render_string(name, **args)

    def render_json(self, j):
        self.set_header('Content-Type', 'application/json') 
        self.write(json.dumps(j))

    def set_error_json(self, error_message, status_code):
        self.set_status(status_code)

        d = {'onerrorlog':
                {'status': status_code,
                 'message': error_message
                }
            }

        self.render_json(d)
        raise tornado.web.HTTPError(status_code)

    def _pretty_date(self, time=False):
        """
        Get a datetime object or a int() Epoch timestamp and return a
        pretty string like 'an hour ago', 'Yesterday', '3 months ago',
        'just now', etc
        """
        from datetime import datetime
        now = datetime.utcnow()
        if type(time) is int:
            diff = now - datetime.utcfromtimestamp(time)
        elif isinstance(time,datetime):
            diff = now - time 
        elif not time:
            diff = now - now
        second_diff = diff.seconds
        day_diff = diff.days
            
        if day_diff < 0:
            return 'a few moments ago'

        if day_diff == 0:
            if second_diff < 10:
                return "a few moments ago"
            if second_diff < 60:
                return str(second_diff) + " seconds ago"
            if second_diff < 120:
                return  "a minute ago"
            if second_diff < 3600:
                return str( second_diff / 60 ) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            if second_diff < 86400:
                return str( second_diff / 3600 ) + " hours ago"
        if day_diff == 1:
            return "Yesterday"
        if day_diff < 7:
            return str(day_diff) + " days ago"
        if day_diff < 31:
            return str(day_diff/7) + " weeks ago"
        if day_diff < 365:
            return str(day_diff/30) + " months ago"
        return str(day_diff/365) + " years ago"

