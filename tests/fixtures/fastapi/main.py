from fastapi import FastAPI, APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
import requests

app = FastAPI()
router = APIRouter(prefix='/verify')

class Identity(BaseModel):
    aadhaar_number: str
    email: str

@router.post('/document', response_model=Identity, dependencies=[Depends(require_auth)])
async def document(file: UploadFile = File(...)):
    content = await file.read()
    return {'ok': True}

@router.post('/face')
async def face(selfie: UploadFile = File(...)):
    content = await selfie.read()
    face_service.match(content)
    return {'ok': True}

@router.post('/submit')
async def submit(identity: Identity):
    print(identity.email)
    requests.post('https://processor.invalid', json=identity.email)
    return identity.email

app.include_router(router, prefix='/api')

class OCR:
    def extract(self):
        return {'structured_data': self.fields()}

    def fields(self):
        data = {}
        data['aadhaar_number'] = 'synthetic'
        return data

ocr = OCR()

@app.post('/ocr')
async def ocr_route():
    result = ocr.extract()
    return {'structured_data': result.get('structured_data')}
