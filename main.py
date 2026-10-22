from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# የ CORS ማስተካከያ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://admin-frontend-brown-three.vercel.app"], # የ Vercel ሊንክ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ሰርቨሩ እየሰራ መሆኑን ለመሞከር (አማራጭ)
@app.get("/")
def read_root():
    return {"message": "ሰላም! ባክኤንድዎ በትክክል እየሰራ ነው!"}

# ፎቶ እና ዳታ የሚቀበለው ኤፒአይ (API)
@app.post("/products")
async def create_product(
    title: str = Form(...), 
    price: str = Form(...), 
    image: UploadFile = File(...)
):
    # ፎቶውን እና ዳታውን ዳታቤዝ ላይ ሴቭ ለማድረግ እዚህ ጋር ይሰራሉ
    return {
        "message": "እቃው እና ፎቶው በትክክል ተጭነዋል!", 
        "title": title,
        "price": price,
        "filename": image.filename
    }
