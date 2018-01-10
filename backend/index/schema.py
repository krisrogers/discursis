"""The schema scripts for the bulk operations of the :class:`.SqliteStorage`."""

# Schema for indexes
index_schema = """
begin;

create table metadata_field (
    id integer primary key,
    name text unique
);

create table utterance (
    id integer primary key,
    sequence integer,
    channel text,
    length integer
);

create table utterance_text (
    utterance_id integer primary key,
    stored text,
    foreign key(utterance_id) references utterance(id)
);

create table utterance_metadata (
    field_id integer,
    value,
    utterance_id integer,
    primary key(field_id, value, utterance_id),
    foreign key(utterance_id) references utterance(id),
    foreign key(field_id) references metadata_field(id)
);

create table utterance_term (
    utterance_id integer,
    term text,
    frequency integer,
    primary key(utterance_id, term),
    foreign key(utterance_id) references utterance(id)
);

create table term_stats (
    term text primary key,
    frequency integer
);

create table term_layout (
    term text primary key,
    x real,
    y real,
    foreign key(term) references term_stats(term)
);

create table ignored_terms (
    term text primary key,
    foreign key(term) references term_stats(term)
);

commit;
"""
