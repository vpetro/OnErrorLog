import urllib2
import json
import cgi
import re

API_KEY = '06a96cdd4ad1a841d958b541a3590b4b81882d47'
CREATE_PROJECT_ACTION = '/projects/{project_id}/tickets.xml?_token=%s' % API_KEY
GET_MEMBERSHIP_ACTION = '/projects/{ID}/memberships.json?_token=%s' % API_KEY
BASE_URL = 'https://gazaro.lighthouseapp.com'

def _get_json(url):
        
    req = urllib2.urlopen(url)
    content = req.read()

    return json.loads(content)

def post(url, body):
    req = urllib2.Request(url, body, {'Content-Type': 'text/xml'})
    
    try:
        response = urllib2.urlopen(req)
        return response.read()
    except urllib2.HTTPError, e:
        print e.read()

def get_project_memberships(project_id):
    url = BASE_URL + GET_MEMBERSHIP_ACTION.replace('{ID}', str(project_id))
    result = _get_json(url)

    return result['memberships']

def create_ticket(project_id, title, body, user_id=None):

    xml = """<?xml version="1.0" encoding="UTF-8"?><ticket>
            <assigned-user-id type="integer">{user_id}</assigned-user-id>
            <attachments-count type="integer">0</attachments-count>
            <body>{body}</body>
            <body-html></body-html>
            <created-at type="datetime"></created-at>
            <creator-id type="integer"></creator-id>
            <milestone-id type="integer"></milestone-id>
            <number type="integer"></number>
            <permalink></permalink>
            <project-id type="integer">{project_id}</project-id>
            <state>new</state>
            <title>{title}</title>
            <updated-at type="datetime"></updated-at>
            <user-id type="integer"></user-id>
            </ticket>"""
        
    xml = xml.replace('{body}', cgi.escape(body))
    xml = xml.replace('{title}', cgi.escape(title))
    xml = xml.replace('{project_id}', str(project_id))
    
    if user_id:
        xml = xml.replace('{user_id}', str(user_id))

    xml = xml.encode('ascii', 'ignore')
    
    url = BASE_URL + CREATE_PROJECT_ACTION.replace('{project_id}', str(project_id))
    xml_result = post(url, xml)

    ticket_url = re.findall('<url>([^<]+)', xml_result)[0]

    return ticket_url
