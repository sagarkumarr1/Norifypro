from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from notifications.tasks import send_welcome_email
from drf_spectacular.utils import extend_schema

User = get_user_model()

class RegisterView(APIView):
    @extend_schema(
        summary="Register a new user",
        description="Creates user account and sends welcome email via Celery background task",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'example': 'sagar'},
                    'email': {'type': 'string', 'example': 'sagar@test.com'},
                    'password': {'type': 'string', 'example': 'test1234'},
                }
            }
        },
        responses={201: {'description': 'User created, email queued'}},
    )
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        # 1. Check if all fields are provided
        if not all([username, email, password]):
            return Response(
                {'error': 'username, email, and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Check if username already exists 
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already taken'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Check if email already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4.create user database
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # 5. Send the task to queue via email — user.id will be passed to the background using .delay().
        send_welcome_email.apply_async(args=[user.id], countdown=1)

        return Response(
            {
                'message': 'Registration successful! Welcome email is being sent.',
                'user_id': user.id,
                'email': user.email
            },
            status=status.HTTP_201_CREATED
        )
