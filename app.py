from flask import Flask, render_template, redirect, session, flash, request
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.exceptions import Unauthorized
from models import connect_db, db, User, Feedback
from forms import RegistrationForm, LoginForm, FeedbackForm, DeleteForm

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///auth_db"
app.config['SECRET_KEY'] = 'spookforprez'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.debug = True

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route("/")
def homepage():
    return redirect("/register")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    login_button = False
    if form.validate_on_submit():

        user = User(username=form.username.data, password=form.password.data, email=form.email.data,
                    first_name=form.first_name.data, last_name=form.last_name.data)
        db.session.add(user)
        db.session.commit()

        session['username'] = form.username.data
        flash('Registration successful', 'success')
        return redirect('/login')
    return render_template('users/register.html', form=form, login_button=login_button)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            session['username'] = form.username.data
            return render_template('users/show.html', user=user)
        else:
            flash('Invalid username or password', 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully', 'success')
    return redirect('/login')


@app.route('/users/<username>')
def user_profile(username):
    if 'username' in session:
        if session['username'] == username:
            user = User.query.filter_by(username=username).first()
            return render_template('users/show.html', user=user)
        else:
            flash('Unauthorized aqccess', 'danger')
            return render_template('404.html'), 404
    else:
        flash('You need to be logged in to view this page', 'warning')
        return redirect('/login')


@app.route('/users/<username>/feedback/new', methods=['GET', 'POST'])
def new_feedback(username):
    if 'username' in session:
        if session['username'] == username:
            form = FeedbackForm()

            if form.validate_on_submit():
                title = form.title.data
                content = form.content.data
                username = session['username']

                feedback = Feedback(
                    title=title, content=content, username=username)
                db.session.add(feedback)
                db.session.commit()

                flash('Feedback submitted successfully', 'success')
                return redirect('/feedback/list')

            return render_template('feedback/new.html', form=form)
        else:
            flash('Unauthorized access', 'danger')
            return redirect(f'/users/{session["username"]}')
    else:
        flash('You need to be logged in to submit feedback', 'warning')
        return redirect('/login')


@app.route('/feedback/edit/<int:feedback_id>', methods=['GET', 'POST'])
def edit_feedback(feedback_id):
    if 'username' in session:
        feedback = Feedback.query.get(feedback_id)

        if feedback:
            if feedback.username == session['username']:
                form = FeedbackForm(request.form, obj=feedback)
                delete_form = DeleteForm()

                if form.validate_on_submit():
                    feedback.title = form.title.data
                    feedback.content = form.content.data
                    db.session.commit()

                    flash('Feedback updated successfully', 'success')
                    return '/feedback/list'

                if delete_form.validate_on_submit():
                    db.session.delete(feedback)
                    db.session.commit()
                    flash('Feedback deleted successfully', 'success')
                    return '/feedback/list'

                return render_template('feedback/edit.html', form=form, feedback=feedback, delete_form=delete_form)
            else:
                flash('Unauthorized access', 'danger')
        else:
            flash('Feedback not found', 'danger')

        return f'/users/{session["username"]}'
    else:
        flash('You need to be logged in to edit feedback', 'warning')
        return '/login'


@app.route('/feedback/list')
def list_feedback():
    if 'username' in session:
        feedback_list = Feedback.query.filter_by(
            username=session['username']).all()
        return render_template('feedback/list.html', feedback_list=feedback_list)
    else:
        flash('You need to be logged in to view your feedback', 'warning')
        return '/login'


@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)

    if request.method == 'POST':

        title = request.form.get('title')
        content = request.form.get('content')
        feedback.title = title
        feedback.content = content
        db.session.commit()
        flash('Feedback updated successfully', 'success')
        return redirect('/feedback/list')

    return render_template('feedback/edit.html', feedback=feedback)
