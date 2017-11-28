"""Tests for the projects module."""
import os

from werkzeug.datastructures import FileStorage

import projects


class TestProjects:
    """Test creation & deletion of projects."""

    def setup_class(self):
        """Setup."""
        self.name = '___test___'

    def teardown_method(self):
        """Cleanup."""
        project = projects.find(self.name)
        if project:
            projects.delete(project.id)

    def test_project(self):
        """Test creation and deletion of project."""
        num_projects = len(projects.listall())

        # Create project
        f = open(os.path.join('test_data', 'denton-kennet.csv'), 'rb')
        project = projects.create(self.name, [FileStorage(f, f.name)])
        term_positions = list(project.get_reader().get_term_layout())
        assert len(term_positions) == \
            len(project.get_reader().get_terms_ordered()) - len(project.get_reader().get_ignored_terms())
        project.generate_recurrence('composition')
        # project.generate_recurrence('term-expansion', num_terms=100)

        assert len(projects.listall()) == num_projects + 1

        assert len(project.generate_term_clusters()) > 0

        # Delete project
        projects.delete(project.id)

        assert len(projects.listall()) == num_projects

    def test_bug(self):
        # Create project
        f = open(os.path.join('test_data', 'T3_ID20.csv'), 'rb')
        project = projects.create(self.name, [FileStorage(f, f.name)])
        term_positions = list(project.get_reader().get_term_layout())
        assert len(term_positions) == \
            len(project.get_reader().get_terms_ordered()) - len(project.get_reader().get_ignored_terms())
        # project.generate_recurrence('composition')
        project.generate_recurrence('term-expansion', num_terms=100)
