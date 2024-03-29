import tornado.web

import re
import cgi
from Controllers.BaseHandler import BaseHandler
from Services import LoggingService
from Services import ApplicationService
from Services import LighthouseService
from Services import Database

ITEMS_PER_PAGE = 20

class BaseDashboard(BaseHandler):

    def _global(self, app_name):
        self._data['applications'] = ApplicationService.get_applications(self._data['user']['_id'])
        self._data['keyword'] = ''

        #Get Applications
        if app_name:

            app_name = app_name.replace('/', '')
            app = ApplicationService.get_application_by_url_name(self._data['user']['_id'], app_name)
            
            if not app:
                raise tornado.web.HTTPError(404)
            
            self._data['current_application'] = str(app['_id'])

        else:
            app = ApplicationService.get_first_application(self._data['user']['_id'])
            self._data['current_application'] = str(app['_id'])

        if app: app_name = app['url_name']
        else: app_name = ''

        self._data['app'] = app
        self._data['app_name'] = app_name

        return app, app_name

    def _compute_paging(self, page, total_count, app_name):
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
        self._data['page_link'] = '/dashboard/%s?%s&page=' % (app_name, re.sub('&?page=\d+', '', self.request.query))
        self._data['page_status'] = page_status
        self._data['next_page'] = next_page
        self._data['previous_page'] = previous_page

class DashboardHandler(BaseDashboard):
    @tornado.web.authenticated
    def get(self, app_name):
        
        global ITEMS_PER_PAGE

        app, app_name = self._global(app_name)

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

        #Sorting Variables
        sort = self.get_argument('sort', 'last_seen_on')
        sort_direction = int(self.get_argument('sort_direction', -1))

        lso_new_sort = -1
        cnt_new_sort = -1

        if sort == 'last_seen_on':
            if sort_direction == -1:
                lso_new_sort = 1
        else:
            if sort_direction == -1:
                cnt_new_sort = 1

        if not keyword and app:
            self._data['exceptions'] = LoggingService.get_exceptions_groups(
                                    self._data['user']['_id'], 
                                    app['_id'], severity=severity, 
                                    start=start, 
                                    sort=sort, 
                                    sort_direction=sort_direction)

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

            documents, _, total_count = mongo_search.search(keyword, 
                                                            conditions=conditions, 
                                                            fields=['unique_hash, _id'], 
                                                            start=start,
                                                            scoring=('last_save_date', -1))
            
            for doc in documents:
                self._data['exceptions'].append(LoggingService.get_exception_group(doc['_id']))
        else:
            self._data['exceptions'] = []
            total_count = 0

        if app:

            stats_data = {'today': [], 'previous': [] }
            
            stats = LoggingService.get_statistics_for_application(app['_id'], severity=severity)
            for i, s in enumerate(stats):
                stats_data['today'].append([i, s['count']])

            stats = LoggingService.get_statistics_for_application(app['_id'], days_back=1, severity=severity)
            for i, s in enumerate(stats):
                stats_data['previous'].append([i, s['count']])

            self._data['stats_data'] = stats_data
            self._data['log_choice'] = log_choice
            self._data['severity'] = severity
            self._data['get_severity_string'] = LoggingService.get_severity_string
            self._data['keyword'] = keyword
            self._data['total_count'] = total_count
            self._data['lso_new_sort'] = lso_new_sort
            self._data['cnt_new_sort'] = cnt_new_sort
            self._data['cgi'] = cgi

            self._compute_paging(page, total_count, app_name)
            
            self._data['section_title'] = 'Dashboard : %s : %s' % (self._data['user']['company_name'], app['application'])
            self._data['application_name'] = app['application']
            self._data['htmlTitle'] = 'OnErrorLog - Dashboard'
            self.write(self.render_view('../Views/dashboard.html', self._data))

        else:
            self._data['section_title'] = 'Getting Started'
            self._data['htmlTitle'] = 'OnErrorLog - Getting Started'
            self.write(self.render_view('../Views/gettingstarted.html', self._data))

        

