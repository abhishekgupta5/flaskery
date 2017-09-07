import os
import time
import random
from flask import Flask, request, url_for, render_template, redirect, flash, session
from celery import Celery
from flask.ext.mail import Mail, Message

#Initialize App and mail extension
app = Flask(__name__)
mail = Mail(app)

#Celery config
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

#Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
accept_content = {'pickle'}

app.config['SECRET_KEY'] = 'top-secret!'

#Flask-Mail config
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SERVER'] = 'flask@example.com'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html', email=session.get('email',''))
    email = request.form['email']
    session['email'] = email

    #Send the email
    msg = Message('Hello from Flask', recipients=[request.form['email']])
    msg.body = 'This is a test email sent from background Celery task.'
    if request.form['submit'] == 'Send':
        #Send right away
        send_async_email.delay(msg)
        flash('Sending email to {0}'.format(email))
    else:
        #Send after a minute
        send_async_email.apply_async(args=[msg], countdown=60)
        flash("An email will be sent to {0} in one minute".format(email))
    return redirect(url_for('index'))


@celery.task()
def send_async_email(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)

if __name__ == '__main__':
    app.run(debug=True)
