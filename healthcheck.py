import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select

async def check_db():
    try:
        engine = create_async_engine(os.getenv("DATABASE_URL"))
        async with engine.begin() as conn:
            await conn.execute(select(1))
        print("Database is healthy")
        return True
    except Exception as e:
        print(f"Database unhealthy: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_db()) 