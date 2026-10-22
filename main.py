from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# የ Vercel ሊንኮችዎን እዚህ ያስገቡ
origins = [
    "https://your-frontend.vercel.app",
    "https://your-miniapp.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # የተፈቀዱት ዶሜይኖች
    allow_credentials=True,      # ኩኪዎችን ለመፍቀድ
    allow_methods=["*"],         # ሁሉንም ጥያቄዎች (GET, POST...) ለመፍቀድ
    allow_headers=["*"],         # ሁሉንም ሄደሮች ለመፍቀድ
)

# የኤፒአይ መስመሮችዎ
@app.get("/api/data")
def read_data():
    return {"message": "ሰላም ከ Render ባክኤንድ!"}
