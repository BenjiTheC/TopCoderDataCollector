""" Some NLP operations that compare the string with same section name.
    Functions/classes in this file should ONLY take care of processing text,
    i.e. the text should be passed in as input arguments. DB querying should be
    out of the scope for this file.
"""
import typing
from collections.abc import Sequence
from gensim import corpora, utils, models
from gensim.similarities import SparseMatrixSimilarity
from gensim.parsing.preprocessing import STOPWORDS as GENSIM_STOPWORDS


STOPWORDS = GENSIM_STOPWORDS - {'computer'}


def tokenize(s: str) -> list[str]:
    """ Preprocess documents into list of word tokens and remove the stopwords."""
    return [w for w in utils.simple_preprocess(s, max_len=20) if w not in STOPWORDS]


# TODO: build tfidf model for each section group. calculate the average similarity.
def section_text_similarity(corpus: Sequence[str]):
    """ Convert text bundle into tfidf vectors."""
    # Use generator to increase memory efficiency
    def tokenized_corpus() -> typing.Generator[list[str], None, None]:
        yield from (tokenize(doc) for doc in corpus)

    def bag_of_words_corpus(dct: corpora.Dictionary) -> typing.Generator[list[tuple[int, int]], None, None]:
        yield from (dct.doc2bow(doc) for doc in corpus)

    word_id_map = corpora.Dictionary(tokenized_corpus())
    tfidf = models.TfidfModel(bag_of_words_corpus(word_id_map), dictionary=word_id_map)

    similarity_index = SparseMatrixSimilarity(tfidf[bag_of_words_corpus(word_id_map)], num_features=len(word_id_map))
    pairwise_similarity = [simi for idx, similarities in enumerate(similarity_index) for simi in similarities[idx + 1:]]
    return sum(pairwise_similarity) / len(pairwise_similarity)
