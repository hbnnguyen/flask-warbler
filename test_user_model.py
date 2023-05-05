"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
from unittest import TestCase

from models import db, User, Message, Follow

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    def setUp(self):
        """set up the testing environment before each test"""
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()

        # Dont do this
        # self.u1 = u1
        # self.u2 = u2

        # going to need to query directly because of reference based errors

        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()


    def tearDown(self):
        """break down the testing environment after every test"""
        db.session.rollback()


    def test_user_model(self):
        """tests creation of user model"""
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)


    def test_successful_user_signup(self):
        """test that user can sign up"""
        u1 = User.signup("testing", "testing@email.com", "password", None)

        self.assertEqual(u1.username, "testing")
        self.assertEqual(u1.email, "testing@email.com")
        self.assertTrue(u1.password != "password")


    def test_unsuccessful_user_signup(self):
        """test uncessful signup attempt"""
        with self.assertRaises(ValueError):
            User.signup("uncessessful", "uncessessful", "", None)
            db.session.commit()

        users = User.query.filter_by(
            username="uncessessful", email="uncessessful")
        self.assertNotIn("uncessessful", users)


    def test_valid_auth(self):
        """test authenticate class method: positive outcome"""

        u1 = User.query.get(self.u1_id)

        auth_user = User.authenticate(u1.username, "password")

        self.assertEqual(u1, auth_user)


    def test_invalid_auth(self):
        """test authenticate class method: negative outcome"""

        u1 = User.query.get(self.u1_id)

        auth_user = User.authenticate(u1.username, "notpassword")

        self.assertEqual(False, auth_user)


    def test_follow(self):
        """test that users can follow eachother"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        followed_user = u2
        u1.following.append(followed_user)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))


    def test_unfollow(self):
        """test that users can follow and then unfollow eachother"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        followed_user = u2
        u1.following.append(followed_user)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))

        u1.following.remove(followed_user)
        db.session.commit()

        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u2.is_followed_by(u1))
