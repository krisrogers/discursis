"""Processing functions."""
from collections import defaultdict, namedtuple

import numpy as np
from scipy.spatial import distance
from scipy import spatial
from scipy.sparse.csgraph import connected_components
from sklearn import cluster, manifold

from index import IndexReader, IndexUpdater
import util

BOOLEAN_FREQ = True


# Load PP-XXL Embeddings
PP_EMBEDDINGS = {}
for embedding in open('resources/paragram-phrase-XXL.txt'):
    parts = embedding.split(' ')
    PP_EMBEDDINGS[parts[0]] = [float(v) for v in parts[1:]]


# Load ZH Embeddings
for embedding in open('resources/zh.tsv'):
    parts = embedding.split('\t')
    vals = [float(v) for v in parts[1].split(',')]
    if parts[0] not in PP_EMBEDDINGS:
        PP_EMBEDDINGS[parts[0]] = vals


def get_term_vectors(terms):
    """Get vectors for `terms` with paraphrase embeddings."""
    skipped_terms = []
    vectors = []
    for term in terms:
        try:
            vectors.append(PP_EMBEDDINGS[term])
        except KeyError:
            skipped_terms.append(term)

    return (vectors, skipped_terms)


def generate_2d_projection(terms):
    """Project `terms` into 2D space."""
    term_vectors, skipped_terms = get_term_vectors(terms)
    # return manifold.TSNE(perplexity=5).fit_transform(term_vectors)  # TODO: check params
    positions = manifold.TSNE(perplexity=5, learning_rate=75).fit_transform(term_vectors)  # TODO: check params
    return (positions, skipped_terms)


def find_similar_terms(positions, distance_threshold):
    """Return sparse matrix of similar terms based on `positions` within `distance_threshold`."""
    distances = distance.cdist(positions, positions)
    avg_distance = np.mean(distances)
    return distances <= (avg_distance * distance_threshold)


def generate_term_clusters(terms, distances):
    """Transform similar terms `distances` matrix into dictionary of clusters mapping name -> terms."""
    n_components, components = connected_components(distances)
    components = list(filter(lambda l: len(l) > 1, [np.where(components == i)[0] for i in range(n_components)]))
    clusters_by_name = {}
    for i, c in enumerate(components):
        lead_term = terms[c[0]]
        cluster_terms = [terms[i] for i in c]
        clusters_by_name[lead_term] = cluster_terms

    return clusters_by_name


def generate_cluster_layout(dir, n_clusters=25):
    """Generate term layout using TSNE."""
    index_reader = IndexReader(dir)
    terms = index_reader.get_terms_ordered()
    term_vectors = [PP_EMBEDDINGS.get(term, np.zeros(300)) for term in terms]
    positions = manifold.TSNE().fit_transform(term_vectors)  # TODO: check params
    clusters = cluster.KMeans(n_clusters=n_clusters).fit_predict(positions)
    index_writer = IndexUpdater(dir)
    index_writer.save_cluster_layout(terms, positions, clusters)
    index_writer.finish()


def generate_term_matrix(project_dir):
    index_reader = IndexReader(project_dir)
    for u_data in index_reader.get_utterances():
        utterance_terms = u_data[3].split('::') if u_data[3] else []
        print (utterance_terms)


def generate_recurrence(
    project_dir, model, num_terms=None,
    start=0, limit=250, include_text=True, delta=False, n_themes=3
):
    """
    Generate recurrence for an index.recurrence_matrix.

    # TODO -- partial update (no text excerpts)

    `model` specifies type of recurrence model used (term, composition)
    """
    index_reader = IndexReader(project_dir)
    terms = index_reader.get_terms_ordered()
    ignored_terms = []
    filter_terms = None
    if num_terms:
        filter_terms = set(terms[:num_terms])

    # TODO make this a real param
    if model.endswith('-delta'):
        model = model.replace('-delta', '')
        delta = True

    # Load vectors
    if model == 'composition':
        # Paraphrase compositional model
        concept_vectors = {
            term: PP_EMBEDDINGS.get(term, np.zeros(300))
            for term in terms
        }
        n_dims = 300
        if delta:
            term_vectors = util.generate_term_vectors(terms)
        tree = spatial.cKDTree(list(concept_vectors.values()))
        labels = list(concept_vectors.keys())
        ignored_terms = index_reader.get_ignored_terms()
    elif model in ('term', 'term-expansion'):
        # Term model
        concept_vectors = util.generate_term_vectors(terms)
        n_dims = len(terms)
        if delta:
            term_vectors = concept_vectors

    # Term mappings & filter terms
    if num_terms:
        filter_terms = set(terms[:num_terms])

    # Load utterances and calculate embeddings
    utterances = []
    utterance_embeddings = []
    channels = []
    if delta:
        utterance_embeddings_term = []
    for u_data in index_reader.get_utterances(start, limit, include_text):
        channel = u_data[1]
        utterance_terms = u_data[3].split('::') if u_data[3] else []
        utterance_concepts = utterance_terms
        if filter_terms:
            utterance_concepts = list(filter(
                lambda t: t in filter_terms and t not in ignored_terms,
                utterance_concepts
            ))
        utterance = {
            'id': u_data[0],
            'channel': channel,
            'length': u_data[2],
            'terms': utterance_terms,  # All terms
            'concepts': utterance_concepts  # Filtered/mapped
        }
        if include_text:
            utterance['text'] = u_data[4]
        if channel not in channels:
            channels.append(channel)
        # Calcualte utterance embedding
        utterance_concept_vectors = [
            concept_vectors[term]
            for term in utterance_concepts
        ]
        if len(utterance_concept_vectors):
            if model == 'composition':
                if len(utterance_concept_vectors) > 1:
                    embedding = np.sum(utterance_concept_vectors, axis=0)
                else:
                    embedding = utterance_concept_vectors[0]
            else:
                embedding = np.sum(utterance_concept_vectors, axis=0)
        else:
            embedding = np.zeros(n_dims)
        if delta:
            utterance_term_vectors = np.array([
                term_vectors[term]
                for term in filter(lambda t: not filter_terms or t in filter_terms, utterance_terms)
            ])
            if len(utterance_term_vectors):
                utterance_embeddings_term.append(np.sum(utterance_term_vectors, axis=0))
            else:
                utterance_embeddings_term.append(np.zeros(len(terms)))

        utterance_embeddings.append(embedding)

        if model == 'composition':
            if (len(utterance_terms) > 0):
                hits = tree.query(embedding, k=n_themes)[1]
                utterance['themes'] = ([labels[i] for i in hits[:len(utterance_terms)]])
            else:
                utterance['themes'] = []

        utterances.append(utterance)

    utterance_embeddings = np.array(utterance_embeddings)
    recurrence_matrix = np.nan_to_num((1 - distance.squareform(distance.pdist(utterance_embeddings, metric='cosine'))))
    recurrence_matrix = np.clip(recurrence_matrix, 0, 1)
    if delta:
        utterance_embeddings_term = np.array(utterance_embeddings_term)
        recurrence_matrix_term = np.nan_to_num((1 - distance.squareform(
            distance.pdist(utterance_embeddings_term, metric='cosine')))
        )
        recurrence_matrix_term = np.clip(recurrence_matrix_term, 0, 1)
        recurrence_matrix = np.subtract(recurrence_matrix, recurrence_matrix_term)

    return {
        'utterances': utterances,
        'utterance_count': index_reader.get_utterance_count(),
        'recurrence_matrix': recurrence_matrix.tolist(),
        'channels': channels
    }


def generate_channel_similarity(project_dir, model, num_terms=None):
    """
    Generate channel similarities.

    Returns tuple containing (channel pair, cumulative similarity, count).
    """
    recurrence = generate_recurrence(project_dir, model, num_terms, limit=None, include_text=False)
    channel_similarity = defaultdict(int)
    channel_cooccurrence = defaultdict(int)
    for u1 in recurrence['utterances']:
        for u2 in recurrence['utterances']:
            if u2['id'] > u1['id']:  # forward direction only
                ch_key = (u1['channel'], u2['channel'])
                channel_similarity[ch_key] += recurrence['recurrence_matrix'][u1['id']][u2['id']]
                channel_cooccurrence[ch_key] += 1

    return map(
        lambda ch_key: (ch_key[0], ch_key[1], channel_similarity[ch_key], channel_cooccurrence[ch_key]),
        channel_similarity.keys()
    )


