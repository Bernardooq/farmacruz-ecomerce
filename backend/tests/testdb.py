from sqlalchemy import create_engine, text

engine = create_engine("postgresql://myuser:mypassword@localhost:5434/mydatabase")
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.fetchone())
