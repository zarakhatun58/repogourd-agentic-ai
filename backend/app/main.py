from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as audit_router
from app.api.repository_routes import router as repository_router
from app.api.analysis_routes import router as analysis_router
from app.api.finding_routes import router as finding_router
from app.api.trajectory_routes import router as trajectory_router
from app.api.evaluation_routes import router as evaluation_router
from app.api.changelog_routes import router as changelog_router
from app.api.architecture_routes import router as architecture_router
from app.api.dependency_routes import router as dependency_router
from app.api.testing_routes import router as testing_router


app = FastAPI(
    title="RepoGuard Agent AI",
    version="0.1.0",
)

app.add_middleware( 
    CORSMiddleware,
      allow_origins=[
           "http://localhost:3000",
        "https://repogourd-agentic-ai-1.onrender.com", ],
             allow_credentials=True, 
             allow_methods=["*"], 
             allow_headers=["*"],
               )
app.include_router(audit_router)
app.include_router(repository_router)
app.include_router(analysis_router)
app.include_router(finding_router)
app.include_router(trajectory_router)
app.include_router(evaluation_router)
app.include_router(changelog_router)
app.include_router(architecture_router)
app.include_router(dependency_router)
app.include_router(testing_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "repoguard-agent-ai",
    }