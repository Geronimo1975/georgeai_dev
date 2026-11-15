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
    path("me/preferences", views.preferences, name="preferences"),
    path("styles", views.styles, name="styles"),
    path("styles/<uuid:pk>", views.style_detail, name="style"),
    path("messages/<uuid:pk>/feedback", views.message_feedback, name="message_feedback"),
]

pages = [
    re_path(r"^(?P<rest>.*)$", views.console_page, name="page"),
]
