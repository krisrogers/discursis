"""Tests for the projects module."""
import os

from werkzeug.datastructures import FileStorage

import projects


class TestProjects:
    """Test creation & deletion of projects."""

    def setup_class(self):
        """Setup."""
        self.name = '___test___'

    def teardown_class(self):
        """Cleanup."""
        project = projects.find(self.name)
        if project:
            projects.delete(project.id)

    def test_project(self):
        """Test creation and deletion of project."""
        num_projects = len(projects.list())

        # Create project
        f = open(os.path.join('test_data', 'denton-kennet.csv'), 'rb')
        project = projects.create(self.name, [FileStorage(f, f.name)])
        # project.generate_recurrence('composition')
        project.generate_recurrence('term-expansion', num_terms=100)

        assert len(projects.list()) == num_projects + 1

        assert len(project.get_term_clusters()) > 0

        print(project.get_term_clusters())

        # Delete project
        projects.delete(project.id)

        assert len(projects.list()) == num_projects
