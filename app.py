import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, CSRFProtectForm, EditProfileForm
from models import db, connect_db, User, Message, Like, DEFAULT_HEADER_IMAGE_URL, DEFAULT_IMAGE_URL

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
        g.csrf_form = CSRFProtectForm()
    else:
        g.user = None


@app.before_request
def add_csrf_form_to_g():
    g.csrf_form = CSRFProtectForm()


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log out user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    do_logout()

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.post('/logout')
def logout():
    """Handle logout of user and redirect to homepage."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = g.csrf_form

    if form.validate_on_submit():
        do_logout()
        flash('logged out!')

    return redirect("/")

    # IMPLEMENT THIS AND FIX BUG
    # DO NOT CHANGE METHOD ON ROUTE


##############################################################################
# General user routes:

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users, form=g.csrf_form)


@app.get('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/show.html', user=user, form=g.csrf_form)


@app.get('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user, form=g.csrf_form)


@app.get('/users/<int:user_id>/followers')
def show_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user, form=g.csrf_form)


@app.post('/users/follow/<int:follow_id>')
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current for the current user.
    """
    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")

    # TODO: refactor all of the if not g.user or not form.validate_on_submit():


@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current for the current user.
    """

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def edit_profile():
    """Update profile for current user and return to user detail"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = EditProfileForm(obj=g.user)

    if form.validate_on_submit():
        user = User.authenticate(
            g.user.username,
            form.password.data,
        )

        if user:
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.header_image_url.data or DEFAULT_HEADER_IMAGE_URL
            g.user.header_image_url = header_image_url
            g.user.bio = form.bio.data
            g.user.location = form.location.data

            db.session.commit()
            return redirect(f'/users/{g.user.id}')

        else:
            flash("Access unauthorized.", "danger")
            return redirect("/")

    else:
        return render_template('users/edit.html', form=form)


@app.post('/users/delete')
def delete_user():
    """Delete user.

    Redirect to signup page.
    """

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    Message.query.filter_by(user_id=g.user.id).delete()

    db.session.delete(g.user)
    db.session.commit()

    do_logout()

    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()
# TODO: how to refactor this?
    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html', form=form)


@app.get('/messages/<int:message_id>')
def show_message(message_id):
    """Show a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)

    liked_by_curr_user = [l.message_id for l in g.user.likes]

    return render_template('messages/show.html',
                            user = g.user,
                            message=msg,
                            liked = liked_by_curr_user,
                            form=g.csrf_form)


@app.post('/messages/<int:message_id>/delete')
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)

    if g.user.id != message.user_id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(message)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


@app.post('/messages/<int:message_id>/like')
def like_message(message_id):

    """
    likes a message, adds like to database, redirects to homepage
    """

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)

    like = Like(user_id=g.user.id, message_id=message.id)

    db.session.add(like)
    db.session.commit()

    #account for changing icon -> on home page
    return redirect("/")


@app.post('/messages/<int:message_id>/unlike')
def unlike_message(message_id):

    """
    unlikes a message, deletes like from database, redirects to homepage
    """

    form = g.csrf_form

    if not g.user or not form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    like = db.session.query(Like).filter(Like.user_id == g.user.id,
                                        Like.message_id == message_id).first()

    db.session.delete(like)
    db.session.commit()

    #account for changing icon -> on home page
    return redirect("/")

@app.get("/users/<int:user_id>/likes")
def display_liked_messages(user_id):

    form = g.csrf_form

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    likes = user.likes

    liked_messages = []

    for like in likes:
        liked_messages.append(Message.query.get(like.message_id))

    return render_template('users/likes.html', messages=liked_messages, user=user, form=form)

##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of self & followed_users
    """

    if g.user:
        # following lines create list of all ID for which to render messages
        following_ids = [f.id for f in g.user.following]
        following_ids.append(g.user.id)

        messages = (Message
                    .query
                    .filter(Message.user_id.in_(following_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        print(f"following_ids: {following_ids}")
        print(f"messages: {messages}")

        liked_by_curr_user = [l.message_id for l in g.user.likes]

        return render_template('home.html',
                                messages=messages,
                                liked=liked_by_curr_user,
                                user=g.user,
                                form=g.csrf_form)

    else:
        return render_template('home-anon.html')


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
