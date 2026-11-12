"""Genera artefactos.joblib en local (mismo pipeline que el notebook, secciones 2-4.2)."""
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

from recomendador import Recomendador, Preprocesador, quitar_tildes

KAGGLE_DATASET = "danielalbarracinm/books-with-isbn-of-different-genres"
N_ITEMS, SEMILLA = 2000, 42
NGRAMAS, MIN_DF, MAX_DF = (1, 2), 2, 0.85
MIN_LARGO_DESCRIPCION = 80

CANDIDATAS = {
    "titulo": ["title", "titulo", "book_title", "book", "name", "book_name", "titulo_libro"],
    "autor": ["author", "writer", "escritor", "authors", "autor", "autores", "book_author"],
    "descripcion": ["description", "descripcion", "synopsis", "sinopsis", "summary", "resumen", "plot", "blurb", "about", "overview"],
    "generos": ["genres", "genre", "gender", "genero", "generos", "categories", "category", "categoria", "subjects", "main_genre"],
}


def norm_col(c):
    return re.sub(r"[^a-z0-9]+", "_", quitar_tildes(str(c).lower())).strip("_")


def leer_tabla(ruta):
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(ruta, encoding=enc, sep=None, engine="python", on_bad_lines="skip")
        except UnicodeDecodeError:
            continue
    raise ValueError("No se pudo leer el archivo")


def parse_generos(x):
    if pd.isna(x):
        return []
    return [g.strip().lower() for g in re.split(r"[,;|/\[\]'\"]+", str(x)) if g.strip()]


def detectar_idioma(textos):
    es = {"el", "la", "los", "las", "de", "que", "y", "en", "un", "una", "por", "con", "para", "del", "se"}
    en = {"the", "of", "and", "to", "in", "a", "is", "that", "with", "for", "his", "her", "he", "she"}
    ce = cn = 0
    for t in textos:
        toks = re.findall(r"[a-záéíóúñ]+", t.lower())
        ce += sum(w in es for w in toks)
        cn += sum(w in en for w in toks)
    return "es" if ce > cn else "en"


def main():
    import kagglehub
    carpeta = Path(kagglehub.dataset_download(KAGGLE_DATASET))
    archivo = max((p for p in carpeta.rglob("*.csv")), key=lambda p: p.stat().st_size)
    bruto = leer_tabla(archivo)
    print(f"{archivo.name}: {bruto.shape}")

    por_norm = {norm_col(c): c for c in bruto.columns}
    cols = {k: next((por_norm[n] for n in v if n in por_norm), None) for k, v in CANDIDATAS.items()}
    print("Columnas:", cols)

    df = pd.DataFrame({"titulo": bruto[cols["titulo"]].astype(str).str.strip()})
    df["autor"] = bruto[cols["autor"]].astype(str).str.strip() if cols["autor"] else ""
    df["descripcion"] = bruto[cols["descripcion"]].fillna("").astype(str).str.strip()
    df["generos_raw"] = bruto[cols["generos"]] if cols["generos"] else np.nan

    df = df[df["titulo"].str.len() > 0]
    df = df[df["descripcion"].str.len() >= MIN_LARGO_DESCRIPCION]
    df["_clave"] = df["titulo"].map(lambda s: re.sub(r"\W+", " ", quitar_tildes(s.lower())).strip())
    df = df.drop_duplicates("_clave").drop(columns="_clave")
    if len(df) > N_ITEMS:
        df = df.sample(N_ITEMS, random_state=SEMILLA)
    df = df.reset_index(drop=True)
    df.insert(0, "id", df.index)
    df["generos_lista"] = df["generos_raw"].map(parse_generos)
    df["generos"] = df["generos_lista"].map(lambda g: ", ".join(g[:6]))

    idioma = detectar_idioma(df["descripcion"].head(300))
    print("Idioma:", idioma)
    pre = Preprocesador(idioma, bilingue=True)
    df["texto_original"] = df["titulo"].str.cat([df["descripcion"]], sep=". ")
    t0 = time.time()
    df["texto_limpio"] = pre.transformar(df["texto_original"].tolist(), batch_size=64)
    print(f"Preprocesado en {time.time() - t0:.0f} s")
    df = df[df["texto_limpio"].str.len() > 0].reset_index(drop=True)
    df["id"] = df.index

    rec = Recomendador(idioma, NGRAMAS, MIN_DF, MAX_DF, bilingue=True).fit(df)
    print(f"TF-IDF: {rec.X.shape[0]:,} libros x {rec.X.shape[1]:,} términos")
    rec.guardar("artefactos.joblib")
    print("Guardado artefactos.joblib")


if __name__ == "__main__":
    main()

