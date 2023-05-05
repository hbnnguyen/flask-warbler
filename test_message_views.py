"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User, Like

from flask import jsonify

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

        self.m1_id = m1.id

        self.client = app.test_client()


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        """TODO: write me"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            Message.query.filter_by(text="Hello").one()


    def test_delete_message(self):
        """TODO: write me"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f'/messages/{self.m1_id}/delete')

            self.assertEqual(resp.status_code, 302)


    def test_show_message(self):
        """TODO: write me"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f'/messages/{self.m1_id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST FOR SHOW MESSAGE ROUTE", html)


    def test_like_message(self):
        """TODO: write me"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.post(f'/messages/{self.m1_id}/like')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 302)

            likes = set(Like.query.all())

            self.assertEqual(len(likes), 1)


    def test_like_message(self):
        """TODO: write me"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            like_resp = c.post(f'/messages/{self.m1_id}/like')
            html = like_resp.get_data(as_text=True)

            self.assertEqual(like_resp.status_code, 302)

            likes = Like.query.all()
            self.assertEqual(len(likes), 1)

            unlike_resp = c.post(f'/messages/{self.m1_id}/unlike')

            empty_likes = Like.query.all()
            self.assertEqual(len(empty_likes), 0)




#POST routes

#  add message form


#GET routes
# TODO: view a single message when clicked on
# TODO: users own messages should not have like button
# display all liked messages

# TODO: do tests for when user is NOT logged in/authorized


