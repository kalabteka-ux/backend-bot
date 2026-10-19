# ==============================================================
# FOLDER: backend-bot
# FILE: main.py
# ==============================================================
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models
from bot_service import bot, dp
from payments import router as payments_router
from kyc import router as kyc_router
from marketplace import router as market_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eotc_market")

# Lifespan context: handles DB table creation and Bot polling/webhook
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Automatically create all PostgreSQL/SQLite tables
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # 2. Start Telegram Bot background polling (if BOT_TOKEN configured)
    bot_task = None
    if bot:
        logger.info("Starting Telegram Bot listener...")
        bot_task = asyncio.create_task(dp.start_polling(bot))

    yield

    # Shutdown
    if bot_task:
        logger.info("Stopping Telegram Bot...")
        bot_task.cancel()
        if bot.session:
            await bot.session.close()

app = FastAPI(
    title="EOTC Market Backend & Bot API",
    version="1.0.0",
    description="Multi-vendor marketplace inside Telegram with 1.5% commission split & Ethiopian KYC.",
    lifespan=lifespan
)

# CORS configuration for Telegram Mini App & Next.js Super Admin Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all endpoint routers
app.include_router(market_router)
app.include_router(kyc_router)
app.include_router(payments_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "EOTC Market Backend", "commission_rate": "1.5%"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)