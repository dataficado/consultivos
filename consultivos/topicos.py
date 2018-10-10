# coding: utf-8
"""Modulo para determinar tópicos usados en corpus."""
from pathlib import Path
import datetime
import logging
import os
import time
import warnings

from gensim.models import CoherenceModel
from gensim.models.ldamodel import LdaModel
from plotly import tools
import pandas as pd
import plotly.offline as pyo
import plotly.graph_objs as go
import pyLDAvis
import pyLDAvis.gensim
import spacy

from helpers import MiCorpus
import helpers as hp


def create_models(corpus, topics, params, ngrams, directory, lang, other=None):
    """
    Crea modelos LDA para diferentes números de tópicos

    Parameters
    ----------
    corpus: MiCorpus
    topics: iterable con el # de tópicos
    params: dict con parámetros requeridos en modelo
    ngrams: dict (bigrams, trigrams)
    directory: str
    lang: spacy.lang
    other: dict, optional (stopwords, postags, entities, stemmer)

    Returns
    -------
    dict of str
        Dict con resultados de modelos LDA
    """
    models = {}

    for i in topics:
        result = {}
        id2word = corpus.diccionario
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            lda = LdaModel(corpus, num_topics=i, id2word=id2word, **params)

        texts = list(hp.iter_documents(ngrams, directory, lang, other))
        cm = CoherenceModel(model=lda, texts=texts, dictionary=id2word, coherence='c_v')
        coherence = cm.get_coherence()

        result['lda'] = lda
        result['coherence'] = coherence

        models[i] = result

    return models


if __name__ == '__main__':
    nlp = spacy.load('es_md')

    dirdocs = '/Users/tombito/Dropbox/datasets/banrep/consultivos/ciiu/'
    dircorpus = os.path.join(dirdocs, 'corpus')

    rundate = f'{datetime.date.today():%Y-%m-%d}'
    dirdate = Path(rundate)
    dirmodels = dirdate.joinpath('modelos', Path(dirdocs).name)
    dirtopics = dirdate.joinpath('topicos', Path(dirdocs).name)
    os.makedirs(dirmodels, exist_ok=True)
    os.makedirs(dirtopics, exist_ok=True)

    logfile = os.path.join(dirtopics, f'{rundate}.log')
    log_format = '%(asctime)s : %(levelname)s : %(message)s'
    log_datefmt = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(format=log_format, datefmt=log_datefmt,
                        level=logging.INFO, filename=logfile, filemode='w')

    pathstops = '/Users/tombito/Dropbox/datasets/wordlists/stopwords.xlsx'
    stops = hp.load_stopwords(pathstops, 'spanish', col='word')
    tags = ['NOUN', 'VERB', 'ADJ', 'ADV', 'ADP','AUX', 'DET', 'PRON']
    ents = ['PER', 'ORG']
    extra = dict(stopwords=stops, postags=tags, entities=ents, )
    # opcional stemmer=SnowballStemmer('spanish')
    # habiendo importado from nltk.stem import SnowballStemmer

    start = time.time()

    # Creacion de corpus, diccionario y modelos n-gramas
    consultivos = MiCorpus(dircorpus, nlp, extra)
    diccionario = consultivos.diccionario
    diccionario.save(os.path.join(dirmodels, 'consultivos.dict'))

    ngramas = consultivos.ngramas
    bigramas = ngramas['bigrams']
    bigramas.save(os.path.join(dirmodels, 'bigramas'))
    trigramas = ngramas['trigrams']
    trigramas.save(os.path.join(dirmodels, 'trigramas'))

    logging.info('Corpus, diccionario y modelos n-gramas generados')

    # Creación de modelos LDA y selección del mejor por Coherence
    n = (20, 30, 40, 50, 60)
    lda_params = dict(chunksize=100, passes=2, alpha='auto', eta='auto', random_state=100)
    modelos = create_models(consultivos, n, lda_params, ngramas, dircorpus, nlp, extra)

    logging.info(f'Modelos LDA generados para n={n}')

    # if several indexes with max score, choose first
    scores = [modelos[i]['coherence'] for i in n]
    best_is = [i for i, j in enumerate(scores) if j == max(scores)][0]
    best = n[best_is]
    logging.info(f'Mejor número de tópicos según Coherence: {best}')

    # generar gráfica del Coherence Score
    colors = ['rgba(204,204,204,1)' if not i==best else 'rgba(222,45,38,0.8)' for i in n]

    trace = go.Bar(x=n, y=scores, marker=dict(color=colors))
    layout = dict(title='Coherence Score para cada número de tópicos',
                xaxis=dict(title='Número de tópicos'),
                yaxis=dict(title='Coherence Score (c_v)', hoverformat='.3f'))

    fig = dict(data=[trace], layout=layout)
    filename = os.path.join(dirtopics, 'coherence.html')
    cohfile = pyo.plot(fig, show_link=False, filename=filename, auto_open=False)

    # Guardar mejor modelo. Para guardar otro habría que seleccionar otro n
    ldamodel = modelos[best]['lda']
    ldamodel.save(os.path.join(dirtopics, 'topicos-{:0>2}.lda'.format(best)))

    # Generar cuadro de probabilidad de topicos para cada documento.
    doctopics = pd.DataFrame(data=(dict(d) for d in ldamodel[consultivos]),
                            index=hp.get_docnames(dircorpus))
    doctopics['dominante'] = doctopics.idxmax(axis=1)
    doctopics.to_csv(dirtopics.joinpath(f'doctopics-{best:0>2}.csv'),
                    index_label='identifiers', encoding='utf-8')

    # Gráfica LDAvis de tópicos y sus palabras
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        vis = pyLDAvis.gensim.prepare(ldamodel, list(consultivos), diccionario, sort_topics=False)

    pyLDAvis.save_html(vis, os.path.join(dirtopics, 'topicos-{:0>2}.html'.format(best)))

    # Determinar en cuantos documentos es dominante cada tópico.
    topic_counts = doctopics['dominante'].value_counts()
    dominance = round(topic_counts/topic_counts.sum(), 4)
    dominance.to_csv(dirtopics.joinpath(f'dominance-{best:0>2}.csv'),
                    header=True, index_label='topico', encoding='utf-8')

    # Grafica de palabras de principales tópicos
    # (aquellos con mayor participación dominante)
    rows = 5
    cols = 2
    head_topics = dominance.head(rows*cols)

    fig = tools.make_subplots(rows=rows, cols=cols,
                            subplot_titles=(['Tópico {}'.format(t) for t in head_topics.index]),
                            print_grid=False,
                            )

    r = 1
    for i, t in enumerate(head_topics.index, 1):
        dfg=pd.DataFrame(ldamodel.show_topic(t, 15), columns=['term','prob']).set_index('term')
        dfg.sort_values(by='prob', inplace=True)

        trace = go.Bar(x=dfg['prob'], y=dfg.index, orientation='h',)

        if i%2==0:
            fig.add_trace(trace, row=r, col=2)
            r+=1
        else:
            fig.add_trace(trace, row=r, col=1)

    fig.layout.update(title='Principales palabras de tópicos más dominantes',
                    showlegend=False, yaxis=dict(automargin=True),
                    height=2000, width=1200)

    f = os.path.join(dirtopics, 'topicwords-{:0>2}.html'.format(best))
    headfile = pyo.plot(fig, show_link=False, filename=f, auto_open=False)

    finish = time.time()
    logging.info(f'{(finish - start) / 60} minutos')
