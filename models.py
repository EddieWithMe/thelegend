
#!/usr/bin/env python
import time
import webapp2_extras.appengine.auth.models
import webapp2_extras.appengine.sessions_ndb

from google.appengine.ext import ndb
from google.appengine.api import memcache
from webapp2_extras import sessions, security
import logging


class Session(webapp2_extras.appengine.sessions_ndb.Session):
    user_id = ndb.IntegerProperty()

    @classmethod
    def get_by_sid(cls, sid):
        """Returns a ``Session`` instance by session id.
        :param sid:
            A session id.
        :returns:
            An existing ``Session`` entity.
        """
        data = memcache.get(sid)
        if not data:
            session = ndb.model.Key(cls, sid).get()
            if session:
                data = session.data
                memcache.set(sid, data)
        return data

    @classmethod
    def delete_by_user_id(cls, self, user_id):
        """Returns a ``Session`` instance by session id.
        :param sid:
            A session id.
        :returns:
            An existing ``Session`` entity.
        """
        usersessions = Session.query(Session.user_id == int(user_id)).fetch()
        logging.info(usersessions)
        for session in usersessions:
            sid = session._key.id()
            logging.info(sid)
            data = Session.get_by_sid(sid)
            logging.info(data)
            sessiondict = sessions.SessionDict(self, data=data)
            sessiondict['_user'] = None
            sessiondict['user_id'] = None
            sessiondict['token'] = None
            memcache.set(sid, '')
            ndb.model.Key(Session, sid).delete()
        usersessions = Session.query(Session.user_id == int(user_id)).fetch()
        logging.info(usersessions)
        return usersessions


class DataStoreSessionFactorExtended(webapp2_extras.appengine.sessions_ndb.DatastoreSessionFactory):
    """A session factory that stores data serialized in datastore.
    To use datastore sessions, pass this class as the `factory` keyword to
    :meth:`webapp2_extras.sessions.SessionStore.get_session`::
    from webapp2_extras import sessions_ndb

    # [...]

    session = self.session_store.get_session(
        name='db_session', factory=sessions_ndb.DatastoreSessionFactory)

    See in :meth:`webapp2_extras.sessions.SessionStore` an example of how to
    make sessions available in a :class:`webapp2.RequestHandler`.
    """

    #: The session model class.
    session_model = Session

    def _get_by_sid(self, sid):
        """Returns a session given a session id."""
        if self._is_valid_sid(sid):
            data = self.session_model.get_by_sid(sid)
            if data is not None:
                self.sid = sid
                logging.info(sid)
                logging.info(sessions.SessionDict(self, data=data))
                return sessions.SessionDict(self, data=data)
        logging.info('new')
        self.sid = self._get_new_sid()
        return sessions.SessionDict(self, new=True)

    def save_session(self, response):
        if self.session is None or not self.session.modified:
            return
        # logging.info(self.session['user_id'])
        logging.info(self.session)
        logging.info(self.sid)
        if self.session:
            try:
                try:
                    logging.info(self.session['user_pre_2FA'])
                    userid = self.session['user_pre_2FA']['user_id']
                except:
                    userid = self.session['_user'][0]
                logging.info('new session with user_id: ' + str(self.sid))
                self.session_model(id=self.sid, data=dict(self.session), user_id=userid)._put()
            except:
                logging.info('new session no user_id: ' + str(self.sid))
                self.session_model(id=self.sid, data=dict(self.session))._put()
        else:
            logging.info('new session no user_id: ' + str(self.sid))
            self.session_model(id=self.sid, data=dict(self.session))._put()
        self.session_store.save_secure_cookie(response, self.name, {'_sid': self.sid}, **self.session_args)


class User(webapp2_extras.appengine.auth.models.User):
    email = ndb.StringProperty()
    lastEmailSent = ndb.DateTimeProperty()
    user_name = ndb.StringProperty()
    stripeDictString = ndb.StringProperty()
    chargeIDList = ndb.StringProperty(repeated=True)
    balanceInCents = ndb.IntegerProperty(default=0)

    def set_password(self, raw_password):
        """Sets the password for the current user

        :param raw_password:
        The raw password which will be hashed and stored
        """
        self.password = security.generate_password_hash(raw_password, length=12)

    @classmethod
    def get_by_auth_token(cls, user_id, token, subject='auth'):
        """Returns a user object based on a user ID and token.

        :param user_id:
        The user_id of the requesting user.
        :param token:
        The token string to be verified.
        :returns:
        A tuple ``(User, timestamp)``, with a user object and
        the token timestamp, or ``(None, None)`` if both were not found.
        """
        token_key = cls.token_model.get_key(user_id, subject, token)
        user_key = ndb.Key(cls, user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp
        return None, None


# class Order(ndb.Model):