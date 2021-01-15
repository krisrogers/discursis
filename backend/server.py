"""Flask server for Discursis prototype."""
import csv
from datetime import datetime, timedelta
from functools import wraps
from hashlib import sha256
import io
import ujson as json

from celery import Celery
from flask import Flask, jsonify, request, Response, make_response
from flask_cors import CORS
from flask_mail import Mail, Message
from flask_migrate import Migrate
import jwt

import config
from database import db, User
import processing
import projects


def make_celery(app):
    """Setup celery for Flask."""
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    BaseTask = celery.Task  # noqa

    class ContextTask(BaseTask):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return BaseTask.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


# Setup Flask application
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config.from_object(config.ConfigClass)
mail = Mail(app)
celery = make_celery(app)


with app.app_context():
    db.init_app(app)
    # Create all database tables
    import projects  # noqa
    db.create_all()
    migrate = Migrate(app, db)


def token_required(f):
    """Decorator to require JWT authentication token on request endpoints."""
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_token = request.headers.get('Authorization', '')

        invalid_msg = {
            'message': 'Invalid token. Registration and / or authentication required',
            'authenticated': False
        }
        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }

        if len(auth_token) == 0:
            return make_response(jsonify(invalid_msg), 401)

        try:
            data = jwt.decode(auth_token, app.config['SECRET_KEY'])
            user = User.query.filter_by(email=data['sub']).first()
            if not user:
                raise RuntimeError('User not found')
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return make_response(jsonify(expired_msg), 401)
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return make_response(jsonify(invalid_msg), 401)

    return _verify


# Views
#
@app.route('/register/', methods=['POST'])
def register():
    """Register new email, returning JWT token."""
    data = request.get_json()

    # Check that email isn't already registered
    if User.query.filter_by(email=data['email']).first():
        return make_response(jsonify({'error': 'Email already registered'}), 400)

    user = User(**data)
    db.session.add(user)
    db.session.commit()

    token = jwt.encode({
        'sub': user.email,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=30)},
        app.config['SECRET_KEY'])
    return json.dumps({'token': token.decode('UTF-8')})


@app.route('/login/', methods=['POST'])
def login():
    """Login, returning JWT token."""
    data = request.get_json()
    user = User.authenticate(**data)

    if not user:
        return make_response(jsonify({'message': 'Invalid credentials', 'authenticated': False}), 400)

    token = jwt.encode({
        'sub': user.email,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=300)},
        app.config['SECRET_KEY'])
    return make_response(jsonify({'token': token.decode('UTF-8')}), 200)


@app.route('/send-reset-password-link/', methods=['POST'])
def send_reset_password_link():
    """Send reset password link, if a registered email matched the one specified."""
    data = request.get_json()
    base_url = data['base_url']
    user = User.query.filter_by(email=data['email']).first()
    if user:
        now = datetime.utcnow()
        exp = now + timedelta(minutes=60)
        hash = sha256((user.password + app.config['SECRET_KEY']).encode('utf-8')).hexdigest()
        token = jwt.encode({
            'sub': hash,
            'iat': now,
            'exp': exp
        }, app.config['SECRET_KEY'])
        msg = Message("Password Reset Link", sender="support@discursis.com", recipients=[user.email])
        msg.body = """
        Please visit the following link to reset your password:
        {}?token={}&email={}
        """.format(base_url, token.decode('UTF-8'), user.email)
        mail.send(msg)

    return ('', 204)


@app.route('/verify-reset-password-token/', methods=['POST'])
def verify_reset_password_token():
    """Reset password..."""
    try:
        data = request.get_json()
        email = data['email']
        token = data['token']
        data = jwt.decode(token, app.config['SECRET_KEY'])
        hash = data['sub']
        user = User.query.filter_by(email=email).first()
        if user and hash == sha256((user.password + app.config['SECRET_KEY']).encode('utf-8')).hexdigest():
            return('', 204)
        else:
            return make_response(jsonify({'invalid': True}), 401)
    except jwt.ExpiredSignatureError:
        return make_response(jsonify({'expired': True}), 401)
    except (jwt.InvalidTokenError, Exception) as e:
        print(e)
        return make_response(jsonify({'invalid': True}), 401)


@app.route('/update-password/', methods=['POST'])
def update_password():
    """Reset password..."""
    try:
        data = request.get_json()
        email = data['email']
        token = data['token']
        password = data['password']
        data = jwt.decode(token, app.config['SECRET_KEY'])
        hash = data['sub']
        user = User.query.filter_by(email=email).first()
        if user and hash == sha256((user.password + app.config['SECRET_KEY']).encode('utf-8')).hexdigest():
            user.update_password(password)
            db.session.commit()
            return('', 204)
        else:
            return make_response(jsonify({'invalid': True}), 401)
    except jwt.ExpiredSignatureError:
        return make_response(jsonify({'expired': True}), 401)
    except (jwt.InvalidTokenError, Exception) as e:
        print('exception')
        print(e)
        return make_response(jsonify({'error': True}), 401)


