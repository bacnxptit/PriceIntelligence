import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
url = os.getenv("SUPABASE_DB_URL")
print("Connecting to Supabase PostgreSQL...")
try:
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT version();")).fetchone()
        print("Connected successfully!")
        print("Version:", res[0][:50])
        tables = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
            )
        ).fetchall()
        print("Tables:", [t[0] for t in tables])
except Exception as e:
    print("PostgreSQL connection error:", e)
