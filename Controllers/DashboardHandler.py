import tornado.web

import re
from Controllers.BaseHandler import BaseHandler
from Services import LoggingService

ITEMS_PER_PAGE = 20

class BaseDashboard(BaseHandler):

    def _global(self, app_name):
        self._data['applications'] = LoggingService.get_applications(self._data['user']['_id'])
        self._data['keyword'] = ''

        #Get Applications
        if app_name:

            app_name = app_name.replace('/', '')
            app = LoggingService.get_application_by_url_name(self._data['user']['_id'], app_name)
            
            if not app:
                raise tornado.web.HTTPError(404)
            
            self._data['current_application'] = str(app['_id'])

            return app
        else:
            app = LoggingService.get_first_application(self._data['user']['_id'])
            if not app:
                return None

            self._data['current_application'] = str(app['_id'])

            return app

    def _compute_paging(self, page, total_count):
        global ITEMS_PER_PAGE

        start_page = 1
        max_pages = 5
        next_page = ''
        previous_page = ''

        page_status = {'previous': 'disabled',
                  'next': 'disabled' }

        if page > 3: 
            if page * ITEMS_PER_PAGE > total_count:
                start_page = page - 4
            elif (page +1) * 10 > total_count:
                start_page = page - 3
            else:
                start_page = page - 2
                
        if page > 1:
            page_status['previous'] = ''
            previous_page = page - 1
       
        if page * ITEMS_PER_PAGE < total_count:
            page_status['next'] = ''
            next_page = page + 1
        

        for i in range(start_page, start_page + max_pages):
            if i * ITEMS_PER_PAGE <= total_count:
                page_status[i] = ''
            elif (i-1) * ITEMS_PER_PAGE <= total_count:
                page_status[i] = ''
            else:
                page_status[i] = 'disabled'
        
        if total_count == 0:
            page_status[1] = 'disabled'

        self._data['page'] = page
        self._data['start_page'] = start_page
        self._data['max_pages'] = max_pages
        self._data['page_link'] = '/dashboard?%s&page=' % re.sub('&?page=\d+', '', self.request.query)
        self._data['page_status'] = page_status
        self._data['next_page'] = next_page
        self._data['previous_page'] = previous_page

class DashboardHandler(BaseDashboard):
    @tornado.web.authenticated
    def get(self, app_name):
        
        global ITEMS_PER_PAGE

        app = self._global(app_name)

        if app: app_name = app['url_name']
        else: app_name = ''

        #Check if the Archive All flag was passed
        archive_all = self.get_argument('archive_all', None)
        if archive_all == 'True':
            LoggingService.archive_all_exception_group(app['_id'])
            self.redirect('/dashboard/%s' % app_name)

        #Check if there are any exceptions to archive, if so
        exception = self.get_arguments('exception', None)
        if exception:
            for ex in exception:
                LoggingService.archive_exception_group(ex)

        #Get Severity
        severity = None
        log_choice = self.get_argument('log_choice', None)
        if log_choice is None or log_choice == 'specific':
            severity = int(self.get_argument('severity_level', 1))

        #Get Page and Offset
        page = int(self.get_argument('page', 1))
        start = (page * ITEMS_PER_PAGE) - ITEMS_PER_PAGE

        #Get Exceptions
        keyword = self.get_argument('keyword', '')

        if not keyword and app:
            self._data['exceptions'] = LoggingService.get_exceptions_groups(self._data['user']['_id'], app['_id'], severity=severity, start=start)
            total_count = self._data['exceptions'].count()
        elif keyword:
            from Packages.mongodbsearch import mongodbsearch
            from pymongo import Connection

            self._data['exceptions'] = []

            mongo_search = mongodbsearch.mongodb_search(Connection()['onerrorlog'])
            conditions = {'key': str(self._data['user']['_id']),
                          'application': str(app['_id']),
                         }

            if severity is not None:
                conditions['severity'] = severity

            documents, _, total_count = mongo_search.search(keyword, conditions=conditions, fields=['unique_hash, _id'])

            for doc in documents:
                self._data['exceptions'].append(LoggingService.get_exception_group(doc['_id']))
        else:
            self._data['exceptions'] = []
            total_count = 0

        self._data['app_name'] = app_name
        if app:
            self._data['log_choice'] = log_choice
            self._data['severity'] = severity
            self._data['get_severity_string'] = LoggingService.get_severity_string
            self._data['keyword'] = keyword
            self._data['total_count'] = total_count

            self._compute_paging(page, total_count)
        
            
            self._data['section_title'] = 'Dashboard : %s : %s' % (self._data['user']['company_name'], app['application'])
            self._data['application_name'] = app['application']
            self._data['htmlTitle'] = 'OnErrorLog - Dashboard'
            self.write(self.render_view('../Views/dashboard.html', self._data))

        else:
            self._data['section_title'] = 'Getting Started'
            self._data['htmlTitle'] = 'OnErrorLog - Getting Started'
            self.write(self.render_view('../Views/gettingstarted.html', self._data))

        

class DetailsHandler(BaseDashboard):
    @tornado.web.authenticated
    def get(self, app_name, unique_hash):
        
        app = self._global(app_name)

        exception_group = LoggingService.get_exception_group(unique_hash)
        exceptions = LoggingService.gex_exceptions_in_group(unique_hash)

        self._data['exception_group'] = exception_group
        self._data['exceptions'] = exceptions
        self._data['app_name'] = app_name

        self._data['get_severity_string'] = LoggingService.get_severity_string
        self._data['section_title'] = '%s : %s' % (app['application'], self._data['exception_group']['message'][0:60])
        self._data['htmlTitle'] = 'OnErrorLog - Dashboard'
        self.write(self.render_view('../Views/details.html', self._data))

