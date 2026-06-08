"""
Reset database: drops all tables and recreates schema.
Run this before seeding new data.
"""
import asyncio
from app.db.session import engine
from app.models.base import Base


async def reset_database():
    """Drop all tables and recreate the schema."""
    async with engine.begin() as conn:
        # Drop all tables
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("✓ All tables dropped")
        
        # Recreate all tables
        print("Recreating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Tables recreated successfully")
        
    await engine.dispose()
    print("\n✅ Database reset complete! Now run: python seed.py")


if __name__ == "__main__":
    asyncio.run(reset_database())
