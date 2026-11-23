from fastapi import FastAPI

app = FastAPI()

class OCRService:
    def extract(self):
        data = {}
        data['aadhaar_number'] = 'synthetic'
        return data

ocr = OCRService()

@app.post('/ocr')
def extract():
    result = ocr.extract()
    return Response(structured_data=result.get('structured_data', {}))
