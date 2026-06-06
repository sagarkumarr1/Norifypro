from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from notifications.models import Notification
from notifications.tasks import send_welcome_email

from .serializers import RegisterSerializer


class RegisterView(APIView):

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        with transaction.atomic():

            user = serializer.save()

            notification = Notification.objects.create(
                user=user,
                notification_type=Notification.TYPE_WELCOME,
                subject=f"Welcome to NotifyPro, {user.username}!",
                message=(
                    f"Hi {user.username},\n\n"
                    "Your account has been successfully created.\n\n"
                    "Thank you for joining NotifyPro!"
                ),
            )

        send_welcome_email.delay(
            notification.id
        )

        return Response(
            {
                "message": (
                    "Registration successful! "
                    "Welcome email is being sent."
                ),
                "user_id": user.id,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )