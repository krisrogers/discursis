"""Tests for the processing module."""
import new_processing as processing


TEST_FILE = 'test_data/denton-kennet.csv'


class TestProcessing:
    """Test indexing of text data."""

    def setup_class(self):
        """Setup."""

    def teardown_class(self):
        """Cleanup."""

    def test_process_csv_file(self):
        processing.process_csv_file(open(TEST_FILE))
