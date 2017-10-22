# Written By Adam Sunderman 
# CS-496 - Simple OAuth -
# This is a simple application to grab some basic info from an end users
# Google+ account. The app relies on two html template files (mainpage.html, 
# login.html) a css folder/file (stylesheet/styles.css) and an app.yaml file
# to specify static paths and handlers. Sessions are used to track users, IF 
# END USERS HAVE COOKIES BLOCKED ON THEIR BROWSERS THE APP WILL NOT FUNCTION. 
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
import webapp2
import os
import json
import logging
import random
import string
import urllib
import httplib
from webapp2_extras import sessions

config = {
	'client_id' : '804900809500-77ihju1joj8ueaf3nt59rms83gf447se.apps.googleusercontent.com',
	'client_redirect' : 'https://simpleoauth.appspot.com/oauth',
	'client_secret':'QjqoGNQPeBK8ryZr_QS8rPkH'
}
config['webapp2_extras.sessions'] = {
	'secret_key' : 'ldy34n7yh234jd7043t54tfjklasdn44'
}
# Class BaseHandler dispatchs new sessions 
# Taken from WebApp2 Documentation 
# http://webapp2.readthedocs.io/en/latest/api/webapp2_extras/sessions.html
class BaseHandler(webapp2.RequestHandler):
	def dispatch(self):
		self.session_store = sessions.get_store(request=self.request)
		try:
			webapp2.RequestHandler.dispatch(self)
		finally:
			self.session_store.save_sessions(self.response)
	@webapp2.cached_property
	def session(self):
		return self.session_store.get_session()

class MainPage(BaseHandler):
	def get(self):
		# Send homepage HTML template values
		template_vals = {
			'mt':'Welcome please click the button below to login with Google.',
			'ex':'The button above will take you to Google to sign in. This will allow me to access some of your very basic info from Google+ which you will see on the next page. This site is an assignment for Oregon State University and can access some of your basic personal information. If you do not want to reveal any info such as your name, email and Google+ account link then please close this page now.',
			'msg':'Go To Google'
		}
		mPath = os.path.join(os.path.dirname(__file__), 'mainpage.html')
		self.response.write(template.render(mPath, template_vals))
	def post(self):
		# Create a new state value, store it in the current session and redirect to Google oauth
		state_secret = ''
		for x in range(0,20):
			state_secret += random.choice(string.letters)
		self.session['state'] = state_secret
		self.redirect('https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=' + str(self.app.config.get('client_id')) + '&redirect_uri=' + str(self.app.config.get('client_redirect')) + '&scope=email&access_type=offline&state=' + str(state_secret))

class Oauth(BaseHandler):
	def get(self):
		# Get the state and code from the redirect request
		c = self.request.get('code')
		s = self.request.get('state')
		# Get the state from the session
		cs = self.session.get('state')
		# If the current session exists and the current session state matches the returned state continue
		if cs:
			if cs == s:
				# Build the request data for token
				data = {
					'client_id' : str(self.app.config.get('client_id')),
					'client_secret' : str(self.app.config.get('client_secret')),
					'redirect_uri' : str(self.app.config.get('client_redirect')),
					'grant_type' : 'authorization_code',
					'code' : str(c)
				}
				# Build the headers and encode the request
				post_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
				enc = urllib.urlencode(data)
				# Fetch the token
				res = urlfetch.fetch('https://www.googleapis.com/oauth2/v4/token', enc, urlfetch.POST, post_headers)
				# Get the token and build the request for Google+ API
				json_res = json.loads(res.content)
				get_headers = {'Authorization': str(json_res['token_type']) + ' ' + str(json_res['access_token'])}
				# Fetch the profile data and build the final page template from retrieved values
				res2 = urlfetch.fetch('https://www.googleapis.com/plus/v1/people/me', headers=get_headers)
				json_res2 = json.loads(res2.content)
				# Try pulling out an email. Will need this later if the person is signed into Google but NOT a Google+ user
				e = json_res2['emails']
				em = e[0]
				# Check to make sure the user has a Google+ account
				if json_res2['isPlusUser']:
					n = json_res2['name']
					template_vals = {
						'at':'Here is your first and last name and your Google+ profile link as stored in Google+ servers. The verification code below was created by this app for verification during the OAuth process. This was just a test of using OAuth to secure some personal information.', 
						'ex2':'This site is an assignment for Oregon State University and will access some of your personal information. If you do not want to reveal any info such as your name, email and Google+ account link then please close this page now.',
						'usr_fname': n['givenName'], 
						'usr_lname': n['familyName'],
						'usr_link' : json_res2['url'],
						'secret': s
					}
					path = os.path.join(os.path.dirname(__file__), 'login.html')
					self.response.write(template.render(path, template_vals))
				# If the user is signed into Google but NOT a Google+ user. 
				elif json_res2['objectType'] == 'person' and em['value'] != '':
					template_vals = {
						'at':'You are not a Google+ user. The info below is from the Google account that you are logged into. The verification code below was created by this app for verification during the OAuth process. This was just a test of using OAuth to secure some personal information.', 
						'ex2':'This site is an assignment for Oregon State University and will access some of your personal information. If you do not want to reveal any info such as your name, email and Google+ account link then please close this page now.',
						'usr_fname': 'None', 
						'usr_lname': 'None',
						'usr_link' : em['value'],
						'secret': s
					}
					path = os.path.join(os.path.dirname(__file__), 'login.html')
					self.response.write(template.render(path, template_vals))
				# If there is no user info
				else:
					template_vals = {
						'at':'Sorry there was an error. The app could not identify you. This was just a test of using OAuth to secure some personal information.', 
						'ex2':'This site is an assignment for Oregon State University and will access some of your personal information. If you do not want to reveal any info such as your name, email and Google+ account link then please close this page now.',
						'usr_fname': 'None', 
						'usr_lname': 'None',
						'usr_link' : 'None',
						'secret': s
					}
					path = os.path.join(os.path.dirname(__file__), 'login.html')
					self.response.write(template.render(path, template_vals))
			# If the current session state does not match the returned state 
			else:
				template_vals = {
					'at':'There was an error in your request. The state value has been modified. The request cannot be completed.', 
					'ex2':'This site is an assignment for Oregon State University and will access some of your personal information. If you do not want to reveal any info such as your name, email and Google+ account link then please close this page now.',
					'usr_fname': 'None', 
					'usr_lname': 'None',
					'usr_link' : 'None',
					'secret': s + ' ' + cs
				}
				path = os.path.join(os.path.dirname(__file__), 'login.html')
				self.response.write(template.render(path, template_vals))
		# If the current session cannot be found (Probably due to blocked cookies)
		else:
			template_vals = {
				'at':'There was an error in your request. Cookies must be turned on. The request cannot be completed.', 
				'ex2':'This site is an assignment for Oregon State University and will access some of your personal information. If you do not want to reveal any info such as your name, email and Google+ account link then please close this page now.',
				'usr_fname': 'None', 
				'usr_lname': 'None',
				'usr_link' : 'None',
				'secret': s + ' ' + cs
			}
			path = os.path.join(os.path.dirname(__file__), 'login.html')
			self.response.write(template.render(path, template_vals))

app = webapp2.WSGIApplication([
	('/', MainPage),
	('/oauth', Oauth)
], debug=True, config=config)