"""Flask server for Discursis prototype."""
import ujson as json
import os

from flask import Flask, abort, request, Response
from flask_cors import CORS, cross_origin

import processing
import projects
from index import IndexReader


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
    return json.dumps([p.as_dict() for p in projects.list()])


@app.route('/projects/<id>/model', methods=['GET'])
@cross_origin()
def model(id):
    num_terms = request.args.get('num_terms', type=int, default=None)
    model = request.args.get('model')
    result = processing.generate_recurrence(projects.get_project_dir(id), model, num_terms)
    return json.dumps(result)


@app.route('/projects/<id>/similar_terms', methods=['GET'])
@cross_origin()
def similar_terms(id):
    """Get similar terms for this project."""
    project = projects.get(id)
    threshold = request.args.get('threshold', None, type=int)
    if threshold:
        clusters = project.get_term_clusters(threshold)
    else:
        clusters = project.get_term_clusters()
    print(123, clusters)
    return json.dumps(clusters)


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


@app.route('/plot', methods=['GET'])
@cross_origin()
def plot():
    """Generate plot from ad hoc project."""
    filter_terms = request.args.get('filter_terms', type=bool, default=False)
    print(filter_terms)
    import cProfile, pstats, io
    pr = cProfile.Profile()
    pr.enable()
    result = processing.generate_model(datadir, filter_terms)
    print(len(result['recurrence_matrix']))
    result = json.dumps(result)
    pr.disable()
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    # print(s.getvalue())
    return result


@app.route('/cluster', methods=['GET'])
@cross_origin()
def cluster():
    """Generate cluster from ad hoc project."""
    pass


if __name__ == '__main__':
    from gevent import pywsgi
    server = pywsgi.WSGIServer(('', 5000), app)
    server.serve_forever()
