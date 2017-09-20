"""
This module allows creation and manipulation of projects.

Projects encapsulate data, settings and results for a recurrence analysis.
"""
import os
import shutil

from sqlalchemy import Column, Integer, String

from database import db_session, BaseModel
from index import IndexReader, IndexUpdater
import processing


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, 'projects')
ALLOWED_EXTENSIONS = set(['csv'])

# Create projects dir
if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)


class Project(BaseModel):
    """Project model."""

    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)

    def __init__(self, name):
        """Create new project."""
        self.name = name

    def add_data(self, files):
        """Load the project's data and process it."""
        project_path = self.get_path()
        os.makedirs(project_path)
        for f in files:
            filename = _safe_name(f.filename)
            f.save(os.path.join(project_path, filename))
            # file_size = os.path.getsize(os.path.join(project_path, filename))

        # Index data; TODO should be a separate process
        processing.index_files(project_path)
        # processing.generate_cluster_layout(datadir)

        self._create_expansion_model()

    def _create_expansion_model(self, threshold=0.5):
        """Create and store expansion model for this project."""
        project_path = self.get_path()
        terms = IndexReader(project_path).get_terms_ordered()
        distances = processing.find_similar_terms(terms, threshold)
        term_groups = processing.generate_term_clusters(terms, distances)
        print(term_groups)
        updater = IndexUpdater(project_path)
        updater.create_term_mappings(term_groups)
        updater.finish()

    def get_path(self):
        """Get path for this project's data & index."""
        return os.path.join(PROJECTS_DIR, str(self.id))

    def as_dict(self):
        """Get dict for this Project instance."""
        return {
            'id': self.id,
            'name': self.name
        }

    def generate_recurrence(self, model, num_terms=None):
        return processing.generate_recurrence(os.path.join(PROJECTS_DIR, str(self.id)), model, num_terms)

    def get_term_clusters(self, threshold=0.5):
        project_path = self.get_path()
        if threshold == 0.5:
            reader = IndexReader(project_path)
            return reader.get_clusters()
        print('wtf mate', threshold)
        terms = IndexReader(project_path).get_terms_ordered()
        distances = processing.find_similar_terms(terms, threshold)
        term_groups = processing.generate_term_clusters(terms, distances)
        return term_groups


class ProjectError(Exception):
    pass


def create(name, files):
    """
    Create project with `name` from the specified data `files`.

    Indexes the data before returning.before
    """
    if Project.query.filter_by(name=name).first():
        raise ProjectError('A project called {} already exists; Please use a different name.'.format(name))

    # Check filetypes
    for f in files:
        if not _allowed_file(f.filename):
            raise ProjectError('Invalid file type; Accepted types: {}'.format(ALLOWED_EXTENSIONS))

    # Create project
    project = Project(name)
    db_session.add(project)
    db_session.commit()
    project.add_data(files)

    return project


def delete(id):
    """Delete the specified project."""
    project = Project.query.get(id)
    db_session.delete(project)
    db_session.commit()
    shutil.rmtree(os.path.join(PROJECTS_DIR, str(project.id)))


def find(name):
    """Find Project by `name`."""
    return Project.query.filter_by(name=name).first()


def get(id):
    """Retrieve the specified project."""
    return Project.query.get(id)


def get_project_dir(id):
    """Just returns the project directory for project `id`."""
    return os.path.join(PROJECTS_DIR, id)


def list():
    """Return a list of all projects."""
    return Project.query.all()


def _allowed_file(filename):
    """Check for valid upload file type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _safe_name(unsafe_name, keepcharacters=(' ', '.', '_')):
    """Turn an unsafe filename into a safe one for saving to the OS."""
    return"".join(c for c in unsafe_name if c.isalnum() or c in keepcharacters).rstrip()
