from fastapi import FastAPI, HTTPException, Query

from recomendador import Recomendador

app = FastAPI(title="Recomendador de libros (TF-IDF + coseno)", version="1.0")
rec = Recomendador.cargar("artefactos.joblib")


@app.get("/health")
def health():
    return {"estado": "ok", "libros": int(rec.X.shape[0]), "terminos": int(rec.X.shape[1]), "idioma": rec.idioma}


@app.get("/items")
def items(q: str = Query(..., min_length=2), limite: int = Query(10, ge=1, le=50)):
    return rec.buscar_titulo(q, limite).to_dict(orient="records")


@app.get("/recomendar")
def recomendar(item_id: int = Query(..., ge=0), n: int = Query(5, ge=1, le=20)):
    if item_id >= len(rec.df):
        raise HTTPException(status_code=404, detail=f"item_id {item_id} fuera del catálogo (0-{len(rec.df)-1})")
    base = rec.df.loc[item_id]
    return {
        "consulta": {"id": item_id, "titulo": base["titulo"], "autor": base.get("autor", "")},
        "recomendaciones": rec.recomendar(item_id, n).to_dict(orient="records"),
    }


@app.get("/recomendar_texto")
def recomendar_texto(texto: str = Query(..., min_length=3), n: int = Query(5, ge=1, le=20)):
    out = rec.recomendar_texto(texto, n)
    if out.empty:
        raise HTTPException(status_code=422, detail="Ninguna palabra de la consulta está en el vocabulario")
    return {"consulta": texto, "recomendaciones": out.to_dict(orient="records")}
