import asyncio
import logging

from neo4j import AsyncGraphDatabase

from app.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logger = logging.getLogger(__name__)
_driver = None


async def init_driver():
    global _driver
    last_error = None
    for attempt in range(3):
        try:
            _driver = AsyncGraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                connection_timeout=10,
                max_transaction_retry_time=30,
            )
            await _driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", NEO4J_URI)
            return
        except Exception as e:
            last_error = e
            logger.warning("Neo4j attempt %d/3 failed: %s", attempt + 1, e)
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
    raise last_error


def set_driver(driver):
    global _driver
    _driver = driver


def get_driver():
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialized")
    return _driver


async def close_driver():
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
