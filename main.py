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


class MainPage(webapp2.RequestHandler):
	def get(self):
		template_vals = {'mt':'Welcome please click the button below to login with Google.',
						'ex':'This will take you to Google to sign in and allow me to access some of your very basic info which you will see on the next page. This site is an assignment for Oregon State University and can access some of your basic personal information. If you do not want to reveal any info such as your name, email and Google+ account link then please close this page now.',
						 'msg':'Go'}
		path = os.path.join(os.path.dirname(__file__), 'mainpage.html')
		self.response.write(template.render(path, template_vals))
	def post(self):
		state_secret = ''
		for x in range(0,20):
			state_secret += random.choice(string.letters)	
		self.redirect(str('https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=804900809500-77ihju1joj8ueaf3nt59rms83gf447se.apps.googleusercontent.com&redirect_uri=https://simpleoauth.appspot.com/oauth&scope=email&access_type=offline&state='+str(state_secret)))

class Oauth(webapp2.RequestHandler):
	def get(self):
		c=self.request.get("code")
		s=self.request.get("state")
		data = {'client_id':'804900809500-77ihju1joj8ueaf3nt59rms83gf447se.apps.googleusercontent.com',
				'client_secret':'QjqoGNQPeBK8ryZr_QS8rPkH',
				'redirect_uri':'https://simpleoauth.appspot.com/oauth',
				'grant_type':'authorization_code'}
		data['code']=str(c)
		post_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
		enc = urllib.urlencode(data)
		res = urlfetch.fetch('https://www.googleapis.com/oauth2/v4/token', enc, urlfetch.POST, post_headers)
		json_res = json.loads(res.content)
		get_headers = {'Authorization': str(str(json_res['token_type']) + ' ' + str(json_res['access_token']))}
		res2 = urlfetch.fetch('https://www.googleapis.com/plus/v1/people/me', headers=get_headers)
		json_res2 = json.loads(res2.content)
		n = json_res2['name']
		template_vals = {'at':'Here is your special verification code from me and your profile link to Google+. This was just a test of using OAuth to secure some of your info', 
						'ex2':'This site is an assignment for Oregon State University and will access some of your personal information. If you do not want to reveal any info such as your name, email and Google+ account link then please close this page now.',
						'usr_fname': n['givenName'], 
						'usr_lname': n['familyName'],
						'usr_link' : json_res2['url'],
						'secret': s}
		path = os.path.join(os.path.dirname(__file__), 'login.html')
		self.response.write(template.render(path, template_vals))		

app = webapp2.WSGIApplication([
	('/', MainPage),
	('/oauth', Oauth)
], debug=True)
