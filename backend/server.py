"""Flask server for Discursis prototype."""
import ujson as json

from flask import Flask, abort, request, Response
from flask_cors import CORS, cross_origin

import processing
import projects


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


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
    files = list(request.files.values())
    try:
        project = projects.create(project_name, files)
    except projects.ProjectError as e:
        app.logger.error(e)
        return abort(Response(json.dumps({'msg': str(e)}), 400))

    return json.dumps(project.as_dict())


@app.route('/cluster', methods=['GET'])
@cross_origin()
def cluster():
    """Generate cluster from ad hoc project."""
    pass


if __name__ == '__main__':
    from gevent import pywsgi
    server = pywsgi.WSGIServer(('', 5000), app)
    server.serve_forever()
