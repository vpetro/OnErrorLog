import tornado.web
import tornado.template

from Controllers.BaseHandler import BaseHandler

class HomeHandler(BaseHandler):
    def get(self):

        self._data['error'] = self.get_argument('error', None)
        self._data['errorlogin'] = self.get_argument('errorlogin', None)

        self._data['htmlTitle'] = 'OnErrorLog - Home'
        self.write(self.render_view('../Views/home.html', self._data))
        
        
