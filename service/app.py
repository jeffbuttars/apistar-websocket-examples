from apistar import ASyncApp
from .handlers import routes


app = ASyncApp(
    routes=routes
)