@app.route('/projects/<id>', methods=['DELETE'])
@token_required
def project_delete(current_user, id):
    """Delete the specified project."""
    projects.delete(id)
    return Response()


@app.route('/projects/<id>', methods=['GET'])
@token_required
def project_get(current_user, id):
    """Retrieve the specified project."""
    return json.dumps(projects.get(id).as_dict())


@app.route('/projects', methods=['GET'])
@token_required
def projects_list(current_user):
    """Get the list of projects."""
    return json.dumps([p.as_dict() for p in projects.listall()])


@app.route('/projects/<id>/model', methods=['GET'])
@token_required
def model(current_user, id):
    """Get recurrence model for the project."""
    num_terms = request.args.get('num_terms', type=int, default=None)
    model = request.args.get('model')
    result = processing.generate_recurrence(projects.get_project_dir(id), model, num_terms)
    return json.dumps(result)


@app.route('/projects/<id>/similar_terms', methods=['GET'])
@token_required
def similar_terms(current_user, id):
    """Get similar terms for this project."""
    project = projects.get(id)
    threshold = request.args.get('threshold', None, type=float)
    if threshold:
        clusters = project.generate_term_clusters(threshold)
    else:
        clusters = project.generate_term_clusters()
    ignored_terms = project.get_reader().get_ignored_terms()
    return json.dumps({
        'clusters': clusters,
        'ignored_terms': ignored_terms
    })


@app.route('/projects/<id>/term_layout', methods=['GET'])
@token_required
def term_layout(current_user, id):
    """Get 2d layout of terms for this project."""
    project = projects.get(id)
    reader = project.get_reader()
    positions = reader.get_term_layout()
    frequencies = reader.get_term_frequencies()
    clusters = project.generate_term_clusters()
    return json.dumps({
        'terms': [{
            'name': term,
            'position': positions[term],
            'frequency': frequency
        } for term, frequency in frequencies if term in positions],
        'clusters': clusters
    })


@app.route('/projects/<id>/term_links', methods=['GET'])
@token_required
def term_links(current_user, id):
    """Get 2d layout of terms for this project."""
    """project = projects.get(id)
    reader = project.get_reader()
    positions = reader.get_term_layout()
    frequencies = reader.get_term_frequencies()
    clusters = project.generate_term_clusters()
    return json.dumps({
        'terms': [{
            'name': term,
            'position': positions[term],
            'frequency': frequency
        } for term, frequency in frequencies if term in positions],
        'clusters': clusters
    })"""
    pass


@app.route('/upload', methods=['POST'])
@token_required
def upload(current_user):
    """Upload files to create a new project."""
    project_name = request.form.get('project_name')
    language = request.form.get('language').lower()
    tokenization = request.form.get('tokenization').lower()
    files = list(request.files.values())
    try:
        project = projects.create(project_name, files, language, tokenization)
    except projects.ProjectError as e:
        app.logger.error(e)
        return Response(json.dumps({'msg': str(e)}), 400)

    return json.dumps(project.as_dict())


@app.route('/projects/<id>/exports/channel-similarity', methods=['GET'])
@token_required
def download_channel_similarity(current_user, id):
    """Download channel similarity CSV with specified model parameters."""
    project = projects.get(id)
    num_terms = request.args.get('num_terms', type=int, default=None)
    model = request.args.get('model')
    f = io.StringIO()
    writer = csv.writer(f)
    writer.writerow(['From', 'To', 'Cumulative Similarity', 'Count'])
    writer.writerows(processing.generate_channel_similarity(projects.get_project_dir(id), model, num_terms))
    f.seek(0)
    response = make_response(f.read())
    filename = '{}-channel-similarity-{}-{}.csv'.format(project.name, model, num_terms or 'all')
    response.headers['Content-Disposition'] = 'attachment; filename=' + filename
    response.mimetype = 'text/csv'

    return response


@app.route('/projects/<id>/exports/primitives', methods=['GET'])
@token_required
def download_primitives(current_user, id):
    """Download primtivies CSV with specified model parameters."""
    project = projects.get(id)
    num_terms = request.args.get('num_terms', type=int, default=None)
    model = request.args.get('model')
    result = processing.generate_primitives(projects.get_project_dir(id), model, num_terms)
    fields = result[0]._fields
    f = io.StringIO()
    writer = csv.writer(f)
    headers = ['Utterance']
    headers.extend(fields)
    writer.writerow(headers)
    for i, r in enumerate(result):
        row = [i + 1]
        row.extend([getattr(r, field) for field in fields])
        writer.writerow(row)
    f.seek(0)
    response = make_response(f.read())
    filename = '{}-primitives-{}-{}.csv'.format(project.name, model, num_terms or 'all')
    response.headers['Content-Disposition'] = 'attachment; filename=' + filename
    response.mimetype = 'text/csv'

    return response


@app.route('/cluster', methods=['GET'])
@token_required
def cluster():
    """Generate cluster from ad hoc project."""
    pass


if __name__ == '__main__':
    from gevent import pywsgi
    server = pywsgi.WSGIServer(('', 5000), app)
    server.serve_forever()
