import html
import random

import streamlit as st

from recomendador import Recomendador

st.set_page_config(page_title="Recomendador de libros", page_icon="📚", layout="wide",
                   initial_sidebar_state="expanded")

# ------------------------------------------------------------------ estilos
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="st-"] {font-family: 'Inter', sans-serif;}
.block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px;}
.hero {background: linear-gradient(135deg, #2b2140 0%, #4a2f5e 55%, #8a4b5c 100%); color: #fff;
border-radius: 20px; padding: 2.2rem 2.4rem; margin-bottom: 1.4rem; box-shadow: 0 10px 30px rgba(43,33,64,.18);}
.hero-eyebrow {text-transform: uppercase; letter-spacing: .14em; font-size: .72rem; opacity: .75;}
.hero-title {font-family: 'Fraunces', serif; font-size: 2.6rem; font-weight: 700; line-height: 1.1; margin: .4rem 0 .6rem;}
.hero p {opacity: .85; max-width: 640px; margin: 0; font-size: 1rem;}
.stats {display: flex; gap: .75rem; margin-top: 1.4rem; flex-wrap: wrap;}
.stat {background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.2); border-radius: 12px; padding: .55rem 1rem;}
.stat b {font-size: 1.15rem; display: block;}
.stat span {font-size: .74rem; opacity: .8;}
.grid {display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; margin: .4rem 0 1rem;}
.card {background: #fff; border: 1px solid #ece6df; border-radius: 16px; padding: 1.1rem 1.2rem;
box-shadow: 0 1px 2px rgba(40,30,20,.04), 0 4px 14px rgba(40,30,20,.05);
transition: transform .15s ease, box-shadow .15s ease; display: flex; flex-direction: column; gap: .65rem;}
.card:hover {transform: translateY(-2px); box-shadow: 0 2px 4px rgba(40,30,20,.06), 0 10px 24px rgba(40,30,20,.09);}
.card-top {display: flex; gap: .8rem; align-items: flex-start;}
.rank {flex: none; width: 2rem; height: 2rem; border-radius: 10px; background: #f3ebf7; color: #5b3a73;
font-weight: 700; display: grid; place-items: center; font-size: .9rem;}
.card-title {font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.08rem; color: #231b2e; line-height: 1.25;}
.card-author {color: #7a6f80; font-size: .85rem; margin-top: .15rem;}
.chip, .term {display: inline-block; border-radius: 999px; padding: .15rem .6rem; font-size: .72rem; margin: 0 .3rem .3rem 0;}
.chip {background: #f6f1ea; color: #6b5a48;}
.term {background: #eaf4f0; color: #2f6b5a; font-weight: 500;}
.synopsis {color: #4d4552; font-size: .88rem; line-height: 1.55; margin: 0;}
.score-row {display: flex; align-items: center; gap: .6rem;}
.bar {flex: 1; height: 6px; background: #f1ecf3; border-radius: 999px; overflow: hidden;}
.bar > div {height: 100%; background: linear-gradient(90deg, #8a4b5c, #5b3a73); border-radius: 999px;}
.score {font-variant-numeric: tabular-nums; font-size: .8rem; color: #5b3a73; font-weight: 600;}
.label {font-size: .68rem; color: #9a8fa0; text-transform: uppercase; letter-spacing: .07em; margin-right: .35rem;}
.featured {background: #fffaf5; border: 1px solid #efe2d6; border-left: 5px solid #8a4b5c; border-radius: 16px;
padding: 1.3rem 1.5rem; margin: .8rem 0 .4rem;}
.featured .card-title {font-size: 1.45rem;}
.featured .synopsis {font-size: .95rem; margin-top: .6rem;}
.section-title {font-family: 'Fraunces', serif; font-size: 1.4rem; font-weight: 600; margin: 1.6rem 0 .2rem; color: #231b2e;}
.section-sub {color: #8a7f90; font-size: .88rem; margin-bottom: .6rem;}
.empty {text-align: center; padding: 2.6rem 1rem; color: #8a7f90; border: 1.5px dashed #e3dbe6; border-radius: 16px;
background: #fffdfb; margin-top: .8rem;}
.empty .big {font-size: 2.2rem; margin-bottom: .4rem;}
.side-title {font-family: 'Fraunces', serif; font-size: 1.3rem; font-weight: 700; color: #2b2140;}
.step {display: flex; gap: .6rem; margin: .55rem 0; font-size: .85rem; color: #4d4552;}
.step b {flex: none; width: 1.4rem; height: 1.4rem; border-radius: 50%; background: #8a4b5c; color: #fff;
display: grid; place-items: center; font-size: .72rem;}
.stTabs [data-baseweb="tab-list"] {gap: .4rem;}
.stTabs [data-baseweb="tab"] {padding: .5rem 1rem; font-weight: 500;}
@media (max-width: 640px) {.hero {padding: 1.5rem;} .hero-title {font-size: 1.9rem;} .grid {grid-template-columns: 1fr;}}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ datos
@st.cache_resource(show_spinner="Cargando el catálogo…")
def cargar():
    return Recomendador.cargar("artefactos.joblib")


rec = cargar()

MENORES = {"de", "del", "la", "las", "el", "los", "y", "e", "o", "u", "en", "a", "al", "un", "una", "con",
           "por", "para", "sin", "the", "of", "and", "in", "to", "a", "on"}


def bonito(t):
    """Los títulos del dataset vienen en MAYÚSCULAS: los pasa a formato título."""
    t = str(t).strip()
    if not t or t.lower() == "nan":
        return ""
    if t != t.upper():
        return t
    pal = t.lower().split()
    return " ".join(p if i and p in MENORES else p[:1].upper() + p[1:] for i, p in enumerate(pal))


def esc(x):
    return html.escape(bonito(x))


def chips(items, clase="chip"):
    return "".join(f'<span class="{clase}">{html.escape(str(i))}</span>' for i in items if str(i).strip())


def generos(s, k=4):
    return [g.strip() for g in str(s).split(",") if g.strip() and g.strip() != "nan"][:k]


def sinopsis(idx, n):
    txt = str(rec.df.loc[idx, "descripcion"])
    return html.escape(txt if len(txt) <= n else txt[:n].rsplit(" ", 1)[0] + "…")


def tarjeta(pos, fila, max_score):
    ancho = 100 * fila.score / max_score if max_score > 0 else 0
    terms = chips(fila.terminos_comunes, "term") or '<span class="chip">—</span>'
    return (
        '<div class="card">'
        f'<div class="card-top"><span class="rank">{pos}</span><div>'
        f'<div class="card-title">{esc(fila.titulo)}</div>'
        f'<div class="card-author">{esc(fila.autor)}</div></div></div>'
        f'<div>{chips(generos(fila.generos))}</div>'
        f'<p class="synopsis">{sinopsis(fila.id, 230)}</p>'
        f'<div class="score-row"><span class="label">Similitud</span>'
        f'<div class="bar"><div style="width:{ancho:.0f}%"></div></div>'
        f'<span class="score">{fila.score:.3f}</span></div>'
        f'<div><span class="label">En común</span>{terms}</div>'
        '</div>'
    )


def mostrar_resultados(out, clave):
    max_score = float(out["score"].max())
    st.markdown('<div class="grid">' + "".join(tarjeta(i, f, max_score)
                for i, f in enumerate(out.itertuples(), 1)) + "</div>", unsafe_allow_html=True)
    if st.toggle("Ver como tabla", key=f"tabla_{clave}"):
        tabla = out.assign(titulo=out["titulo"].map(bonito), autor=out["autor"].map(bonito))
        st.dataframe(
            tabla, hide_index=True, width="stretch",
            column_config={
                "id": None,
                "titulo": "Título", "autor": "Autor", "generos": "Géneros",
                "score": st.column_config.ProgressColumn("Similitud", min_value=0.0, max_value=max_score, format="%.3f"),
                "terminos_comunes": st.column_config.ListColumn("Términos en común"),
            })


def vacio(icono, texto):
    st.markdown(f'<div class="empty"><div class="big">{icono}</div>{texto}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ barra lateral
with st.sidebar:
    st.markdown('<div class="side-title">📚 Ajustes</div>', unsafe_allow_html=True)
    n = st.slider("Número de recomendaciones", 1, 10, 6)
    st.divider()
    st.markdown("**¿Cómo funciona?**")
    st.markdown(
        '<div class="step"><b>1</b>Cada sinopsis se limpia con spaCy: lemas, sin tildes ni stopwords.</div>'
        '<div class="step"><b>2</b>Se representa como vector TF-IDF (palabras y bigramas).</div>'
        '<div class="step"><b>3</b>Se recomiendan los libros con mayor similitud coseno.</div>'
        '<div class="step"><b>4</b>Los términos en común explican cada recomendación.</div>',
        unsafe_allow_html=True)
    st.divider()
    st.caption("NLP desde cero · Proyecto 5 · Recomendador de contenido")

# ------------------------------------------------------------------ cabecera
st.markdown(
    '<div class="hero">'
    '<div class="hero-eyebrow">NLP · Recomendación basada en contenido</div>'
    '<div class="hero-title">Encuentra tu próxima lectura</div>'
    '<p>Elige un libro que te haya gustado o describe con tus palabras lo que te apetece leer. '
    'Te sugerimos títulos con sinopsis parecidas.</p>'
    '<div class="stats">'
    f'<div class="stat"><b>{rec.X.shape[0]:,}</b><span>libros en el catálogo</span></div>'
    f'<div class="stat"><b>{rec.X.shape[1]:,}</b><span>términos en el vocabulario</span></div>'
    '<div class="stat"><b>TF-IDF</b><span>+ similitud coseno</span></div>'
    '</div></div>', unsafe_allow_html=True)

tab_libro, tab_texto = st.tabs(["📖  Libros parecidos a…", "✍️  Describe lo que buscas"])


def libro_al_azar():
    st.session_state.q = str(rec.df.loc[random.randrange(len(rec.df)), "titulo"])


# ------------------------------------------------------------------ pestaña 1: por libro
with tab_libro:
    c1, c2 = st.columns([5, 1], vertical_alignment="bottom")
    q = c1.text_input("Busca un libro por su título", key="q", placeholder="Ej.: noche, amor, historia, guerra…")
    c2.button("🎲 Al azar", on_click=libro_al_azar, width="stretch")

    if not q:
        vacio("🔎", "Escribe parte de un título para empezar, o prueba con un libro <b>al azar</b>.")
    else:
        res = rec.buscar_titulo(q, 30)
        if res.empty:
            vacio("🤔", f"No encontramos títulos que contengan <b>{html.escape(q)}</b>. Prueba con otra palabra.")
        else:
            ids = [int(i) for i in res["id"]]
            idx = st.selectbox(
                f"{len(ids)} coincidencia{'s' if len(ids) != 1 else ''} · elige el libro", ids,
                format_func=lambda i: f"{bonito(rec.df.loc[i, 'titulo'])} — {bonito(rec.df.loc[i, 'autor'])}")
            base = rec.df.loc[idx]
            st.markdown(
                '<div class="featured"><span class="label">Tu libro</span>'
                f'<div class="card-title">{esc(base["titulo"])}</div>'
                f'<div class="card-author">{esc(base["autor"])}</div>'
                f'<div style="margin-top:.5rem">{chips(generos(base.get("generos", ""), 6))}</div>'
                f'<p class="synopsis">{sinopsis(idx, 600)}</p></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Te podrían gustar</div>'
                        '<div class="section-sub">Ordenados por similitud de sinopsis</div>', unsafe_allow_html=True)
            mostrar_resultados(rec.recomendar(idx, n), "libro")

# ------------------------------------------------------------------ pestaña 2: texto libre
EJEMPLOS = [
    "misterio y detectives en una ciudad antigua",
    "una historia de amor durante la guerra",
    "aventuras y viajes por el mar",
    "la vida de un científico famoso",
]

with tab_texto:
    ejemplo = st.pills("Ideas para empezar", EJEMPLOS, selection_mode="single")
    with st.form("form_texto", border=False):
        texto = st.text_area("Describe qué quieres leer", value=ejemplo or "", height=110,
                             placeholder="Ej.: una novela sobre la memoria y la familia en un pueblo pequeño…")
        st.form_submit_button("Recomendar", type="primary", icon="✨")

    if not texto.strip():
        vacio("✍️", "Describe temas, ambientes o personajes y te sugerimos libros con sinopsis parecidas.")
    else:
        out = rec.recomendar_texto(texto, n)
        if out.empty or out["score"].max() <= 0:
            vacio("🤷", "Ninguna palabra de tu descripción aparece en el vocabulario del catálogo. "
                       "Prueba con otras palabras.")
        else:
            st.markdown('<div class="section-title">Resultados</div>'
                        f'<div class="section-sub">Para: “{html.escape(texto.strip())}”</div>', unsafe_allow_html=True)
            mostrar_resultados(out, "texto")

