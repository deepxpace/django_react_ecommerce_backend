from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from userauths.models import User, Profile
from userauths.serializers import (
    MyTokenObtainPairSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
)
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

import shortuuid

# Create your views here.


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        print(f"Registration request received: {request.data}")
        
        # Normalize email to prevent case sensitivity issues
        email = request.data.get('email', '').lower().strip() if request.data.get('email') else ''
        
        # Validate email uniqueness before serializer validation
        if email and User.objects.filter(email=email).exists():
            return Response(
                {"detail": "A user with this email already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update email in request data
        mutable_data = request.data.copy()
        if email:
            mutable_data['email'] = email
            
        serializer = self.get_serializer(data=mutable_data)
        
        # Check if serializer is valid but don't raise exception yet
        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
            # Extract and format error message for better user experience
            error_detail = self._format_error_message(serializer.errors)
            return Response({"detail": error_detail}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Create the user
            user = serializer.save()
            print(f"User created successfully: {user.email}")
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            error_message = str(e)
            
            # Handle specific error cases
            if "email" in str(e) and "already exists" in str(e):
                error_message = "A user with this email already exists."
            elif "username" in str(e) and "already exists" in str(e):
                error_message = "This username is already taken."
                
            return Response({"detail": error_message}, status=status.HTTP_400_BAD_REQUEST)
    
    def _format_error_message(self, errors):
        """Format error messages from serializer for better UI display"""
        if 'email' in errors:
            return f"Email error: {errors['email'][0]}"
        elif 'password' in errors:
            return f"Password error: {errors['password'][0]}"
        elif 'full_name' in errors:
            return f"Name error: {errors['full_name'][0]}"
        elif 'phone' in errors:
            return f"Phone error: {errors['phone'][0]}"
        else:
            # Return the first error if we can't categorize it
            for field, messages in errors.items():
                if messages:
                    return f"{field} error: {messages[0]}"
            return "Invalid data provided. Please check your input."


def generate_otp():
    uuid_key = shortuuid.uuid()
    unique_key = uuid_key[:6]
    return unique_key


class PasswordResetEmailVerify(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def get_object(self):
        email = self.kwargs["email"]
        try:
            user = User.objects.get(email=email)
            user.otp = generate_otp()
            user.save()

            uidb64 = user.pk
            otp = user.otp

            # Generate reset link (adjust the URL to match your frontend)
            frontend_url = "http://localhost:5175"  # Updated to current port
            link = f"{frontend_url}/create-new-password?otp={otp}&uidb64={uidb64}"
            
            print(f"Password reset link: {link}")
            
            # TODO: Send email to user with the reset link
            # You would implement email sending here using Django's email functionality
            # For now, we'll just print the link for testing purposes
            
            return user
        except User.DoesNotExist:
            # Return a response instead of the object when user doesn't exist
            from django.http import Http404
            raise Http404("User with this email does not exist.")


class PasswordChangeView(generics.CreateAPIView):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        try:
            payload = request.data
            
            # Validate required fields
            required_fields = ['otp', 'uidb64', 'password']
            for field in required_fields:
                if field not in payload or not payload[field]:
                    return Response(
                        {"message": f"Field '{field}' is required"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            otp = payload["otp"]
            uidb64 = payload["uidb64"]
            password = payload["password"]
            
            # Basic password validation
            if len(password) < 8:
                return Response(
                    {"message": "Password must be at least 8 characters long"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                # Find user with matching ID and OTP
                user = User.objects.get(id=uidb64, otp=otp)
                
                # Update password and clear OTP
                user.set_password(password)
                user.otp = ""
                user.save()
                
                return Response(
                    {"message": "Password changed successfully"},
                    status=status.HTTP_200_OK
                )
                
            except User.DoesNotExist:
                return Response(
                    {"message": "Invalid reset link or OTP. Please request a new password reset."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [
        AllowAny,
    ]

    def get_object(self):
        user_id = self.kwargs["user_id"]
        
        # Handle undefined, null or invalid user_id
        if user_id in ('undefined', 'null') or not user_id:
            if self.request.user.is_authenticated:
                # Use authenticated user instead
                user = self.request.user
            else:
                # Return 404 if no valid user
                from django.http import Http404
                raise Http404("User not found")
        else:
            try:
                user = User.objects.get(id=user_id)
            except (User.DoesNotExist, ValueError):
                from django.http import Http404
                raise Http404("User not found")
                
        try:
            profile = Profile.objects.get(user=user)
            return profile
        except Profile.DoesNotExist:
            # Create profile if doesn't exist
            profile = Profile.objects.create(user=user)
            return profile


class MyTokenRefreshView(TokenRefreshView):
    """Custom TokenRefreshView using correct serializer import path."""
    serializer_class = TokenRefreshSerializer