Primitives = namedtuple('Primitives', [
    'self_backward_short', 'self_backward_medium', 'self_backward_long',
    'self_forward_short', 'self_forward_medium', 'self_forward_long',
    'other_backward_short', 'other_backward_medium', 'other_backward_long',
    'other_forward_short', 'other_forward_medium', 'other_forward_long'
])


def generate_primitives(project_dir, model, num_terms=None, short_range=2, medium_range=10):
    """
    Generate primitives for an index with specified model parameters.

    Returns a list of `Primitives`.
    """
    utterance_primitives = []
    recurrence = generate_recurrence(project_dir, model, num_terms, limit=None, include_text=False)

    # Precalculate ids by channel
    channel_utterances = defaultdict(list)
    ids = []
    for u in recurrence['utterances']:
        channel_utterances[u['channel']].append(u['id'])
        ids.append(u['id'])

    def calc_primitive(vals):
        return np.sum(vals) / len(vals) if len(vals) else 0

    # Calculate primitives for each utterance
    similarities = np.array(recurrence['recurrence_matrix'])
    for u in recurrence['utterances']:
        self_ids = channel_utterances[u['channel']]
        other_ids = list(filter(lambda i: i not in self_ids, ids))

        # Self Backward
        self_backward_ids = list(filter(lambda i: i < u['id'], self_ids))
        sbl_vals = similarities[u['id'], self_backward_ids]
        self_backward_long = calc_primitive(sbl_vals)
        sbm_vals = similarities[u['id'], self_backward_ids[-medium_range:]]
        self_backward_medium = calc_primitive(sbm_vals)
        sbs_vals = similarities[u['id'], self_backward_ids[-short_range:]]
        self_backward_short = calc_primitive(sbs_vals)

        # Self Forward
        self_forward_ids = list(filter(lambda i: i > u['id'], self_ids))
        sfl_vals = similarities[u['id'], self_forward_ids]
        self_forward_long = calc_primitive(sfl_vals)
        sfm_vals = similarities[u['id'], self_forward_ids[:medium_range]]
        self_forward_medium = calc_primitive(sfm_vals)
        sfs_vals = similarities[u['id'], self_forward_ids[:short_range]]
        self_forward_short = calc_primitive(sfs_vals)

        # Other Backward
        other_backward_ids = list(filter(lambda i: i < u['id'], other_ids))
        obl_vals = similarities[u['id'], other_backward_ids]
        other_backward_long = calc_primitive(obl_vals)
        obm_vals = similarities[u['id'], other_backward_ids[-medium_range:]]
        other_backward_medium = calc_primitive(obm_vals)
        obs_vals = similarities[u['id'], other_backward_ids[-short_range:]]
        other_backward_short = calc_primitive(obs_vals)

        # Other Forward
        other_forward_ids = list(filter(lambda i: i > u['id'], other_ids))
        ofl_vals = similarities[u['id'], other_forward_ids]
        other_forward_long = calc_primitive(ofl_vals)
        ofm_vals = similarities[u['id'], other_forward_ids[:medium_range]]
        other_forward_medium = calc_primitive(ofm_vals)
        ofs_vals = similarities[u['id'], other_forward_ids[:short_range]]
        other_forward_short = calc_primitive(ofs_vals)

        # utterance_primitives.append
        utterance_primitives.append(Primitives(
            self_backward_short, self_backward_medium, self_backward_long,
            self_forward_short, self_forward_medium, self_forward_long,
            other_backward_short, other_backward_medium, other_backward_long,
            other_forward_short, other_forward_medium, other_forward_long
        ))

    return utterance_primitives
