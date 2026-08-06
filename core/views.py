from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from django.conf import settings

# Create your views here.
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            response.set_cookie(
                key='access',
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG, 
                samesite='Lax'
            )
            response.set_cookie(
                key='refresh',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax'
            )
            
            response.data = {"detail": "Successfully logged in."}
            
        return response
