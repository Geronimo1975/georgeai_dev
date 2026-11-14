from django.urls import path, re_path

from . import views

app_name = "console"

api = [
    path("bootstrap", views.bootstrap, name="bootstrap"),
    path("conversations", views.conversations, name="conversations"),
    path("conversations/<uuid:pk>", views.conversation_detail, name="conversation"),
    path("conversations/<uuid:pk>/messages", views.send_message, name="send_message"),
]

pages = [
    re_path(r"^(?P<rest>.*)$", views.console_page, name="page"),
]
