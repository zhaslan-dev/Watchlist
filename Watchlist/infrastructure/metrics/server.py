from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from aiohttp import web
import asyncio
import threading
from loguru import logger

REQUEST_COUNT = Counter('bot_requests_total', 'Total requests', ['command'])
VOTE_COUNT = Counter('bot_votes_total', 'Total votes', ['vote_type'])
SEARCH_DURATION = Histogram('bot_search_duration_seconds', 'Search duration')

async def metrics_handler(request):
    return web.Response(body=generate_latest(), content_type=CONTENT_TYPE_LATEST)

async def start_metrics_server():
    app = web.Application()
    app.router.add_get('/metrics', metrics_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 9090)
    await site.start()
    logger.info("Metrics server started on port 9090")

def run_metrics():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_metrics_server())
    loop.run_forever()

thread = threading.Thread(target=run_metrics, daemon=True)
thread.start()