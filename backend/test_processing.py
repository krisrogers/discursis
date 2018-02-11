"""Tests for the processing module."""
import numpy as np
from werkzeug.datastructures import FileStorage

import processing
import projects


class TestProcessing:
    """Test indexing of text data."""

    # TEST_FILE = 'test_data/Air France 447.csv'
    TEST_FILE = 'test_data/denton-kennet.csv'
    N = 121

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
        n = TestProcessing.N
        result = processing.generate_recurrence(self.project_path, 'composition-delta', num_terms=100)
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.project_path, 'term')
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n
        result = processing.generate_recurrence(self.project_path, 'composition')
        assert len(result['utterances']) == n and len(result['recurrence_matrix']) == n

    def test_channel_similarity(self):
        """Test generation of channel similarity export for an index."""
        result = list(processing.generate_channel_similarity(self.project_path, 'composition'))
        assert(len(result[0])) == 4

    def test_primitives(self):
        """Test generation of primitives export for an index."""
        similarities = np.array(processing.generate_recurrence(self.project_path, 'term')['recurrence_matrix'])
        result = processing.generate_primitives(self.project_path, 'term')

        def assert_primitive(index, end, field):
            # Determine step
            if 'backward' in field:
                step = -2
            else:
                step = 2

            # Determine start
            start = index
            if field.startswith('other'):
                # Handle offset for other
                if step < 0:
                    start -= 1
                else:
                    start += 1
            else:
                start += step

            # Calculate & verify
            v1 = getattr(result[index], field)
            assert v1 > 0
            v2 = 0
            n_samples = 0
            i = start
            while (step < 0 and i >= end) or (step > 0 and i <= end):
                v2 += similarities[index, i]
                n_samples += 1
                i += step
            assert v1 == v2 / n_samples

        # Sanity checking
        r0 = result[0]
        assert r0.self_backward_long == r0.self_backward_medium == r0.self_backward_short == 0
        assert r0.other_backward_long == r0.other_backward_medium == r0.other_backward_short == 0
        rn = result[-1]
        assert rn.self_forward_long == rn.self_forward_medium == rn.self_forward_short == 0
        assert rn.other_forward_long == rn.other_forward_medium == rn.other_forward_short == 0

        # Self backward
        assert_primitive(31, 27, 'self_backward_short')
        assert_primitive(52, 32, 'self_backward_medium')
        assert_primitive(102, 0, 'self_backward_long')

        # Self forward
        assert_primitive(12, 16, 'self_forward_short')
        assert_primitive(63, 83, 'self_forward_medium')
        assert_primitive(1, 119, 'self_forward_long')

        # Other backward
        assert_primitive(62, 59, 'other_backward_short')
        assert_primitive(43, 24, 'other_backward_medium')
        assert_primitive(51, 0, 'other_backward_long')

        # Other forward
        assert_primitive(61, 64, 'other_forward_short')
        assert_primitive(22, 41, 'other_forward_medium')
        assert_primitive(6, 119, 'other_forward_long')

    def test_similar_terms(self):
        """Test detection of similar terms for corpus."""
        index_reader = self.project.get_reader()
        terms = index_reader.get_terms_ordered()
        vectors, skipped_terms = processing.get_term_vectors(terms)
        terms = filter(lambda t: t not in skipped_terms, terms)
        # similarities = processing.find_similar_terms(terms, 1)
        # assertion
        # processing.generate_term_clusters(terms, similarities)

    def test_themes(self):
        """Test theme inference for utterances."""
        result = processing.generate_recurrence(self.project_path, 'composition')
        assert 'youth' in result['utterances'][81]['themes']
        assert 'young' in result['utterances'][81]['themes']
        assert 'suicide' in result['utterances'][81]['themes']
        themes = set()
        for u in result['utterances']:
            themes.update(set(u['themes']))
        assert len(themes) == 176

    def test_model(self):
        """Test modelling an index."""
        # processing.generate_model(self.data_dir, filter_terms=True)
