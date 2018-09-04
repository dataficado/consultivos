# coding: utf-8
"""Modulo para extraer texto de archivos binarios."""
from pathlib import Path
import csv
import os
import sys
import time
import warnings

from tika import unpack
from tika import language


def extract(filepath):
    """
    De un archivo en filepath, extraer contenido, metadata e idioma.

    Parameters
    ----------
    filepath: str

    Returns
    -------
    dict ('contenido'(str), 'metadata'(dict), 'idioma'(str))
    """
    parsed = unpack.from_file(filepath)
    text = parsed.get('content')
    lang = language.from_buffer(text)
    metadata = parsed.get('metadata')
    info = dict(text=text, metadata=metadata, lang=lang)

    return info


def get_metavalue(meta, keys):
    """
    Saca valor de un diccionario según posibles keys presentes.

    Parameters
    ----------
    meta: dict
    keys: tuple

    Returns
    -------
    str
    """
    assert type(keys) is tuple

    first, second, third = keys
    val = meta.get(first) if first in meta else meta.get(second)
    if not val:
        val = meta.get(third)

    return val


def append_to_processed(filepath, data):
    """
    Incluye data como nueva fila en filepath.

    Parameters
    ----------
    filepath: str
    data: tuple
    """
    assert type(data) is tuple

    with open(filepath, 'a', newline='', encoding='utf-8') as out:
        writer = csv.writer(out, delimiter=',')
        writer.writerow(data)


if __name__ == '__main__':
    inicio = time.time()
    dir_input = sys.argv[1]
    dir_output = os.path.join(dir_input, 'corpus')
    os.makedirs(dir_output, exist_ok=True)

    formatos = ('.pdf', '.doc', '.docx')
    kpgs = ('xmpTPg:NPages', 'meta:page-count', 'Page-Count')
    kcdt = ('Creation-Date', 'meta:creation-date', 'date')
    procfile = os.path.join(dir_output, 'procesados.csv')
    bien = 0
    mal = 0

    path_input = Path(dir_input)
    for f in path_input.iterdir():
        if f.suffix.lower() in formatos:
            outname = f'{f.stem}.txt'
            outfile = os.path.join(dir_output, outname)
            if not os.path.isfile(outfile):
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=RuntimeWarning)
                        info = extract(filepath=str(f))

                except Exception as e:
                    info = {}
                    logstr = 'TIKA {}:{}'.format(f, e)
                    print(logstr)

                texto = info.get('text') if info else ''
                idioma = info.get('lang') if info else ''
                meta = info.get('metadata') if info else {}
                paginas = get_metavalue(meta, kpgs) if meta else ''
                fecha = get_metavalue(meta, kcdt) if meta else ''

                if texto:
                    bien += 1
                    with open(outfile, "w", encoding='utf-8') as out:
                        out.write(texto)

                    datos = (outname, fecha, idioma, paginas)
                    append_to_processed(procfile, datos)

                else:
                    mal += 1

    fin = time.time()
    secs = fin - inicio

    logstr = '{:.2f} mins, {} bien y {} mal'.format(secs / 60, bien, mal)
    print(logstr)
