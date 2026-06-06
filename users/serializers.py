from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
        )

    def validate_email(self, value):
        email = value.lower().strip()

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "Email already registered."
            )

        return email

    def validate_username(self, value):
        username = value.strip()

        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError(
                "Username already taken."
            )

        return username

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )