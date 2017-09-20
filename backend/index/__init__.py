"""This module provides access to creating and manipulating indexes."""
from collections import Counter
import os
import sqlite3

from .schema import index_schema


INDEX_FILE = 'index.db'


class IndexWriter:
    """Allow creation of an index."""

    def __init__(self, index_path):
        """Create the index at `index_path`."""
        self.field_id = 0
        self.utterance_num = 0
        self.term_freqs = Counter()
        self.connection = sqlite3.connect(os.path.join(index_path, INDEX_FILE))

        # Initialise index
        list(self.connection.cursor().executescript(index_schema))

        # Cursor for future writing
        self.cursor = self.connection.cursor()

    def add_metadata_field(self, field_name):
        """Register metadata field on the index."""
        self.cursor.execute('insert into metadata_field(id, name) values(?, ?)', [self.field_id, field_name])
        field_id = self.field_id
        self.field_id += 1
        return field_id

    def add_utterance(self, channel, text, metadata, term_counts):
        """Add analysed utterance including text and metadata."""
        self.cursor.execute(
            'insert into utterance(id, channel, length) values (?, ?, ?)',
            [self.utterance_num, channel, len(text)]
        )
        self.cursor.execute(
            'insert into utterance_text(utterance_id, stored) values (?, ?)',
            [self.utterance_num, text]
        )

        # Add metadata fields
        insert_rows = ((self.utterance_num, field, value) for field, value in metadata.items())
        self.cursor.executemany(
            'insert into utterance_metadata(field_id, value, utterance_id) values (?, ?, ?)',
            insert_rows
        )

        # Utterance term frequencies
        insert_term_data = (
            (self.utterance_num, term, frequency)
            for term, frequency in term_counts.items()
        )
        self.cursor.executemany(
            'insert into utterance_term(utterance_id, term, frequency) values (?, ?, ?)',
            insert_term_data
        )

        self.term_freqs.update(list(term_counts.keys()))
        self.utterance_num += 1  # increment utterance number

    def finish(self):
        """Close the connection to index with any final updates."""

        # Term stats
        insert_term_data = list(self.term_freqs.items())
        self.cursor.executemany(
            'insert into term_stats(term, frequency) values(?, ?)',
            insert_term_data
        )
        # Add foreign key to utterance term table
        """
        NOT SUPPORTED BY SQLITE
        self.cursor.execute(
            'alter table utterance_term add constraint term foreign key(term) references term_stats(term)'
        )
        """
        # Finalise
        self.connection.commit()
        self.connection.close()


class IndexUpdater:
    """Allow updating of an index."""

    def __init__(self, index_path):
        self.connection = sqlite3.connect(os.path.join(index_path, INDEX_FILE))
        # Cursor for future writing
        self.cursor = self.connection.cursor()

    def save_cluster_layout(self, terms, positions, term_clusters):
        """Save cluster layout of terms."""
        insert_data = ((
            term,
            positions[i][0],
            positions[i][1],
            term_clusters[i]
        ) for i, term in enumerate(terms))
        self.cursor.executemany(
            'insert into cluster_layout(term, x, y, cluster_id) values (?, ?, ?, ?)',
            insert_data
        )

    def create_term_mappings(self, term_groups):
        insert_data = []
        for lead_term, terms in term_groups.items():
            for term in terms:
                for aa in insert_data:
                    if aa[0] == term:
                        print('wtf', terms, aa)
                insert_data.append((term, lead_term))
        self.cursor.executemany(
            'insert into term_mapping(term, mapped_term) values (?, ?)',
            insert_data
        )

    def finish(self):
        """Close the connection to index with any final updates."""
        self.connection.commit()
        self.connection.close


class IndexReader:
    """Allow reading from an index."""
    def __init__(self, index_path):
        self.connection = sqlite3.connect(os.path.join(index_path, INDEX_FILE))
        self.cursor = self.connection.cursor()

    def get_utterances(self, start, limit, include_text=False):
        q = (
            "select id, channel, length, group_concat(term, '::')" +

            # Utterance text
            (", stored" if include_text else "") +
            #

            """
            from utterance
            left outer join utterance_term on utterance_term.utterance_id = utterance.id
            """ +

            # Utterance text join
            ("""
            join utterance_text on utterance_text.utterance_id = utterance.id
            """ if include_text else "") +
            #

            """

            where id >= ? and id < ?
            group by id, utterance_term.utterance_id
            order by id asc
            """
        )
        print(q)
        return self.cursor.execute(q, (start, start + limit)).fetchall()

    def get_top_terms(self, limit):
        """Return `limit` top terms by frequency."""
        return self.cursor.execute(
            'select term from term_stats order by frequency desc limit ?', (limit,)
        ).fetchall()

    def get_terms_ordered(self):
        """Return ordered list of all terms."""
        return [t[0] for t in self.cursor.execute(
            'select term from term_stats order by frequency desc'
        ).fetchall()]

    def get_clusters(self):
        return {
            t[0]: t[1].split(',')
            for t in self.cursor.execute('select mapped_term, group_concat(term) from term_mapping group by mapped_term')
        }

    def get_cluster_layout(self):
        """Return cluster layout of terms."""
        return self.cursor.execute(
            'select term, x, y, cluster from cluster_layout'
        ).fetchall()


def delete_index(index_path):
    """Delete index at specified `index_path`."""
    os.remove(index_path)
