import tornado.web
import tornado.template

from Controllers.BaseHandler import BaseHandler

class HomeHandler(BaseHandler):
    def get(self):

        self._data['error'] = self.get_argument('error', None)
        self._data['errorlogin'] = self.get_argument('errorlogin', None)

        self._data['htmlTitle'] = 'OnErrorLog - Home'
        self.write(self.render_view('../Views/home.html', self._data))
        
class AboutHandler(BaseHandler):
    def get(self):
        self._data['htmlTitle'] = 'OnErrorLog - About'
        self.write(self.render_view('../Views/about.html', self._data))

class DocsHandler(BaseHandler):
    def get(self):
        self._data['htmlTitle'] = 'OnErrorLog - About'
        self.write(self.render_view('../Views/docs.html', self._data))