class DetailsHandler(BaseDashboard):

    def _find_github_url(self, sections, gh, github_account, github_repository, sha=None, path=[]):

        try:
            
            if sha not in self.tree_dict:
                tree = gh.objects.tree(github_account, github_repository, sha)
                self.tree_dict[sha] = tree
            else:
                tree = self.tree_dict[sha]
            
            for name in sections:
                if name in tree:
                    node = tree[name]
                    if node.type == 'blob':
                        path.append(name)
                        c = gh.commits.forFile(github_account, github_repository, '/'.join(path))
                        
                        url = c[0].url
                        url = url.replace('commit', 'blob')
                        url = url + '/%s' % '/'.join(path)
                        return 'http://github.com%s' % (url)

                    elif node.type == 'tree':
                        path.append(name)
                        return self._find_github_url(sections, gh, github_account, github_repository, sha=node.sha, path=path)

        except Exception, e:
            print str(e)
            return None

        return None
    
    @tornado.web.authenticated
    def get(self, app_name, unique_hash):

        self.tree_dict = {}

        app, app_name = self._global(app_name)

        import cgi
        from github import github
        gh = None
        if 'github_account' in app and app['github_account'] and 'github_repository' in app and app['github_repository']:
            if 'github_token' in app and app['github_token'] and 'github_username' in app and app['github_username']:
                gh = github.GitHub(app['github_username'], app['github_token'])
            else:
                gh = github.GitHub()

        exception_group = LoggingService.get_exception_group(unique_hash)
        exceptions = LoggingService.gex_exceptions_in_group(unique_hash)

        if gh:
            sha = gh.commits.forBranch(app['github_account'], app['github_repository'])[0].id

            for s in exception_group['stacktrace']:
                sections = s['filename'].split('/')
                path = []
                url = self._find_github_url(sections, gh, app['github_account'], app['github_repository'], path=path, sha=sha)

                if url:
                    s['url'] = '%s#L%s' % (url, s['line_number'])

        stats_data = {'today': [], 'previous': [] }
            
        stats = LoggingService.get_statistics_for_exception_group(exception_group['_id'])
        for i, s in enumerate(stats):
            stats_data['today'].append([i, s['count']])

        stats = LoggingService.get_statistics_for_exception_group(exception_group['_id'], days_back=1)
        for i, s in enumerate(stats):
            stats_data['previous'].append([i, s['count']])

        self._data['stats_data'] = stats_data
        self._data['exception_group'] = exception_group
        self._data['exceptions'] = exceptions
        self._data['unique_hash'] = unique_hash
        self._data['get_severity_string'] = LoggingService.get_severity_string
        self._data['section_title'] = '%s : %s' % (app['application'], self._data['exception_group']['message'][0:60])
        self._data['htmlTitle'] = 'OnErrorLog - Dashboard'
        self._data['cgi'] = cgi

        self.write(self.render_view('../Views/details.html', self._data))

class ConfigureSaveHandler(BaseDashboard):

    def post(self, app_name):
        app, app_name = self._global(app_name)
        

        app['github_account'] = self.get_argument('github_account', None)
        app['github_repository'] = self.get_argument('github_repository', None)
        app['github_username'] = self.get_argument('github_username', None)
        app['github_token'] = self.get_argument('github_token', None)
        app['lighthouse_apitoken'] = self.get_argument('lighthouse_apitoken', None)
        app['lighthouse_project_id'] = self.get_argument('lighthouse_project_id', None)

        ApplicationService.save_application(app)

        self.redirect('/configure/%s' % app_name)

class ConfigureHandler(BaseDashboard):
    def get(self, app_name):
        app, app_name = self._global(app_name)
        
        self._data['section_title'] = 'Configure : %s : %s' % (self._data['user']['company_name'], app['application'])
        self._data['htmlTitle'] = 'OnErrorLog - Configuration'

        self._data['app'] = app
        self.write(self.render_view('../Views/configure.html', self._data))

class LighthouseHandler(BaseDashboard):
    def get(self, app_name, unique_hash):
        import cgi

        app, app_name = self._global(app_name)

        exception_group = LoggingService.get_exception_group(unique_hash)

        lh_memberships = LighthouseService.get_project_memberships(app['lighthouse_project_id'])

        members = []
        for member in lh_memberships:
            members.append({'name': member['membership']['user']['name'], 'id': member['membership']['user']['id'] })

        self._data['exception_group'] = exception_group
        self._data['unique_hash'] = unique_hash
        self._data['htmlTitle'] = 'OnErrorLog - Create Lighthouse Ticket'
        self._data['section_title'] = '%s : %s' % (app['application'], self._data['exception_group']['message'][0:60])
        self._data['cgi'] = cgi
        self._data['members'] = members

        self.write(self.render_view('../Views/lighthouse.html', self._data))

class LighthouseCreateHandler(BaseDashboard):
    def post(self, app_name, unique_hash):
        lighthouse_title = self.get_argument('lighthouse_title', None)
        lighthouse_member = self.get_argument('lighthouse_member', None)
        lighthouse_body = self.get_argument('lighthouse_body', None)

        app, app_name = self._global(app_name)

        ticket_url = LighthouseService.create_ticket(app['lighthouse_project_id'], lighthouse_title, lighthouse_body, user_id=lighthouse_member)
        
        exception_group = LoggingService.get_exception_group(unique_hash)
        
        exception_groups = Database.Instance().exception_groups()
        exception_group['lighthouse_url'] = ticket_url
        exception_groups.save(exception_group)

        self.redirect('/%s/details/%s' % (app_name, unique_hash))
