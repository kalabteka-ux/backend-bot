from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. አፑን ማስጀመር
app = FastAPI()

# 2. CORS ማስተካከያ (ከፊት-አንድ ጋር እንድገናኝ የሚያስችል)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ሁሉንም የፊት-አንድ ሊንኮች እንድቀበል ያደርጋል
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. መሠረታዊ የሙከራ ፔጅ (Root Endpoint)
@app.get("/")
def read_root():
    return {"message": "EOTC Market Backend is running successfully!"}

# ከዚህ በታች የቀሩት የዳታቤዝ እና የኢፒአይ (API) ኮዶችዎ ይቀጥላሉ...
