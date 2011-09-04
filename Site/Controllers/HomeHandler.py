import tornado.web
import tornado.template

from Controllers.BaseHandler import BaseHandler

class HomeHandler(BaseHandler):
    def get(self):

        self._data['htmlTitle'] = 'OnErrorLog - Home'

        self.write(self.render_view('../Views/home.html', self._data))

