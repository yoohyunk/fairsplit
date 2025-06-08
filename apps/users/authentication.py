from rest_framework import authentication, exceptions
import os
import environ
from pathlib import Path
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env'))

SUPABASE_URL = env('SUPABASE_URL')
SUPABASE_KEY = env('SUPABASE_ANON_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class SupabaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Supabase 클라이언트를 사용하여 토큰 검증
            user = supabase.auth.get_user(token)
            
            from django.contrib.auth.models import User
            from .models import Profile
            
            django_user, created = User.objects.get_or_create(
                username=user.user.id,
                defaults={
                    'email': user.user.email,
                    'first_name': user.user.user_metadata.get('full_name', ''),
                }
            )
            
            # Profile이 없으면 생성
            if not hasattr(django_user, 'profile'):
                Profile.objects.create(
                    user=django_user,
                    username=user.user.user_metadata.get('username', user.user.email),
                    bio=user.user.user_metadata.get('bio', ''),
                    avatar_url=user.user.user_metadata.get('avatar_url', '')
                )
            
            return (django_user, None)
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise exceptions.AuthenticationFailed('Invalid token')
