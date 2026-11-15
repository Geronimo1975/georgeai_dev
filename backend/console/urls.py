from django.urls import path, re_path

from . import views

app_name = "console"

api = [
    path("bootstrap", views.bootstrap, name="bootstrap"),
    path("conversations", views.conversations, name="conversations"),
    path("conversations/<uuid:pk>", views.conversation_detail, name="conversation"),
    path("conversations/<uuid:pk>/messages", views.send_message, name="send_message"),
    path("conversations/<uuid:pk>/branch", views.switch_branch, name="switch_branch"),
    path("search", views.search, name="search"),
]

pages = [
    re_path(r"^(?P<rest>.*)$", views.console_page, name="page"),
]
