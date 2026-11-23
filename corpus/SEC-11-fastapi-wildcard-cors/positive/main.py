from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'])
@app.post('/face/match')
async def match(selfie_image: UploadFile = File(...)):
    content = await selfie_image.read()
    return face_service.match_faces(content)
