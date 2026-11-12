import streamlit as st

from recomendador import Recomendador

st.set_page_config(page_title="Recomendador de libros", page_icon="📚", layout="wide")


@st.cache_resource
def cargar():
    return Recomendador.cargar("artefactos.joblib")


rec = cargar()
st.title("📚 Recomendador de libros")
st.caption(f"TF-IDF + similitud coseno · {rec.X.shape[0]:,} libros · {rec.X.shape[1]:,} términos")

n = st.sidebar.slider("Cantidad de recomendaciones", 1, 10, 5)
modo = st.sidebar.radio("Buscar por", ["Libro parecido a…", "Descripción libre"])

if modo == "Libro parecido a…":
    q = st.text_input("Parte del título")
    if q:
        res = rec.buscar_titulo(q, 30)
        if res.empty:
            st.warning("Sin coincidencias.")
        else:
            opciones = {f"{r.titulo} — {r.autor}": int(r.id) for r in res.itertuples()}
            elegido = st.selectbox("Elige el libro", list(opciones))
            idx = opciones[elegido]
            st.write(rec.df.loc[idx, "descripcion"][:500])
            out = rec.recomendar(idx, n)
            st.subheader("Recomendaciones")
            st.dataframe(out, width="stretch", hide_index=True)
            st.bar_chart(out.set_index("titulo")["score"])
else:
    texto = st.text_area("Describe qué quieres leer")
    if texto.strip():
        out = rec.recomendar_texto(texto, n)
        if out.empty:
            st.warning("Ninguna palabra de tu descripción está en el vocabulario del catálogo.")
        else:
            st.dataframe(out, width="stretch", hide_index=True)
            st.bar_chart(out.set_index("titulo")["score"])