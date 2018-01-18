"""Flask server for Discursis prototype."""
import csv
import io
import ujson as json

from celery import Celery
from flask import Flask, abort, request, Response, make_response
from flask_cors import CORS, cross_origin

import processing
import projects


def make_celery(app):
    """Setup celery for Flask."""
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    BaseTask = celery.Task

    class ContextTask(BaseTask):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return BaseTask.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

# Setup Flask application
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024    # 5 Mb limit
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)


@app.route('/projects/<id>', methods=['DELETE'])
@cross_origin()
def project_delete(id):
    """Delete the specified project."""
    projects.delete(id)
    return Response()


@app.route('/projects/<id>', methods=['GET'])
@cross_origin()
def project_get(id):
    """Retrieve the specified project."""
    return json.dumps(projects.get(id).as_dict())


@app.route('/projects', methods=['GET'])
@cross_origin()
def projects_list():
    """Get the list of projects."""
    return json.dumps([p.as_dict() for p in projects.listall()])


@app.route('/projects/<id>/model', methods=['GET'])
@cross_origin()
def model(id):
    """Get recurrence model for the project."""
    num_terms = request.args.get('num_terms', type=int, default=None)
    model = request.args.get('model')
    result = processing.generate_recurrence(projects.get_project_dir(id), model, num_terms)
    return json.dumps(result)


@app.route('/projects/<id>/similar_terms', methods=['GET'])
@cross_origin()
def similar_terms(id):
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
@cross_origin()
def term_layout(id):
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


@app.route('/upload', methods=['POST'])
@cross_origin()
def upload():
    """Upload files to create a new project."""
    project_name = request.form.get('project_name')
    language = request.form.get('language').lower()
    files = list(request.files.values())
    try:
        project = projects.create(project_name, files, language)
    except projects.ProjectError as e:
        app.logger.error(e)
        return abort(Response(json.dumps({'msg': str(e)}), 400))

    return json.dumps(project.as_dict())


@app.route('/projects/<id>/exports/channel-similarity', methods=['GET'])
def download_channel_similarity(id):
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
def download_primitives(id):
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
@cross_origin()
def cluster():
    """Generate cluster from ad hoc project."""
    pass


if __name__ == '__main__':
    from gevent import pywsgi
    server = pywsgi.WSGIServer(('', 5000), app)
    server.serve_forever()
