# coding: utf-8
"""Modulo para variables y funciones de uso comun."""
from pathlib import Path
import logging

from gensim.corpora import Dictionary
from gensim.models import Phrases
from gensim.models.phrases import Phraser
from unidecode import unidecode
import pandas as pd
import spacy


def change_filename(filepath):
    """
    Elimina caracteres no ascii en nombre de archivo en filepath.

    Parameters
    ----------
    filepath: str or Path

    Returns
    -------
    Path
    """
    fp = Path(filepath)
    dirpath = fp.parent
    filename = fp.name

    if not all(ord(char) < 128 for char in filename):
        deconame = unidecode(filename)
        newpath = Path(dirpath, deconame)
        fp.rename(newpath)

    return newpath


def ordered_filepaths(directory):
    """
    Parameters
    ----------
    directory: str or Path

    Yields
    ------
    Path
        Itera sobre cada documento en directory, devolviendo filepath del archivo.
    """
    cpath = Path(directory)
    filepaths = sorted(cpath.glob('*.txt'))
    for fpath in filepaths:
        yield fpath


def get_docnames(directory):
    """
    Parameters
    ----------
    directory: str or Path

    Returns
    -------
    list of str
        Itera sobre cada documento en directory, devolviendo nombre del archivo.
    """

    return [fpath.stem for fpath in ordered_filepaths(directory)]


def read_text(filepath):
    """
    Lee texto de archivo en filepath.

    Parameters
    ----------
    filepath: str or Path

    Returns
    -------
    str
       Texto de archivo en filepath
    """
    try:
        with open(filepath, encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        logging.info(f'Error leyendo {filepath}: {e}')
        text = ''

    return text


def load_stopwords(filepath, sheet, col='word'):
    """
    Lee lista de palabras a usar como stopwords.
    Ubicadas en columna col de la hoja sheet del archivo Excel en filepath.

    Parameters
    ----------
    filepath: str or Path
    sheet: str
    col: str

    Returns
    -------
    set
       Stopwords
    """
    df = pd.read_excel(filepath, sheet_name=sheet)

    return set(df[col])


def process_tokens(container, other=None):
    """
    Procesa tokens del container, filtrando según criterios en other.

    Parameters
    ----------
    container: spacy.tokens.Doc | spacy.tokens.Span
    other: dict, optional (stopwords, postags, entities, stemmer)

    Returns
    -------
    list of str
    """
    tokens = (tok for tok in container if tok.is_alpha)

    if other:
        if 'stopwords' in other:
            tokens = (
                tok for tok in tokens if tok.lower_ not in other['stopwords'])
        if 'postags' in other:
            tokens = (tok for tok in tokens if tok.pos_ in other['postags'])
        if 'entities' in other:
            tokens = (
                tok for tok in tokens if tok.ent_type_ not in other['entities'])

    wordlist = [tok.lower_ for tok in tokens]
    if other and 'stemmer' in other:
        wordlist = [other['stemmer'].stem(w) for w in wordlist]

    return wordlist


def doc_sentences(document, other=None):
    """
    Itera sobre cada frase de document filtrando según criterios en other.

    Parameters
    ----------
    document: spacy.tokens.Doc
    other: dict, optional (stopwords, postags, entities, stemmer)

    Yields
    ------
    list of str
    """
    for sent in document.sents:
        yield process_tokens(sent, other)


def model_ngrams(sentences):
    """
    Crea modelos Phraser a partir de frase iterables en sentences,
    para identificar ngramas recurrentes.

    Parameters
    ----------
    sentences: iterable of list of str

    Returns
    -------
    dict
        Modelos Phraser para bigramas y trigramas
    """
    big = Phrases(sentences, min_count=5, threshold=10)
    model_big = Phraser(big)

    trig = Phrases(model_big[sentences], min_count=5, threshold=10)
    model_trig = Phraser(trig)

    return dict(bigrams=model_big, trigrams=model_trig)


def iter_sentences(directory, lang, other=None):
    """
    Itera sobre cada documento en directory,
    devolviendo palabras de cada frase de cada documento,
    filtrando según criterios en other.

    Parameters
    ----------
    directory: str
    lang: spacy.lang
    other: dict, optional (stopwords, postags, entities, stemmer)

    Yields
    ------
    list of str
    """
    for fpath in ordered_filepaths(directory):
        text = read_text(fpath)
        doc = lang(text)

        yield from doc_sentences(doc, other)


def iter_documents(ngrams, directory, lang, other=None):
    """
    Itera sobre cada documento en directory,
    devolviendo lista de palabras de cada documento,
    filtrando según criterios en other.
    Listas de palabras pasan por modelos en ngrams.

    Parameters
    ----------
    ngrams: dict (bigrams, trigrams)
    directory: str
    lang: spacy.lang
    other: dict, optional (stopwords, postags, entities, stemmer)

    Yields
    ------
    list of str
    """
    bigrams = ngrams['bigrams']
    trigrams = ngrams['trigrams']

    for fpath in ordered_filepaths(directory):
        text = read_text(fpath)
        doc = lang(text)

        words = []
        for tokens in doc_sentences(doc, other):
            words.extend(trigrams[bigrams[tokens]])

        yield words


class MiCorpus:
    """
    Iterable: en cada iteración devuelve vectores bag-of-words, uno por documento.
    Procesa un documento a la vez usando generators. Nunca carga todo el corpus a RAM.
    """

    def __init__(self, directorio, lenguaje, otros=None):
        self.directorio = directorio
        self.lenguaje = lenguaje
        self.otros = otros

        self.ngramas = model_ngrams(iter_sentences(
            self.directorio, self.lenguaje, self.otros))

        self.diccionario = Dictionary(iter_documents(
            self.ngramas, self.directorio, self.lenguaje, self.otros))
        self.diccionario.filter_extremes(no_above=0.8)
        self.diccionario.filter_tokens(
            bad_ids=(tokid for tokid, freq in self.diccionario.dfs.items() if freq == 1))
        self.diccionario.compactify()

    def __iter__(self):
        """
        CorpusConsultivos es un streamed iterable.
        """
        for tokens in iter_documents(self.ngramas, self.directorio, self.lenguaje, self.otros):
            yield self.diccionario.doc2bow(tokens)
