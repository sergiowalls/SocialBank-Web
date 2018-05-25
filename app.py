import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey

app = Flask(__name__)
CORS(app)
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PW = os.environ['POSTGRES_PW']
POSTGRES_URL = os.environ['POSTGRES_URL']
POSTGRES_DB = os.environ['POSTGRES_DB']
DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user=POSTGRES_USER, pw=POSTGRES_PW, url=POSTGRES_URL,
                                                               db=POSTGRES_DB)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
db = SQLAlchemy(app)


class User(db.Model):
    email = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    surname = db.Column(db.String(255))
    enabled = db.Column(db.Boolean)
    verified_account = db.Column(db.Boolean)

    def toJSON(self):
        return {'email': self.email,
                'name': self.name,
                'surname': self.surname,
                'enabled': self.enabled,
                'verified': self.verified_account}


class Report(db.Model):
    reporter = db.Column(db.String(255), ForeignKey("user.email"), primary_key=True)
    reported = db.Column(db.String(255), ForeignKey("user.email"), primary_key=True)

    def toJSON(self):
        return {'reporter': self.reporter,
                'reported': self.reported}


class RequestAccountVerification(db.Model):
    user = db.Column(db.String(255), ForeignKey("user.email"), primary_key=True)
    message = db.Column(db.String(255))

    def toJSON(self):
        return {'user': self.user,
                'message': self.message}


@app.route('/users')
def get_users():
    users = User.query.all()
    return jsonify([user.toJSON() for user in users])


@app.route('/reported_users')
def get_reported_users():
    reports = []
    for report in Report.query.all():
        dictionary = report.toJSON()
        dictionary['enabled'] = User.query.filter_by(email=report.reported).first().enabled
        reports.append(dictionary)

    return jsonify(reports)


@app.route('/requested_verifications')
def get_requested_verifications():
    requests = []
    for request in RequestAccountVerification.query.all():
        dictionary = request.toJSON()
        dictionary['verified'] = User.query.filter_by(email=request.user).first().verified_account
        requests.append(dictionary)

    return jsonify(requests)


@app.route('/users/<email>/verified', methods=['POST'])
def verify_user(email):
    user = User.query.filter_by(email=email).first()
    user.verified_account = True
    db.session.commit()
    return jsonify(''), 204


@app.route('/users/<email>/banned', methods=['POST'])
def ban_user(email):
    user = User.query.filter_by(email=email).first()
    user.enabled = False
    db.session.commit()
    return jsonify(''), 204


@app.route('/users/<email>/banned', methods=['DELETE'])
def unban_user(email):
    user = User.query.filter_by(email=email).first()
    user.enabled = True
    db.session.commit()
    return jsonify(''), 204


if __name__ == '__main__':
    app.run(host=os.environ['HOST'], port=os.environ['PORT'], threaded=True)
