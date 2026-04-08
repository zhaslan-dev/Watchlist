import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from Watchlist.infrastructure.api.kinopoisk import KinopoiskClient, KinopoiskError

@pytest.fixture
def kinopoisk_client():
    return KinopoiskClient(api_key="test_key")

@pytest.mark.asyncio
async def test_search_movies_success(kinopoisk_client):
    mock_response = AsyncMock()
    # ✅ .json() должен возвращать обычный словарь, не AsyncMock
    mock_response.json = MagicMock(return_value={
        "films": [
            {"filmId": 123, "nameRu": "Test", "rating": "7.5"}
        ]
    })
    mock_response.raise_for_status = AsyncMock()
    with patch.object(kinopoisk_client, "_request", return_value=mock_response):
        movies = await kinopoisk_client.search_movies("test")
        assert len(movies) == 1
        assert movies[0].kinopoiskId == 123
        assert movies[0].nameRu == "Test"
        assert movies[0].rating == 7.5

@pytest.mark.asyncio
async def test_search_movies_empty(kinopoisk_client):
    mock_response = AsyncMock()
    mock_response.json = MagicMock(return_value={"films": []})
    mock_response.raise_for_status = AsyncMock()
    with patch.object(kinopoisk_client, "_request", return_value=mock_response):
        movies = await kinopoisk_client.search_movies("nonexistent")
        assert movies == []

@pytest.mark.asyncio
async def test_get_movie_by_id_success(kinopoisk_client):
    mock_response = AsyncMock()
    mock_response.json = MagicMock(return_value={
        "kinopoiskId": 123,
        "nameRu": "Test Movie",
        "ratingKinopoisk": 8.0,
        "year": 2023,
        "type": "FILM",
        "description": "Test description"
    })
    mock_response.raise_for_status = AsyncMock()

    mock_staff_response = AsyncMock()
    mock_staff_response.json = MagicMock(return_value=[
        {"professionKey": "DIRECTOR", "nameRu": "Test Director"}
    ])
    mock_staff_response.raise_for_status = AsyncMock()

    with patch.object(kinopoisk_client, "_request", side_effect=[mock_response, mock_staff_response]):
        movie = await kinopoisk_client.get_movie_by_id(123)
        assert movie is not None
        assert movie.kinopoiskId == 123
        assert movie.nameRu == "Test Movie"
        assert movie.rating == 8.0
        assert movie.director == "Test Director"

@pytest.mark.asyncio
async def test_get_movie_by_id_not_found(kinopoisk_client):
    async def raise_404(*args, **kwargs):
        raise httpx.HTTPStatusError("Not Found", request=None, response=AsyncMock(status_code=404))
    with patch.object(kinopoisk_client, "_request", side_effect=raise_404):
        movie = await kinopoisk_client.get_movie_by_id(999)
        assert movie is None

@pytest.mark.asyncio
async def test_convert_to_media_item(kinopoisk_client):
    from Watchlist.infrastructure.api.kinopoisk import KinopoiskMovie
    movie = KinopoiskMovie(
        kinopoiskId=123,
        nameRu="Original Title",
        description="Desc",
        posterUrl="http://poster",
        rating=7.5
    )
    media_item = await kinopoisk_client.convert_to_media_item(movie)
    assert media_item.external_id == "123"
    assert media_item.title == "Original Title"
    assert media_item.rating == 7.5