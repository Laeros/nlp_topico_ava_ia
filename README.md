# nlp_topico_ia — Recomendador de libros por contenido

Recomendador de libros **basado en contenido**. Representa cada libro con **TF-IDF** a partir de su título y sinopsis, y recomienda los más parecidos con **similitud coseno**. Incluye una API REST (FastAPI), un panel interactivo en el notebook y una aplicación web (Streamlit).

Proyecto del curso *NLP desde cero · Semana 1 · Proyecto 5: Recomendador de contenido*.

## Contenido del repositorio

| Archivo | Qué es |
|---|---|
| `recomendador_libros.ipynb` | Notebook principal (Google Colab): datos, preprocesamiento, modelo, evaluación, API y app |
| `recomendador.py` | Módulo reutilizable: preprocesamiento + TF-IDF + coseno + guardado/carga |
| `api.py` | API FastAPI con el endpoint `/recomendar` |
| `app_streamlit.py` | Aplicación web Streamlit |
| `requirements.txt` | Dependencias |

`recomendador.py`, `api.py` y `app_streamlit.py` también los genera el notebook.

## Cómo ejecutarlo

**En Google Colab:** abre `recomendador_libros.ipynb` y usa *Entorno de ejecución → Ejecutar todo*. Las opciones se cambian en la celda **CONFIGURACIÓN**.

**En local:**

```bash
pip install -r requirements.txt
python -m spacy download es_core_news_sm
python -m spacy download en_core_web_sm
jupyter notebook recomendador_libros.ipynb   # genera artefactos.joblib

uvicorn api:app --reload                     # API en http://127.0.0.1:8000/docs
streamlit run app_streamlit.py               # aplicación web
```

La API y la app necesitan `artefactos.joblib`. Ese archivo lo crea el notebook (sección 4.2) y no se sube al repositorio.

## Flujo del proyecto

1. **Datos.** Dataset de Kaggle [*Books with ISBN of different genres*](https://www.kaggle.com/datasets/danielalbarracinm/books-with-isbn-of-different-genres): unos 31 000 libros con título, sinopsis, género (`gender`) y autor (`writer`). Se quitan duplicados y sinopsis cortas, y se toma una muestra de 2000 libros.
2. **Preprocesamiento** (spaCy):
   - se descartan las palabras con caracteres dañados (`#`);
   - lematización, minúsculas y eliminación de tildes;
   - se quitan las stopwords en **español e inglés**, porque el catálogo mezcla los dos idiomas.
3. **Modelo.** `TfidfVectorizer` con 1-2 gramas, `sublinear_tf=True`, `min_df=2` (justificado con una tabla) y `max_df=0.85`. Se recomienda el top-N por similitud coseno. Cada recomendación incluye los **términos en común** que la explican.
4. **Evaluación:**
   - métrica automática por géneros (Precision@K y nDCG@K) comparada contra recomendaciones al azar;
   - encuesta a ciegas para personas reales (opcional en la demo).
5. **Servicio.** API FastAPI y aplicación Streamlit.
6. **Extra.** Comparación con *embeddings* (`paraphrase-multilingual-MiniLM-L12-v2`) para mostrar el límite de TF-IDF con los sinónimos.

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Estado y tamaño del catálogo |
| GET | `/items?q=texto&limite=10` | Buscar libros por título para obtener su `id` |
| GET | `/recomendar?item_id=12&n=5` | Libros parecidos a uno dado |
| GET | `/recomendar_texto?texto=...&n=5` | Libros para una descripción en texto libre |

## Limitaciones

- TF-IDF compara palabras exactas (ya lematizadas): no entiende sinónimos ni contexto.
- La métrica por géneros mide cercanía de género, no si al lector le gustaría el libro.
- La lematización usa un solo modelo de spaCy (español), así que las sinopsis en inglés se lematizan peor.
