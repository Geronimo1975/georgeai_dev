"""Session-based auth API (DRF) for the frontend signin/signup form.

Uses SessionAuthentication (the session cookie) and csrf_protect so every
unsafe request — including anonymous signup/login — requires the CSRF token
that auth.js sends as X-CSRFToken.
"""
from django.contrib.auth import (
    authenticate,
    login as auth_login,
    logout as auth_logout,
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, SignupSerializer, UserSerializer


def _state(user, status_code=status.HTTP_200_OK):
    return Response({"authenticated": True, **UserSerializer(user).data}, status=status_code)


@method_decorator(csrf_protect, name="dispatch")
class SignupView(APIView):
    def post(self, request):
        s = SignupSerializer(data=request.data)
        if not s.is_valid():
            if "email_taken" in str(s.errors.get("email", "")):
                return Response({"error": "email_taken"}, status=status.HTTP_409_CONFLICT)
            if "password" in s.errors:
                return Response({"error": "weak_password", "detail": s.errors["password"]},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "email_and_password_required", "detail": s.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        user = s.save()
        auth_login(request, user)
        return _state(user, status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    def post(self, request):
        s = LoginSerializer(data=request.data)
        if not s.is_valid():
            return Response({"error": "email_and_password_required"},
                            status=status.HTTP_400_BAD_REQUEST)
        email = s.validated_data["email"].strip().lower()
        user = authenticate(request, username=email, password=s.validated_data["password"])
        if user is None:
            return Response({"error": "invalid_credentials"},
                            status=status.HTTP_401_UNAUTHORIZED)
        auth_login(request, user)
        if not s.validated_data.get("remember"):
            request.session.set_expiry(0)  # clear on browser close
        return _state(user)


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    def post(self, request):
        auth_logout(request)
        return Response({"authenticated": False})


class MeView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            return _state(request.user)
        return Response({"authenticated": False})
