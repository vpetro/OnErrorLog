import tornadotoad
import tornado.web
import tornado.template
import json
import os

class BaseHandler(tornado.web.RequestHandler):

    def initialize(self):

        self._data = {}
        
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
