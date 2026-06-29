from fastapi import FastAPI
from app.api.routes import appointments, auth, doctors, patients, queue

app = FastAPI(title="Medi-Q API", version="0.1.0")

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(queue.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}