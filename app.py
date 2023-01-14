from flask import Flask, render_template, redirect, session, flash, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.app_context().push()

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///flask_feed"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY ECHO"] = True
app.config["SECRET_KEY"] = "secret1234"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
toolbar = DebugToolbarExtension(app)


connect_db(app)
db.create_all()


@app.route('/')
def home_page():
    return redirect('/register')


@app.route('/register', methods=["GET", "POST"])
def add_new_user():
    """shows registration form and handles new user"""

    form = UserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(
            username, password, email, first_name, last_name)

        session['username'] = username

        try:
            db.session.commit()
        except IntegrityError:
            flash("Username or email is taken. Please select another")
            return render_template('register.html', form=form)

        return redirect(f'/users/{username}')

    return render_template('register.html', form=form)


@app.route('/users/<username>', methods=['GET'])
def show_user_info(username):
    """checks if username is in the session and then allows the user to see the user details page"""

    if "username" in session and session['username'] == username:
        user = User.query.filter_by(username=username).first()
        feedback = Feedback.query.filter_by(username=username).all()

        return render_template("details.html", user=user, feedback=feedback)
    else:
        flash("You don't have permission to do that!")
        return redirect('/')


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """deletes a user"""
    if "username" in session and session['username'] == username:
        user = User.query.filter_by(username=username).first()

        db.session.delete(user)
        db.session.commit()
        session.pop('username')
        return redirect('/')

    else:
        flash("You don't have permission to do that!")
        return redirect('/')


@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def show_feedback_form(username):
    """shows and handles user feedback form"""
    form = FeedbackForm()
    if "username" in session and session['username'] == username:
        user = User.query.filter_by(username=username).first()

        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data

            new_feedback = Feedback(
                username=username, title=title, content=content)

            db.session.add(new_feedback)
            db.session.commit()

            return redirect(f'/users/{username}')

        return render_template("feedback.html", form=form)
    else:

        return redirect('/')


@app.route('/feedback/<feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    """deletes feedback on a particular user"""
    feedback = Feedback.query.get_or_404(feedback_id)

    if "username" in session and session['username'] == feedback.username:

        db.session.delete(feedback)
        db.session.commit()

        return redirect(f'/users/{feedback.username}')

    else:
        return redirect('/')


@app.route('/feedback/<feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    """shows feedback form and allows a user to edit"""
    feedback = Feedback.query.get_or_404(feedback_id)
    form = FeedbackForm()
    if "username" in session and session['username'] == feedback.username:

        if form.validate_on_submit():
            feedback.title = form.title.data
            feedback.content = form.content.data

            db.session.commit()

            return redirect(f'/users/{feedback.username}')

        return render_template("feedback.html", form=form, feedback=feedback)
    else:
        return redirect('/')


@app.route('/login', methods=["GET", "POST"])
def show_user_login():

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(
            username, password)

        if user:
            flash("Welcome back")
            session['username'] = username
            return redirect(f'/users/{username}')
        else:
            flash("Incorrect username/password")

    return render_template('login.html', form=form)


@app.route('/logout', methods=["GET"])
def show_user_logout():
    session.pop('username')
    flash("Goodbye")
    return redirect('/')
