"""
Database initialization
"""
from app.db.base import Base
from app.db.session import engine, SessionLocal

def init_db():
    """Initialize database tables"""
    from app.models import document, fund, transaction
    from app.models.fund import Fund

    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

    # 🔹 Setelah tabel dibuat, lakukan seeding data default
    db = SessionLocal()
    try:
        default_fund = db.query(Fund).filter_by(name="Default Fund").first()
        if not default_fund:
            print("Creating default fund...")
            new_fund = Fund(
                name="Default Fund",
                gp_name="System",
                fund_type="Auto",
                vintage_year=2025
            )
            db.add(new_fund)
            db.commit()
            print("✅ Default fund created successfully!")
        else:
            print("ℹ️ Default fund already exists.")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
