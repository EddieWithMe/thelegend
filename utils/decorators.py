
from __future__ import division
import calendar
import os
import hmac
import time
import logging
import urllib
from hashlib import sha512
from global_variables import LENGTH_OF_UUID4
from secrets import secret_string


#http://stackoverflow.com/questions/25363433/why-does-webapp2-auth-get-user-by-session-change-the-token token auto created for session?
def csrf_decorator(handler):
	def check_csrf(self, *args, **kwargs):
		token = self.request.get("csrf")
		if not token:
			return self.display_session_error()
		logging.info("delivered csrf param" + token)
		if len(token) == LENGTH_OF_UUID4:
			logging.info("len(token) != LENGTH_OF_UUID4:")
			if not self.session.get(token):
				return self.display_session_error()
		else:
			logging.info("len(token) == LENGTH_OF_UUID4:")
			if not validate_token(token, secret_string):#adding a session variable check in here possibly?
				return self.display_session_error()
		return handler(self, *args, **kwargs)
	return check_csrf

def test_decorator(handler):
	def check_csrf2(self, *args, **kwargs):
		token = self.request.get("csrf")
		if not token:
			return self.display_session_error()