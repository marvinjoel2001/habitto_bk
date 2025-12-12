from django.urls import path
from payments.views import receive_notification, generate_qr_view


urlpatterns = [
    path('bnb/notify', receive_notification, name='bnb_notify'),
    path('bnb/generate-qr', generate_qr_view, name='bnb_generate_qr'),
]

