"""Tests for the processing module."""
import os
import shutil

from werkzeug.datastructures import FileStorage

import index
import processing
import projects


class TestProcessing:
    """Test indexing of text data."""

    # TEST_FILE = 'test_data/Air France 447.csv'
    TEST_FILE = 'test_data/denton-kennet.csv'

    def setup_class(self):
        """Setup."""
        p = projects.find('__test__')
        if p:
            projects.delete(p.id)
        f = open(TestProcessing.TEST_FILE, 'rb')
        self.project = projects.create('__test__', [FileStorage(f, f.name)])
        self.project_path = self.project.get_path()

    def teardown_class(self):
        """Cleanup."""
        projects.delete(self.project.id)

    def test_cluster_layout(self):
        """Test generation of the cluster layout for an existing index."""
        # processing.generate_cluster_layout(self.project_path)
        # index_reader = index.IndexReader(self.project_path)
        # print(index_reader.get_cluster_layout())

    def test_recurrence(self):
        """Test generating recurrence for index."""
        n = 121
        result = processing.generate_recurrence(self.project_path, 'composition-delta', num_terms=100)
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.project_path, 'term')
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.project_path, 'composition')
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.project_path, 'term-expansion', num_terms=100)
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.project_path, 'term-expansion-delta', num_terms=100)
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n

    def test_similar_terms(self):
        index_reader = self.project.get_reader()
        terms = index_reader.get_terms_ordered()
        vectors, skipped_terms = processing.get_term_vectors(terms)
        terms = filter(lambda t: t not in skipped_terms, terms)
        # similarities = processing.find_similar_terms(terms, 1)
        # assertion
        # processing.generate_term_clusters(terms, similarities)

    def test_model(self):
        """Test modelling an index."""
        # processing.generate_model(self.data_dir, filter_terms=True)
