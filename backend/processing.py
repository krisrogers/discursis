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
NUM_TERMS = 200


# Load PP-XXL Embeddings
PP_EMBEDDINGS = {}
for embedding in open('resources/paragram-phrase-XXL.txt'):
    parts = embedding.split(' ')
    PP_EMBEDDINGS[parts[0]] = [float(v) for v in parts[1:]]


# Load stopwords
STOPWORDS = [w.strip() for w in open('resources/stopwords-english.txt')]


Model = namedtuple('Model', ['text_embeddings'])


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
    index_reader = IndexReader(dir)
    terms = index_reader.get_terms_ordered()
    term_vectors = [PP_EMBEDDINGS.get(term, np.zeros(300)) for term in terms]
    positions = manifold.TSNE().fit_transform(term_vectors)  # TODO: check params
    clusters = cluster.KMeans(n_clusters=n_clusters).fit_predict(positions)
    index_writer = IndexUpdater(dir)
    index_writer.save_cluster_layout(terms, positions, clusters)
    index_writer.finish()


def generate_recurrence(project_dir, model, num_terms=None, start=0, limit=250, include_text=True, delta=False):
    """
    Generate recurrence for an index.recurrence_matrix

    # TODO -- partial update (no text excerpts)

    `model` specifies type of recurrence model used (term, composition)
    """
    index_reader = IndexReader(project_dir)
    terms = index_reader.get_terms_ordered()
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
    elif model in ('term', 'term-expansion'):
        # Term model
        concept_vectors = util.generate_term_vectors(terms)
        n_dims = len(terms)
        if delta:
            term_vectors = concept_vectors

    # Term mappings & filter terms
    if num_terms:
        filter_terms = set(terms[:num_terms])
    term_mappings = None
    if model == 'term-expansion':
        clusters = index_reader.get_clusters()
        term_mappings = {}
        for cluster_name, cluster_terms in clusters.items():
            for term in cluster_terms:
                term_mappings[term] = cluster_name
        if num_terms:
            filter_terms.update(set(list(filter(lambda t: term_mappings.get(t, t) == t, terms))[:num_terms]))

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
            utterance_concepts = list(filter(lambda t: t in filter_terms, utterance_concepts))
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
                hits = tree.query(embedding, k=5)[1]
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
        # print(recurrence_matrix[57, 108], recurrence_matrix_term[57, 108], recurrence_matrix.shape)
        recurrence_matrix = np.subtract(recurrence_matrix, recurrence_matrix_term)
        # print('delta', recurrence_matrix[57, 108])

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

    return map(lambda ch_key: (':'.join(ch_key), channel_similarity[ch_key], channel_cooccurrence[ch_key]), channel_similarity.keys())
