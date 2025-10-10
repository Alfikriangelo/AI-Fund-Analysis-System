#!/bin/sh

echo "Initializing database..."
cd /app
python -m app.db.init_db

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000