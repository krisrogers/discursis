"""
This module allows creation and manipulation of projects.

Projects encapsulate data, settings and results for a recurrence analysis.
"""
from collections import Counter
import csv
from io import TextIOWrapper
import os
import shutil

from sqlalchemy import Column, Integer, String

from database import db_session, BaseModel
from index import IndexReader, IndexUpdater, IndexWriter
import processing
import text_util


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
    language = Column(String(100))

    def __init__(self, name, language):
        """Create new project."""
        self.name = name
        self.language = language

    def add_data(self, files):
        """
        Load the project's data and process it.

        TODO async?
        """
        project_path = self.get_path()
        os.makedirs(project_path)
        index_writer = IndexWriter(project_path)

        for f in files:
            reader = csv.reader(TextIOWrapper(f))

            # Process headers
            channel_id = None
            metadata_index = {}
            headers = [h.lower() for h in next(reader)]
            for i, header in enumerate(headers):
                header = header.strip().lower()
                if header == 'text':
                    text_index = i
                else:
                    field_id = index_writer.add_metadata_field(header)
                    metadata_index[i] = field_id
                    if header in ('channel', 'speaker', 'name'):
                        channel_id = field_id

            # Process rows
            for row in reader:
                utterance_metadata = {}
                # TODO: split into smaller utterances?
                for i, cell in enumerate(row):
                    if i == text_index:
                        utterance_text = cell
                    else:
                        utterance_metadata[metadata_index[i]] = cell
                index_writer.add_utterance(
                    utterance_metadata[channel_id], utterance_text, utterance_metadata,
                    Counter(text_util.tokenize(utterance_text, language=self.language))
                )

        index_writer.finish()

        if self.language == 'english':
            # processing.generate_cluster_layout(datadir)
            self._create_term_layout()

    def get_reader(self):
        """Get `IndexReader` for this project."""
        return IndexReader(self.get_path())

    def generate_term_clusters(self, distance_threshold=0.01):
        """Generate term clusters for this project with given `distance_threshold`."""
        reader = self.get_reader()
        terms = reader.get_terms_ordered()
        term_positions = reader.get_term_layout()
        ignored_terms = reader.get_ignored_terms()
        terms = list(filter(lambda t: t not in ignored_terms, terms))
        positions = [term_positions[term] for term in terms]  # maintain order
        distances = processing.find_similar_terms(positions, distance_threshold)
        return processing.generate_term_clusters(terms, distances)

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

    def _create_term_layout(self):
        """Generate and store 2D projection of term vectors."""
        reader = self.get_reader()
        terms = reader.get_terms_ordered()
        positions, skipped_terms = processing.generate_2d_projection(terms)
        terms = list(filter(lambda t: t not in skipped_terms, terms))
        updater = self._get_updater()
        updater.save_term_layout(terms, positions.tolist())
        updater.save_ignored_terms(skipped_terms)
        updater.finish()

    def _get_writer(self):
        """Get `IndexWriter` for this project."""
        return IndexWriter(self.get_path())

    def _get_updater(self):
        """Get `IndexUpdater` for this project."""
        return IndexUpdater(self.get_path())



class ProjectError(Exception):
    pass


def create(name, files, language='english'):
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
    project = Project(name, language)
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


def listall():
    """Return a list of all projects."""
    return Project.query.all()


def _allowed_file(filename):
    """Check for valid upload file type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _safe_name(unsafe_name, keepcharacters=(' ', '.', '_')):
    """Turn an unsafe filename into a safe one for saving to the OS."""
    return"".join(c for c in unsafe_name if c.isalnum() or c in keepcharacters).rstrip()
