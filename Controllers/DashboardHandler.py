import tornado.web

import re
from Controllers.BaseHandler import BaseHandler
from Services import LoggingService

class BaseDashboard(BaseHandler):
    def _global(self):
        self._data['applications'] = LoggingService.get_applications(self._data['user']['_id'])
        self._data['keyword'] = ''

        #Get Applications
        app = self.get_argument('app', None)
        if not app:
            try:
                app = str(LoggingService.get_first_application(self._data['user']['_id'])['_id'])
            except:
                return None

        self._data['current_application'] = app

        return LoggingService.get_application_by_id(self._data['user']['_id'], app)

    def _compute_paging(self, page, total_count):
        start_page = 1
        max_pages = 5
        next_page = ''
        previous_page = ''

        page_status = {'previous': 'disabled',
                  'next': 'disabled' }

        if page > 3: 
            if page * 10 > total_count:
                start_page = page - 4
            elif (page +1) * 10 > total_count:
                start_page = page - 3
            else:
                start_page = page - 2
                
        if page > 1:
            page_status['previous'] = ''
            previous_page = page - 1
       
        if page * 10 < total_count:
            page_status['next'] = ''
            next_page = page + 1
        

        for i in range(start_page, start_page + max_pages):
            if i * 10 <= total_count:
                page_status[i] = ''
            elif (i-1) * 10 <= total_count:
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
    def get(self):

        #Check if there are any exceptions to archive, if so
        exception = self.get_arguments('exception', None)
        if exception:
            for ex in exception:
                LoggingService.archive_exceptiong_roup(ex)

        app = self._global()

        #Get Severity
        severity = None
        log_choice = self.get_argument('log_choice', None)
        if log_choice == 'specific':
            severity = int(self.get_argument('severity_level', 3))

        #Get Page and Offset
        page = int(self.get_argument('page', 1))
        start = (page * 10) - 10

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

        if app:
            self._data['log_choice'] = log_choice
            self._data['severity'] = severity
            self._data['get_severity_string'] = LoggingService.get_severity_string
            self._data['keyword'] = keyword
            self._compute_paging(page, total_count)
        
            self._data['section_title'] = 'Dashboard : %s : %s' % (self._data['user']['company_name'], app['application'])
            self._data['htmlTitle'] = 'OnErrorLog - Dashboard'
            self.write(self.render_view('../Views/dashboard.html', self._data))

        else:
            self._data['section_title'] = 'Getting Started'
            self._data['htmlTitle'] = 'OnErrorLog - Getting Started'
            self.write(self.render_view('../Views/gettingstarted.html', self._data))

        

class DetailsHandler(BaseDashboard):
    @tornado.web.authenticated
    def get(self):
        
        unique_hash = self.get_argument('id', None)

        app = self._global()

        exception_group = LoggingService.get_exception_group(unique_hash)
        exceptions = LoggingService.gex_exceptions_in_group(unique_hash)

        self._data['exception_group'] = exception_group
        self._data['exceptions'] = exceptions

        self._data['get_severity_string'] = LoggingService.get_severity_string
        self._data['section_title'] = '%s : %s' % (app['application'], self._data['exception_group']['message'][0:60])
        self._data['htmlTitle'] = 'OnErrorLog - Dashboard'
        self.write(self.render_view('../Views/details.html', self._data))

