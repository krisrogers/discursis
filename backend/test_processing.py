"""Tests for the processing module."""
import os
import shutil

import index
import processing
import projects


class TestProcessing:
    """Test indexing of text data."""

    TEST_FILE = 'test_data/denton-kennet.csv'

    def setup_class(self):
        """Setup."""
        self.data_dir = os.path.join(projects.PROJECTS_DIR, '__test__')
        os.makedirs(self.data_dir)
        shutil.copyfile(TestProcessing.TEST_FILE, os.path.join(self.data_dir, 'data.csv'))
        self.index_path = os.path.join(self.data_dir, 'index.db')

    def teardown_class(self):
        """Cleanup."""
        shutil.rmtree(self.data_dir)

    def test_index(self):
        """Test the actual creation of index from raw data."""
        processing.index_files(self.data_dir)

    def test_cluster_layout(self):
        """Test generation of the cluster layout for an existing index."""
        # processing.generate_cluster_layout(self.data_dir)
        # index_reader = index.IndexReader(self.data_dir)
        # print(index_reader.get_cluster_layout())

    def test_recurrence(self):
        """Test generating recurrence for index."""
        n = 121
        result = processing.generate_recurrence(self.data_dir, 'composition-delta', num_terms=100)
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.data_dir, 'term')
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.data_dir, 'composition')
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.data_dir, 'term-expansion', num_terms=100)
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.data_dir, 'term-expansion-delta', num_terms=100)
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n

    def test_similar_terms(self):
        index_reader = index.IndexReader(self.data_dir)
        terms = index_reader.get_terms_ordered()
        similarities = processing.find_similar_terms(terms)
        # assertion
        processing.generate_term_clusters(terms, similarities)

    def test_model(self):
        """Test modelling an index."""
        # processing.generate_model(self.data_dir, filter_terms=True)
