from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import licitacoes, fornecedores, dashboard, alertas, pipeline

app = FastAPI(
    title="API Transparencia Jacarei",
    description="API REST para consumo de dados de licitacoes e contratos.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(licitacoes.router, prefix="/api/v1/licitacoes", tags=["Licitacoes"])
app.include_router(fornecedores.router, prefix="/api/v1/fornecedores", tags=["Fornecedores"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(alertas.router, prefix="/api/v1/alertas", tags=["Alertas"])
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["Pipeline"])

@app.get("/")
def root():
    return {"status": "API rodando. Acesse /docs para a documentacao Swagger."}