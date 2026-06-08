import asyncio
from sqlalchemy import select
from app.core.security import get_password_hash
from app.db.session import engine, AsyncSessionFactory
from app.models.user import User
from app.models.category import Category
from app.models.item import Item
from app.models.enums import UserRole
from decimal import Decimal

async def seed_data():
    async with AsyncSessionFactory() as session:
        async with session.begin():
            # Check if categories already exist
            categories = {
                "Electronics": "electronics",
                "Cameras": "cameras",
                "Camping Gear": "camping-gear",
                "Tools": "tools"
            }
            
            db_categories = {}
            for name, slug in categories.items():
                stmt = select(Category).where(Category.slug == slug)
                res = await session.execute(stmt)
                cat = res.scalar_one_or_none()
                if not cat:
                    cat = Category(name=name, slug=slug, description=f"Premium rentals for {name}")
                    session.add(cat)
                    print(f"Created category: {name}")
                db_categories[slug] = cat
            
            # Flush to get category IDs
            await session.flush()
            
            # Create Owner User
            owner_email = "owner@example.com"
            stmt = select(User).where(User.email == owner_email)
            res = await session.execute(stmt)
            owner = res.scalar_one_or_none()
            if not owner:
                owner = User(
                    email=owner_email,
                    phone="9876543210",
                    city="Bengaluru",
                    hashed_password=get_password_hash("securepassword123"),
                    full_name="Rajesh Kumar",
                    role=UserRole.OWNER,
                    is_verified=True,
                    is_active=True
                )
                session.add(owner)
                print("Created owner user")
                
            # Create Renter User
            renter_email = "renter@example.com"
            stmt = select(User).where(User.email == renter_email)
            res = await session.execute(stmt)
            renter = res.scalar_one_or_none()
            if not renter:
                renter = User(
                    email=renter_email,
                    phone="8765432109",
                    city="Pune",
                    hashed_password=get_password_hash("securepassword123"),
                    full_name="Priya Sharma",
                    role=UserRole.RENTER,
                    is_verified=True,
                    is_active=True
                )
                session.add(renter)
                print("Created renter user")
                
            await session.flush()
            
            # Create Items
            items_to_create = [
                {
                    "title": "DJI Mavic 3 Pro Drone",
                    "description": "Professional camera drone with 3 batteries and controller. Perfect for aerial photography in India.",
                    "daily_price": Decimal("2500.00"),
                    "security_deposit": Decimal("80000.00"),
                    "location_lat": 12.9716,
                    "location_lng": 77.5946,
                    "location_text": "Koramangala, Bengaluru",
                    "category_slug": "electronics",
                    "images": {"url": "/assets/drone.png"}
                },
                {
                    "title": "Sony Alpha 7 IV Mirrorless Camera",
                    "description": "Professional 33MP mirrorless camera with 28-70mm lens. Ideal for wedding and event photography.",
                    "daily_price": Decimal("3500.00"),
                    "security_deposit": Decimal("120000.00"),
                    "location_lat": 18.5204,
                    "location_lng": 73.8567,
                    "location_text": "Bandra, Mumbai",
                    "category_slug": "cameras",
                    "images": {"url": "/assets/camera.png"}
                },
                {
                    "title": "Premium Camping Tent Set",
                    "description": "Double-walled 3-season dome tent with waterproof cover. Great for Western Ghats trekking.",
                    "daily_price": Decimal("600.00"),
                    "security_deposit": Decimal("15000.00"),
                    "location_lat": 18.5244,
                    "location_lng": 73.8307,
                    "location_text": "Pune City Center, Pune",
                    "category_slug": "camping-gear",
                    "images": {"url": "/assets/tent.png"}
                },
                {
                    "title": "Cordless Drill/Driver Kit",
                    "description": "Heavy-duty cordless drill with batteries and charger. Perfect for home renovation projects.",
                    "daily_price": Decimal("400.00"),
                    "security_deposit": Decimal("10000.00"),
                    "location_lat": 16.6833,
                    "location_lng": 75.8667,
                    "location_text": "Sangli City, Sangli",
                    "category_slug": "tools",
                    "images": {"url": "/assets/drill.png"}
                },
                {
                    "title": "HD Projector for Home Theater",
                    "description": "4K HD Projector with 3000 lumens brightness. Perfect for movie nights and presentations.",
                    "daily_price": Decimal("1200.00"),
                    "security_deposit": Decimal("40000.00"),
                    "location_lat": 12.9716,
                    "location_lng": 77.5946,
                    "location_text": "Indiranagar, Bengaluru",
                    "category_slug": "electronics",
                    "images": {"url": "/assets/projector.png"}
                },
                {
                    "title": "Professional DSLR Camera Bundle",
                    "description": "Canon 5D Mark IV with 24-105mm and 50mm lenses. Great for professional shoots.",
                    "daily_price": Decimal("4000.00"),
                    "security_deposit": Decimal("150000.00"),
                    "location_lat": 18.5204,
                    "location_lng": 73.8567,
                    "location_text": "South Mumbai, Mumbai",
                    "category_slug": "cameras",
                    "images": {"url": "/assets/dslr.png"}
                }
            ]
            
            for itm in items_to_create:
                stmt = select(Item).where(Item.title == itm["title"])
                res = await session.execute(stmt)
                item = res.scalar_one_or_none()
                if not item:
                    item = Item(
                        title=itm["title"],
                        description=itm["description"],
                        daily_price=itm["daily_price"],
                        security_deposit=itm["security_deposit"],
                        location_lat=itm["location_lat"],
                        location_lng=itm["location_lng"],
                        location_text=itm["location_text"],
                        owner_id=owner.id,
                        category_id=db_categories[itm["category_slug"]].id,
                        images=itm["images"],
                        is_active=True
                    )
                    session.add(item)
                    print(f"Created item listing: {itm['title']}")
                else:
                    item.images = itm["images"]
                    item.daily_price = itm["daily_price"]
                    item.security_deposit = itm["security_deposit"]
                    print(f"Updated item listing: {itm['title']}")
                    
    await engine.dispose()
    print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
