"""Recomendador de contenido: preprocesamiento + TF-IDF + similitud coseno."""
import re
import unicodedata

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

MODELOS_SPACY = {"es": "es_core_news_sm", "en": "en_core_web_sm"}
MAX_CHARS = 1500  # recorta sinopsis larguísimas para acelerar spaCy


def quitar_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c))


def normalizar_titulo(s):
    return re.sub(r"\W+", " ", quitar_tildes(str(s).lower())).strip()


RE_ROTAS = re.compile(r"\w*#\w*")  # palabras con caracteres mal codificados (p. ej. "Amar#s")


def stopwords_spacy(idioma):
    if idioma == "es":
        from spacy.lang.es.stop_words import STOP_WORDS
    else:
        from spacy.lang.en.stop_words import STOP_WORDS
    return {quitar_tildes(w.lower()) for w in STOP_WORDS}


class Preprocesador:
    """minúsculas + sin tildes + sin stopwords + lematización (spaCy)."""

    def __init__(self, idioma="es", bilingue=True):
        self.idioma = idioma
        self.bilingue = bilingue
        self._nlp = None
        self._stop = None

    @property
    def nlp(self):
        if self._nlp is None:
            import spacy
            nombre = MODELOS_SPACY[self.idioma]
            try:
                self._nlp = spacy.load(nombre, disable=["parser", "ner"])
            except OSError as e:
                raise RuntimeError(f"Falta el modelo: python -m spacy download {nombre}") from e
            self._stop = {quitar_tildes(w.lower()) for w in self._nlp.Defaults.stop_words}
            if self.bilingue:
                for otro in MODELOS_SPACY:
                    self._stop |= stopwords_spacy(otro)
        return self._nlp

    def transformar(self, textos, batch_size=64, n_process=1):
        nlp = self.nlp
        salida = []
        flujo = (RE_ROTAS.sub(" ", str(t)[:MAX_CHARS]) for t in textos)
        for doc in nlp.pipe(flujo, batch_size=batch_size, n_process=n_process):
            toks = []
            for t in doc:
                if not t.is_alpha or t.is_stop:
                    continue
                lema = quitar_tildes(t.lemma_.lower())
                if len(lema) > 2 and lema not in self._stop and quitar_tildes(t.lower_) not in self._stop:
                    toks.append(lema)
            salida.append(" ".join(toks))
        return salida


class Recomendador:
    def __init__(self, idioma="es", ngram_range=(1, 2), min_df=2, max_df=0.85, bilingue=True):
        self.idioma = idioma
        self.bilingue = bilingue
        self.params = dict(ngram_range=tuple(ngram_range), min_df=min_df, max_df=max_df)
        self.pre = Preprocesador(idioma, bilingue)
        self.vec = None
        self.X = None
        self.df = None

    # ------------------------------------------------------------ entrenamiento
    def fit(self, df, col_limpio="texto_limpio", col_titulo="titulo"):
        self.df = df.reset_index(drop=True).copy()
        self.vec = TfidfVectorizer(
            ngram_range=self.params["ngram_range"],
            min_df=self.params["min_df"],
            max_df=self.params["max_df"],
            sublinear_tf=True,
            norm="l2",
        )
        self.X = self.vec.fit_transform(self.df[col_limpio].fillna(""))
        self.terminos = self.vec.get_feature_names_out()
        self.titulo_norm = self.df[col_titulo].map(normalizar_titulo).values
        return self

    # ------------------------------------------------------------ consulta por ítem
    def indices_similares(self, idx, n=5):
        """Top-N por similitud coseno. TF-IDF ya viene normalizado (L2), así que el coseno es el producto punto."""
        sims = linear_kernel(self.X[idx], self.X).ravel()
        sims[self.titulo_norm == self.titulo_norm[idx]] = -1.0  # excluye el propio libro y otras ediciones
        n = min(n, len(sims) - 1)
        top = np.argpartition(-sims, n - 1)[:n]
        top = top[np.argsort(-sims[top])]
        return top, sims[top]

    def terminos_comunes(self, i, j, k=5):
        prod = self.X[i].multiply(self.X[j]).tocoo()
        if prod.nnz == 0:
            return []
        orden = np.argsort(-prod.data)[:k]
        return [str(self.terminos[prod.col[o]]) for o in orden]

    def _tabla(self, idxs, scores, comunes):
        d = self.df
        filas = []
        for pos, (j, s) in enumerate(zip(idxs, scores)):
            filas.append({
                "id": int(d.loc[j, "id"]),
                "titulo": d.loc[j, "titulo"],
                "autor": d.loc[j, "autor"] if "autor" in d else "",
                "generos": d.loc[j, "generos"] if "generos" in d else "",
                "score": round(float(s), 4),
                "terminos_comunes": comunes[pos],
            })
        return pd.DataFrame(filas)

    def recomendar(self, idx, n=5):
        top, sc = self.indices_similares(idx, n)
        return self._tabla(top, sc, [self.terminos_comunes(idx, j) for j in top])

    # ------------------------------------------------------------ consulta por texto libre
    def recomendar_texto(self, texto, n=5):
        limpio = self.pre.transformar([texto])[0]
        q = self.vec.transform([limpio])
        if q.nnz == 0:
            return pd.DataFrame(columns=["id", "titulo", "autor", "generos", "score", "terminos_comunes"])
        sims = linear_kernel(q, self.X).ravel()
        n = min(n, len(sims))
        top = np.argpartition(-sims, n - 1)[:n]
        top = top[np.argsort(-sims[top])]
        comunes = []
        for j in top:
            prod = q.multiply(self.X[j]).tocoo()
            orden = np.argsort(-prod.data)[:5] if prod.nnz else []
            comunes.append([str(self.terminos[prod.col[o]]) for o in orden])
        return self._tabla(top, sims[top], comunes)

    def buscar_titulo(self, texto, limite=10):
        q = normalizar_titulo(texto)
        if not q:
            return self.df.iloc[0:0][["id", "titulo", "autor"]]
        mask = pd.Series(self.titulo_norm).str.contains(re.escape(q), regex=True).values
        return self.df.loc[mask, ["id", "titulo", "autor"]].head(limite)

    # ------------------------------------------------------------ persistencia
    def guardar(self, ruta):
        joblib.dump({"idioma": self.idioma, "bilingue": self.bilingue, "params": self.params, "vec": self.vec,
                     "X": self.X, "df": self.df}, ruta, compress=3)

    @classmethod
    def cargar(cls, ruta):
        d = joblib.load(ruta)
        r = cls(d["idioma"], bilingue=d.get("bilingue", True), **d["params"])
        r.vec, r.X, r.df = d["vec"], d["X"], d["df"]
        r.terminos = r.vec.get_feature_names_out()
        r.titulo_norm = r.df["titulo"].map(normalizar_titulo).values
        return r
    