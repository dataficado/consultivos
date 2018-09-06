# Análisis de Comités Consultivos
Explora la posibilidad de aprender tópicos de las ayudas de memoria de los comités.

## Contenido
- extraction.py
    - Se usa para extraer el texto de archivos pdf y word usando TIKA.
    - Crea una carpeta *corpus* en el directorio donde están los documentos originales, almacenando el texto de cada documento en un archivo txt.
    - Crea, si no existe, *procesados.csv* donde se incluye metadata de cada documento al que se le realize extracción. Si ya existe se actualiza con nuevas filas.

    **Modo de uso**:

    python extraction.py <path/to/original/docs/>

- helpers.py
    - Contiene funciones, variables y clases comunes que pueden ser usadas en diferentes archivos.
    - Otros archivos la llaman con

        *import helpers as hp*

- notebooks exploratorios
