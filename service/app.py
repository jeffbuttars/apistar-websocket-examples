from apistar import ASyncApp
from handlers import routes, WebSocketEvents


app = ASyncApp(
    event_hooks=[WebSocketEvents],
    routes=routes,
)
