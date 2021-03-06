import os
import random
import string
import json
import cherrypy
from cherrypy.lib.static import serve_file
from model.user import *

from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__), 'html')])

cherrypy.config.update({'session_filter.on': True})

class SessionData:
    def __init__(self):
        cherrypy.log('Creating new session data')
        self.user = None
    
    def SetUserId(self, user_id):
        self.ClearUserId()
        cherrypy.session['user_id'] = user_id
        
    def GetUser(self):
        if self.user:
            return self.user;
        if not cherrypy.session.get('user_id'):
            return None
        self.user = User(cherrypy.session.get('user_id'))
        return self.user
    
    def ClearUser(self):
        cherrypy.session.pop('user_id')
        self.user = None
    

session_data = {}

def GetSessionData():
    session_id = cherrypy.session.id
    cherrypy.log('Retrieving session data for session %s' % session_id)
    if not session_data.has_key(session_id):
        session_data[session_id] = SessionData()
    return session_data[session_id]

def ClearSessionData():
    session_id = cherrypy.session.id
    cherrypy.log('Clearing session data for session %s' % session_id)
    if session_data.has_key(session_id):
        del session_data[session_id]

def GetUser():
    session = GetSessionData()
    if not session:
        return None
    return session.GetUser()

class MultiUserController(object):
    
    def authenticate_access(self):
        if not GetUser():
            raise cherrypy.HTTPRedirect("/login")

    def index(self):
        self.authenticate_access()
        
        return self.render_index()
    index.exposed = True
    
    def render_index(self):
        tmpl = lookup.get_template("index.html")
        return tmpl.render()
    
    def login(self):
        if GetUser():
            raise cherrypy.HTTPRedirect("/")
        tmpl = lookup.get_template("login.html")
        return tmpl.render()
    login.exposed = True
    
    def signup(self, username, password, email):
        try:
            user = User.create(username, password, email)
            return "OK"
        except UserException, e:
            return e.message
    signup.exposed = True

    def authenticate(self, username, password):
        try:
            user = User(username)
            if user.authenticate(password):
                cherrypy.session['user_id'] = user.user_id
                return "OK"
        except UserException, e:
            pass
        return "Unknown user name or password"
    authenticate.exposed = True
    
    def logout(self):
        GetSessionData().ClearUser()
        ClearSessionData()
        raise cherrypy.HTTPRedirect("/")
    logout.exposed = True

conf = os.path.join(os.getcwd(), 'settings.conf')

if __name__ == '__main__':
    # CherryPy always starts with app.root when trying to map request URIs
    # to objects, so we need to mount a request handler root. A request
    # to '/' will be mapped to HelloWorld().index().
    cherrypy.quickstart(MultiUserController(), config=conf)
