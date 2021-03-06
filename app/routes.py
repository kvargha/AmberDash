import os 
from flask import send_from_directory 
from app import app
from app import db
from app.forms import EditProfileForm
from app.forms import LoginForm
from app.models import User
from app.forms import RegistrationForm
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

import sys


@app.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')



@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Miguel'}
    posts = [
        {
            'author': {'username':'Test','name': 'Elon Musk', 'Description': 'Sexy', 'Age': 69420, 'Height': 69, "Weight": 420, 'Hair': 'Brown', 'Eyes': 'Brown'},
            'body': 'Buy my Teslas!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    # logic for getting database data
    # make a amber aler
    # car location 
    # color
    from .firebase import firebase
    firebase = firebase.FirebaseApplication('https://slugalert.firebaseio.com', None)
    amberMatchDict = firebase.get('/AmberMatch', None)
    amberAlertDict = firebase.get('/MockAmberAlert', None)

    amberMatches = []
    for key, value in amberMatchDict.items():
        amberAlertId = value['AmberAlert']
        value['AmberAlert'] = amberAlertDict[amberAlertId]
        recorded_time = datetime.strptime(value['Time'], '%H:%M:%S %m-%d-%Y')
        value['time_raw'] = recorded_time
        diff = datetime.now() - recorded_time
        value['diff_raw'] = diff
        value['time_difference'] = strfdelta(diff, "{hours} hours {minutes} minutes")

        amberMatches.append(value)

    #amberMatches = sorted(amberMatches, key=lambda x: int(strfdelta(x['diff_raw'], "{hours}")), reverse=True)
    amberMatches = sorted(amberMatches, key=lambda x: (x['diff_raw'] .seconds), reverse=False)
    #print(amberMatches, file=sys.stderr)

    return render_template("index.html", title='Home Page', posts=amberMatches)


def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)

@app.route('/about')
def about():
    return render_template("about.html", title='About Page')


def sendEmail():
    json_data = {"latitude": "1", "license_plate": "dasfdsaf", "longitude": "2", "police_email": "jonneka@gmail.com"}
    r = requests.post(url, json=json_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)
