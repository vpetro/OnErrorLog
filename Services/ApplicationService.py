from Services import Database
from Services import ServicesTools

def insert_application(key, application):
    applications = Database.Instance().applications()

    d = {'key': key, 
         'application': application,
         'url_name': ServicesTools.normalize_text_for_url(application) 
        }

    app = applications.find_one(d)

    if not app:
        d['count'] = 1
        return applications.save(d)

    return app['_id']

def save_application(app):
    applications = Database.Instance().applications()

    applications.save(app)

def get_application_by_id(key, application_id):
    applications = Database.Instance().applications()

    application_id = ServicesTools.convert_to_object_id(application_id)

    d = {'key': key, '_id': application_id }
    app = applications.find_one(d)

    if not app:
        return None

    return app

def get_application_by_url_name(key, url_name):
    applications = Database.Instance().applications()

    d = {'key': key, 'url_name': url_name }
    app = applications.find_one(d)

    if not app:
        return None

    return app

def get_applications(key):
    applications = Database.Instance().applications()

    return applications.find({'key': key })

def get_first_application(key):
    applications = Database.Instance().applications()

    return applications.find_one({'key': key })

