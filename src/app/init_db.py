from __future__ import annotations

import logging

from app.db import Base, engine


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    init_db()
    logging.info("Database tables created.")
