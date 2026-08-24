# core/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        
        if header is None:
            raw_token = request.COOKIES.get(settings.SIMPLE_JWT.get('AUTH_COOKIE', 'access'))
        else:
            raw_token = self.get_raw_token(header)
            
        if raw_token is None:
            return None
            
        try:
            # টোকেন ভ্যালিড কি না চেক করবে
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except (InvalidToken, TokenError):
            # টোকেন এক্সপায়ার বা ইনভ্যালিড হলে 401 না দিয়ে None রিটার্ন করবে (যাতে পাবলিক API কাজ করে)
            return None