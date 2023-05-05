"""User model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follow

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()
        Message.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u1 = User.query.get(self.u1_id)

        # User should have 0 messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_create_message(self):
        """TODO: write me"""

        u1 = User.query.get(self.u1_id)

        self.assertEqual(len(u1.messages), 0)

        message = Message(text="wahoo!")
        u1.messages.append(message)
        db.session.commit()

        msg_in_db = Message.query.get(message.id)
        self.assertEqual(msg_in_db.text, "wahoo!")

        self.assertEqual(len(u1.messages), 1)


    def test_delete_message(self):
        """TODO: write me"""

        u1 = User.query.get(self.u1_id)

        self.assertEqual(len(u1.messages), 0)

        message = Message(text="wahoo!")
        u1.messages.append(message)
        db.session.commit()

        msg_in_db = Message.query.get(message.id)

        self.assertEqual(msg_in_db.text, "wahoo!")
        self.assertEqual(len(u1.messages), 1)

        db.session.delete(msg_in_db)
        db.session.commit()

        deleted_msg = Message.query.get(message.id)

        self.assertIsNone(deleted_msg)






# delete message
# like message
# unlike message
# liked_by relationship