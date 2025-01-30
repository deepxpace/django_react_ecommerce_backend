from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from userauths.models import User, Profile
from userauths.serializers import MyTokenObtainPairSerializer, RegisterSerializer, UserSerializer 

import shortuuid

# Create your views here.


class MyTokenObtainPairView(TokenObtainPairView):
  serializer_class = MyTokenObtainPairSerializer
  
class RegisterView(generics.CreateAPIView):
  queryset = User.objects.all()
  permission_classes = (AllowAny,)
  serializer_class = RegisterSerializer
  
def generate_otp():
  uuid_key = shortuuid.uuid()
  unique_key = uuid_key[:6]
  return unique_key
  
class PasswordResetEmailVerify(generics.RetrieveAPIView):
  permission_classes = (AllowAny,)
  serializer_class = UserSerializer
  
  def get_object(self):
    email = self.kwargs['email']
    user = User.objects.get(email=email)
    
    if user:
      user.otp = generate_otp()
      user.save()
      
      uidb64 = user.pk
      otp = user.otp
      
      link = f'http://localhost:5173/create-new-password?otp={otp}&uidb64={uidb64}'
      
      print('link ===== ', link)
      
      # Send Email to User
      
    return user
  
class PasswordChangeView(generics.CreateAPIView):
  permission_classes = [AllowAny,]
  serializer_class = UserSerializer
  
  def create(self, request, *args, **kwargs):
    payload = request.data
    
    otp = payload['otp']
    uidb64 = payload['uidb64']
    password = payload['password']
    
    user = User.objects.get(id=uidb64, otp=otp)
    
    if user:
      user.set_password(password)
      user.otp = ''
      user.save()
      
      return Response({'message': 'Password changed successfully'}, status=status.HTTP_201_CREATED)
    else:
      return Response({'message': 'An error occured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)