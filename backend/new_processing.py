"""Document processing and modelling."""
import csv

import spacy


def process_csv_file(csv_file, text_col='text', lang='en'):
    """Process specified `csv_file`."""
    nlp = spacy.load(lang)

    # Process headers
    reader = csv.reader(csv_file)
    headers = [h.lower() for h in next(reader)]
    text_index = headers.index(text_col)

    # Process content
    for row in reader:
        print(row[text_index])
