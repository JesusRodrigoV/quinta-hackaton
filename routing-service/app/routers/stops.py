from fastapi import APIRouter, Query

from app.core.graph import get_driver
from app.schemas.responses import StationInfo

router = APIRouter()


@router.get("/stops")
async def list_stops(
    skip: int = Query(0, ge=0, description="Stations to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max stations to return"),
):
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (s:Station) RETURN s ORDER BY s.name SKIP $skip LIMIT $limit",
            skip=skip, limit=limit,
        )
        records = await result.data()
        mapped = [
            StationInfo(
                station_id=r["s"]["station_id"],
                name=r["s"]["name"],
                type=r["s"]["type"],
            )
            for r in records
        ]
        return {"stops": mapped}


@router.get("/health")
async def health():
    try:
        driver = get_driver()
        async with driver.session() as session:
            await session.run("RETURN 1")
        return {"status": "healthy", "service": "routing-service"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
