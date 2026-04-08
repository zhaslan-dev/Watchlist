import json
import httpx
import tenacity
import logging
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from loguru import logger
from Watchlist.domain.entities import MediaItem, MediaSource
from Watchlist.infrastructure.cache.redis_client import redis_client
from Watchlist.config import settings

class KinopoiskMovie(BaseModel):
    kinopoiskId: int
    nameRu: Optional[str] = None
    nameEn: Optional[str] = None
    description: Optional[str] = None
    posterUrl: Optional[str] = None
    rating: Optional[float] = None
    year: Optional[str] = None
    type: Optional[str] = None
    director: Optional[str] = None

    @staticmethod
    def parse_rating(v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str) and v.lower() == 'null':
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    class Config:
        populate_by_name = True
        json_encoders = {float: lambda v: None if v is None else v}

class KinopoiskError(Exception):
    pass

class KinopoiskClient:
    BASE_URL = "https://kinopoiskapiunofficial.tech/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(base_url=self.BASE_URL, headers={"X-API-KEY": api_key}, timeout=10.0)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        retry=tenacity.retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
    )
    async def _request(self, method: str, url: str, **kwargs):
        response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    async def search_movies(self, query: str, page: int = 1) -> List[KinopoiskMovie]:
        cache_key = f"search:{query}:{page}"
        if redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {cache_key}")
                data = json.loads(cached) if isinstance(cached, str) else cached
                return [KinopoiskMovie.model_validate(item) for item in data]

        params = {"keyword": query, "page": page}
        try:
            response = await self._request("GET", "/v2.1/films/search-by-keyword", params=params)
            data = response.json()
            movies_data = data.get("films", [])
            movies = []
            for m in movies_data:
                m['kinopoiskId'] = m.pop('filmId')
                rating = m.get('rating')
                if rating is not None and isinstance(rating, str) and rating.lower() == 'null':
                    rating = None
                m['rating'] = rating
                movies.append(KinopoiskMovie(**m))
            logger.debug(f"Found {len(movies)} movies for query '{query}'")
            if redis_client:
                await redis_client.setex(cache_key, 3600, json.dumps([m.model_dump() for m in movies]))
            return movies
        except Exception as e:
            logger.exception("Unexpected error during search")
            raise KinopoiskError("Search failed") from e

    async def get_movie_by_id(self, kinopoisk_id: int) -> Optional[KinopoiskMovie]:
        cache_key = f"movie:{kinopoisk_id}"
        if redis_client:
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {cache_key}")
                if isinstance(cached, str):
                    return KinopoiskMovie.model_validate_json(cached)
                else:
                    return KinopoiskMovie.model_validate(cached)

        try:
            response = await self._request("GET", f"/v2.2/films/{kinopoisk_id}")
            data = response.json()

            # Запрос режиссёра
            director = None
            try:
                staff_resp = await self._request("GET", "/v1/staff", params={"filmId": kinopoisk_id})
                staff_data = staff_resp.json()
                for person in staff_data:
                    if person.get("professionKey") == "DIRECTOR":
                        director = person.get("nameRu") or person.get("nameEn")
                        break
            except Exception:
                pass  # режиссёр не критичен

            movie = KinopoiskMovie(
                kinopoiskId=data.get("kinopoiskId"),
                nameRu=data.get("nameRu"),
                nameEn=data.get("nameEn"),
                description=data.get("description"),
                posterUrl=data.get("posterUrl"),
                rating=data.get("ratingKinopoisk"),
                year=str(data.get("year")) if data.get("year") else None,
                type=data.get("type"),
                director=director,
            )
            if redis_client:
                await redis_client.setex(cache_key, 86400, movie.model_dump_json())
            return movie
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Kinopoisk API HTTP error: {e}")
            raise KinopoiskError(f"HTTP error: {e.response.status_code}") from e
        except Exception as e:
            logger.exception(f"Unexpected error fetching movie {kinopoisk_id}")
            raise KinopoiskError("Fetch failed") from e

    async def convert_to_media_item(self, movie: KinopoiskMovie) -> MediaItem:
        title = movie.nameRu or movie.nameEn or "Без названия"
        return MediaItem(
            external_id=str(movie.kinopoiskId),
            title=title,
            description=movie.description,
            poster_url=movie.posterUrl,
            rating=movie.rating,
            source=MediaSource.KINOPOISK,
            year=movie.year,
            director=movie.director,
        )

    async def close(self):
        await self.client.aclose()

_global_client = None

def get_kinopoisk_client() -> KinopoiskClient:
    global _global_client
    if _global_client is None:
        _global_client = KinopoiskClient(settings.KINOPOISK_API_KEY)
    return _global_client