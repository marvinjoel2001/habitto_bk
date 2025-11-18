from django.urls import re_path
from .consumers import ChatConsumer, InboxConsumer
from .notification_consumers import PropertyNotificationConsumer, TenantNotificationConsumer

websocket_urlpatterns = [
    re_path(r'^/?ws/chat/(?P<room_id>[^/]+)/?$', ChatConsumer.as_asgi()),
    re_path(r'^/?ws/chat/inbox/(?P<user_id>\d+)/?$', InboxConsumer.as_asgi()),
    re_path(r'^/?ws/notifications/(?P<user_id>\d+)/?$', InboxConsumer.as_asgi()),
    re_path(r'^/?ws/property-notifications/(?P<user_id>\d+)/?$', PropertyNotificationConsumer.as_asgi()),
    re_path(r'^/?ws/tenant-notifications/(?P<user_id>\d+)/?$', TenantNotificationConsumer.as_asgi()),
]