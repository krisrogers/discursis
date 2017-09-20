"""Processing functions."""
from collections import Counter, namedtuple
import csv
import itertools
import os


import numpy as np
from scipy import spatial
from scipy.spatial import distance
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform
from sklearn import cluster, manifold

from index import IndexReader, IndexWriter, IndexUpdater
import text_util
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


def index_files(project_dir):
    """Index files at `dir`."""
    index_writer = IndexWriter(project_dir)
    for fname in os.listdir(project_dir):
        if not fname.endswith('.csv'):
            continue
        with open(os.path.join(project_dir, fname)) as input_file:
            reader = csv.reader(input_file)

            # Process headers
            channel_id = None
            metadata_index = {}
            headers = [h.lower() for h in next(reader)]
            for i, header in enumerate(headers):
                header = header.strip().lower()
                if header == 'text':
                    text_index = i
                else:
                    field_id = index_writer.add_metadata_field(header)
                    metadata_index[i] = field_id
                    if header in ('channel', 'speaker'):
                        channel_id = field_id

            # Process rows
            for row in reader:
                utterance_metadata = {}
                # TODO: split into smaller utterances?
                for i, cell in enumerate(row):
                    if i == text_index:
                        utterance_text = cell
                    else:
                        utterance_metadata[metadata_index[i]] = cell
                index_writer.add_utterance(
                    utterance_metadata[channel_id], utterance_text, utterance_metadata,
                    Counter(text_util.tokenize(utterance_text))
                )

    index_writer.finish()


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
        for cluster_name, terms in clusters.items():
            for term in terms:
                term_mappings[term] = cluster_name
        if num_terms:
            filter_terms.update(set(list(filter(lambda t: term_mappings.get(t, t) == t, terms))[:num_terms]))

    # Load utterances and calculate embeddings
    utterances = []
    utterance_embeddings = []
    if delta:
        utterance_embeddings_term = []
    for u_data in index_reader.get_utterances(start, limit, include_text):
        utterance_terms = u_data[3].split('::') if u_data[3] else []
        utterance_concepts = utterance_terms
        if term_mappings:
            utterance_concepts = set([term_mappings.get(term, term) for term in utterance_concepts])
        if filter_terms:
            utterance_concepts = list(filter(lambda t: t in filter_terms, utterance_concepts))
        utterances.append({
            'id': u_data[0],
            'channel': u_data[1],
            'length': u_data[2],
            'terms': utterance_terms,  # All terms
            'concepts': utterance_concepts,  # Filtered/mapped
            'text': u_data[4]
        })
        # Calcualte utterance embedding
        utterance_concept_vectors = [
            concept_vectors[term]
            for term in utterance_concepts
        ]
        if len(utterance_concept_vectors):
            if model == 'composition':
                # utterance_embeddings.append(np.mean(utterance_concept_vectors, axis=0))
                if len(utterance_concept_vectors) > 1:
                    utterance_embeddings.append(np.sum(utterance_concept_vectors, axis=0))

                else:
                    utterance_embeddings.append(utterance_concept_vectors[0])
            else:
                utterance_embeddings.append(np.sum(utterance_concept_vectors, axis=0))
        else:
            utterance_embeddings.append(np.zeros(n_dims))
        if delta:
            utterance_term_vectors = [
                term_vectors[term]
                for term in filter(lambda t: not filter_terms or t in filter_terms, utterance_terms)
            ]
            if len(utterance_term_vectors):
                utterance_embeddings_term.append(np.sum(utterance_term_vectors, axis=0))
            else:
                utterance_embeddings_term.append(np.zeros(len(terms)))

    utterance_embeddings = np.array(utterance_embeddings)
    recurrence_matrix = np.nan_to_num((1 - distance.squareform(distance.pdist(utterance_embeddings, metric='cosine'))))
    recurrence_matrix = np.clip(recurrence_matrix, 0, 1)
    if delta:
        utterance_embeddings_term = np.array(utterance_embeddings_term)
        print(utterance_embeddings_term.shape)
        recurrence_matrix_term = np.nan_to_num((1 - distance.squareform(
            distance.pdist(utterance_embeddings_term, metric='cosine')))
        )
        recurrence_matrix_term = np.clip(recurrence_matrix_term, 0, 1)
        # print(recurrence_matrix[57, 108], recurrence_matrix_term[57, 108], recurrence_matrix.shape)
        recurrence_matrix = np.subtract(recurrence_matrix, recurrence_matrix_term)
        # print('delta', recurrence_matrix[57, 108])

    return {
        'utterances': utterances,
        'recurrence_matrix': recurrence_matrix.tolist()
    }


