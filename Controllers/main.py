import os, sys
import tornado.web
import tornado.httpserver
import tornado.ioloop

from Services import Logging
from Controllers.HomeHandler import HomeHandler, AboutHandler, DocsHandler
from Controllers.DashboardHandler import DashboardHandler, DetailsHandler
from Controllers.UserHandler import NewUserHandler, LogoutHandler, LoginHandler
from Controllers.ExceptionHandler import AddExceptionHandler, ListExceptionGroupsHandler

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Views', 'static'))
Logging.Init('onerroglog-web', echo=True)

if __name__ == '__main__':

    try:
        port = int(sys.argv[1])
    except (IndexError, ValueError):
        Logging.Info('usage: %s <port>' % (sys.argv[0]))
        raise SystemExit(0)

    routes = [
        #Static
        (r'/(js/.*)', tornado.web.StaticFileHandler, {'path': root}),
        (r'/(images/.*)', tornado.web.StaticFileHandler, {'path': root}),
        (r'/(css/.*)', tornado.web.StaticFileHandler, {'path': root}),
        (r'/(favicon.ico)', tornado.web.StaticFileHandler, {'path': '%s/images/' % root}),

        (r'/', HomeHandler),

        #User Account Routes
        (r'/newuser', NewUserHandler),
        (r'/logout', LogoutHandler),
        (r'/login', LoginHandler),
        
        #General Functionality
        (r'/dashboard', DashboardHandler),
        (r'/details', DetailsHandler),
        (r'/about', AboutHandler),
        (r'/docs', DocsHandler),

        #API Routes
        (r'/v1/exception/add', AddExceptionHandler),
        (r'/v1/groups/list', ListExceptionGroupsHandler),
     ]

    settings = {
        'debug': True,
        'login_url': '/',
        'cookie_secret': 'f904c1faa4367df7ed575751b0f1b5020a818635',
        'autoescape': None,
        'template_path' : root + '/..'
    }

    #    "ui_modules": uimodules,
    #    "ui_methods": {'format' : BaseHandler._format},
    app = tornado.web.Application(routes, **settings)
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

