from django.urls import re_path
from .consumers import ChatConsumer, InboxConsumer

websocket_urlpatterns = [
    re_path(r'^/?ws/chat/(?P<room_id>[^/]+)/?$', ChatConsumer.as_asgi()),
    re_path(r'^/?ws/chat/inbox/(?P<user_id>\d+)/?$', InboxConsumer.as_asgi()),
    re_path(r'^/?ws/notifications/(?P<user_id>\d+)/?$', InboxConsumer.as_asgi()),
]