def find_similar_terms(terms, distance_threshold):
    """Return sparse matrix of similar terms within `distance_threshold`."""
    term_vectors = [PP_EMBEDDINGS.get(term, np.zeros(300)) for term in terms]
    vectors = manifold.TSNE().fit_transform(term_vectors)
    tree = spatial.cKDTree(vectors)
    return tree.sparse_distance_matrix(tree, distance_threshold)


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


def generate_model(dir, filter_terms=False, start=0, limit=500):
    """Generate model from index at `dir`."""
    terms, term_vectors, recurrence_matrix = get_recurrence()

    # Cluster
    # terms = terms[:200]
    vectors = (manifold.TSNE(perplexity=10).fit_transform(list(term_vectors.values())))

    import itertools as IT
    import scipy.spatial as spatial
    tree = spatial.cKDTree(vectors)
    cool = set()
    for i, point in enumerate(vectors):
        groups = tree.query_ball_point(point, 0.5)
        if len(groups) > 1:
            cool.add((terms[i] for i in groups))
            print(terms[i], [terms[i] for i in groups])
        # print (terms[i], np.unique(list(IT.chain.from_iterable(groups))))
    cool = list(cool)
    """
    merged_cool = []
    skip_indices = []
    for i, c1 in enumerate(cool):
        c1 = set(c1)
        for j, c2 in enumerate((cool[i + 1:])):
            if j in skip_indices:
                continue
            c2 = set(c2)
            if c1 & c2:
                c1 = c1.update(c2)
                skip_indices.append(j)
            # if [val for val in c1 if val in c2]:
    print()
    for c in cool:
        print(', '.join(c))
    """

    # vectors = (manifold.MDS().fit_transform([term_vectors[t] for t in terms]))
    cluster_labels = cluster.KMeans(n_clusters=25).fit_predict(vectors)
    from collections import defaultdict
    clusters = defaultdict(list)
    for i, label in enumerate(cluster_labels):
        clusters[label].append(terms[i])
    # print(clusters)

    return {
        'recurrence_matrix': recurrence_matrix.tolist(),
        'utterances': utterance_data,
        'terms': terms,
        'term_vectors': vectors.tolist(),
        'cluster_labels': clusters
    }


def generate_model2(texts):
    """..."""
    text_terms = []
    indptr = [0]
    indices = []
    data = []
    vocabulary = {}
    reverse_vocabulary = {}
    for text in texts:
        terms = [t['name'] for t in text['terms'] if t['name'] and t['name'] not in STOPWORDS]
        if BOOLEAN_FREQ:
            terms = list(set(terms))
        text_terms.append(terms)
        for term in terms:
            index = vocabulary.setdefault(term, len(vocabulary))
            reverse_vocabulary[index] = term
            indices.append(index)
            data.append(1)
        indptr.append(len(indices))

    term_doc_frequencies = csr_matrix((data, indices, indptr), dtype=int).toarray().T
    term_frequencies = term_doc_frequencies.sum(axis=1)
    top_terms = {reverse_vocabulary[i]: term_frequencies[i].sum() for i in term_frequencies.argsort()[-NUM_TERMS:]}

    text_embeddings = []
    for i, terms in enumerate(text_terms):
        filtered_terms = [PP_EMBEDDINGS.get(term, np.zeros(300)) for term in terms if term in top_terms]
        if len(filtered_terms):
            text_embeddings.append(
                np.mean(filtered_terms, axis=0)
            )
        else:
            text_embeddings.append(np.zeros(300))
    text_embeddings = np.array(text_embeddings)

    # term_vectors = manifold.TSNE().fit_transform([PP_EMBEDDINGS.get(term, np.zeros(300).tolist()) for term in vocabulary])
    # clusters = cluster.KMeans(n_clusters=100).fit_predict(term_vectors)
    # cluster_map = defaultdict(list)
    # for term_index, cluster_id in enumerate(clusters):
    #     cluster_map[cluster_id].append(reverse_vocabulary[term_index])
    # print(cluster_map)

    recurrence_matrix = np.nan_to_num((1 - distance.squareform(distance.pdist(text_embeddings, metric='cosine'))))

    return {
        'recurrence_matrix': recurrence_matrix.tolist(),
        'terms': [{
            'name': term,
            'frequency': int(freq),
            'vector': PP_EMBEDDINGS.get(term, np.zeros(300).tolist())
        } for term, freq in top_terms.items()]
    }
