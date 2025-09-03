from aiohttp import web

from .constants import constants

routes = web.RouteTableDef()


@routes.get("/health")
async def health(_: web.Request) -> web.Response:
    """Simple health check endpoint."""
    return web.json_response({"status": "healthy"})


async def run_http_server(
    host: str = constants.DEFAULT_HEALTH_HOST,
    port: int = constants.DEFAULT_HEALTH_PORT,
):
    """Run the simple health check server."""
    app = web.Application()

    app.add_routes(routes)

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(runner, host, port)

    await site.start()
