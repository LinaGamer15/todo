from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Length, Email
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL1', 'sqlite:///todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


options = ''


# forms
class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    login = StringField('Login', validators=[DataRequired(), Length(min=8)])
    password = PasswordField('Password (must be at least 12 characters long)',
                             validators=[DataRequired(), Length(min=12)])
    repeat_password = PasswordField('Repeat Password', validators=[DataRequired(), Length(min=12)])
    submit = SubmitField('OK')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    login = StringField('Login', validators=[DataRequired(), Length(min=8)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=12)])
    submit = SubmitField('OK')


class NumberForm(FlaskForm):
    number = StringField(validators=[DataRequired(), Length(max=2)])
    submit = SubmitField('OK')


class CreatePlan(FlaskForm):
    option = StringField('Option', validators=[DataRequired()])
    submit = SubmitField('OK')


# db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False, unique=True)
    email = db.Column(db.String(250), nullable=False, unique=True)
    login = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    plan = db.Column(db.String(250), nullable=False)
    plan_day_or_month = db.Column(db.String, nullable=False)
    time_start = db.Column(db.String(250), nullable=False)
    time_final = db.Column(db.String(250), nullable=False)


db.create_all()


@app.route('/')
def home():
    return render_template('index.html', current_user=current_user)


@app.route('/signin', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        login1 = form.login.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('That email does not exist, please try again.')
            return redirect(url_for('login'))
        if not check_password_hash(user.login, login1):
            flash('Login incorrect, please try again.')
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
        else:
            login_user(user)
            return redirect(url_for('profile'))
    return render_template('signIn.html', form=form, current_user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(name=form.name.data).first():
            flash('This name is already in use')
        elif User.query.filter_by(email=form.email.data).first():
            flash('You\'ve already signed up with that email, log in instead!')
            return redirect(url_for('login'))
        elif form.password.data == form.repeat_password.data:
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
            hashed_login = generate_password_hash(form.login.data, method='pbkdf2:sha256', salt_length=8)
            new_user = User(name=form.name.data, email=form.email.data, login=hashed_login, password=hashed_password,
                            plan_day_or_month='', plan='', time_start='', time_final='')
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('profile'))
    return render_template('register.html', form=form, current_user=current_user)


@app.route('/profile')
@login_required
def profile():
    user = User.query.filter_by(id=current_user.id).first()
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    if user.time_final != '' and datetime.strptime(now, '%Y-%m-%dT%H:%M:%SZ') < datetime.strptime(user.time_final,
                                                                                                  '%Y-%m-%dT%H:%M:%SZ'):
        if user.plan != '':
            list_options = user.plan_day_or_month.strip().split('  ')
            counts_options = len(list_options)
    elif user.time_final != '' and datetime.strptime(now, '%Y-%m-%dT%H:%M:%SZ') >= datetime.strptime(user.time_final,
                                                                                                  '%Y-%m-%dT%H:%M:%SZ'):
        flash('You did not complete the plan in time')
    else:
        list_options = ''
        counts_options = len(list_options)
    return render_template('profile.html', current_user=current_user, list_options=list_options, count=counts_options)


@app.route('/profile/create')
@login_required
def todo():
    return render_template('TODO.html', current_user=current_user)


@app.route('/profile/create/<plan>', methods=['GET', 'POST'])
@login_required
def choose(plan):
    form = NumberForm()
    if form.validate_on_submit():
        return redirect(url_for('create', plan=plan, count=int(form.number.data)))
    return render_template('add_plan.html', plan=plan, form=form, current_user=current_user)


@app.route('/profile/create/<plan>/<int:count>', methods=['GET', 'POST'])
@login_required
def create(plan, count):
    global options
    form = CreatePlan()
    user_name = current_user.name
    user = User.query.filter_by(name=user_name).first()
    user.plan = plan
    db.session.commit()
    if form.validate_on_submit() and count != 0:
        options += f'{form.option.data}  '
        return redirect(url_for('create', plan=plan, count=count - 1))
    elif count == 0:
        if plan == 'day' or plan == 'month':
            if user.plan_day_or_month == '':
                user.plan_day_or_month = options
                user.time_start = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                db.session.commit()
                options = ''
                if plan == 'day':
                    user.time_final = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
                    db.session.commit()
                elif plan == 'month':
                    user.time_final = (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
                    db.session.commit()
            else:
                flash(f'You already have a plan')
        return redirect(url_for('profile'))
    return render_template('create_plan.html', plan=plan, count=count, form=form, current_user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/done')
@login_required
def done():
    user = User.query.filter_by(id=current_user.id).first()
    list_options = user.plan_day_or_month.strip().split('  ')
    del list_options[0]
    new_options = '  '.join(map(str, list_options))
    user.plan_day_or_month = new_options
    db.session.commit()
    if user.plan_day_or_month == '':
        user.plan = ''
        user.time_start = ''
        user.time_final = ''
        db.session.commit()
    return redirect(url_for('profile'))


@app.route('/delete')
@login_required
def delete():
    user = User.query.filter_by(id=current_user.id).first()
    user.plan = ''
    user.plan_day_or_month = ''
    user.time_start = ''
    user.time_final = ''
    db.session.commit()
    return redirect(url_for('profile'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
