from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
  return {"message": "¡Hola, FastAPI en tu proyecto!"}
