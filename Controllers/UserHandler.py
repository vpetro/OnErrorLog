import json

from Controllers.BaseHandler import BaseHandler

from Services import UserService

class NewUserHandler(BaseHandler):
    def post(self):

        username = self.get_argument('username', None)
        password = self.get_argument('password', None)
        email_address = self.get_argument('email', None)
        company_name= self.get_argument('company_name', None)

        if not username or not password or not email_address or not company_name:
            self.redirect('/?error=required')

        account = UserService.create_user(username, password, email_address, company_name)

        if not account:
            self.redirect('/?error=exists')

        self.set_secure_cookie("_ur", json.dumps(account))

        self.redirect('/dashboard')

class LogoutHandler(BaseHandler):
    def get(self):
        self.delete_current_user()
        self.redirect("/")

class LoginHandler(BaseHandler):
    def post(self):
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)

        if not username or not password:
            self.redirect('/?errorlogin=required')

        account = UserService.verify_user(username, password)

        if not account:
                self.redirect('/?errorlogin=nologin')

        self.set_secure_cookie("_ur", json.dumps(account))
        
        self.redirect('/dashboard')
