import requests
from jose import jwt
from rest_framework import authentication, exceptions
import os
import environ
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# tell django-environ to read .env
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env'))


SUPABASE_URL = env('SUPABASE_URL')
JWKS_URL = f"{SUPABASE_URL}/.well-known/jwks.json"

class SupabaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        jwks = requests.get(JWKS_URL).json()
        unverified_header = jwt.get_unverified_header(token)
        
        rsa_key = {}
        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
        if not rsa_key:
            raise exceptions.AuthenticationFailed('Unable to find appropriate key')
        
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=['RS256'],
                audience='authenticated',
                issuer=f'{SUPABASE_URL}/auth/v1'
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.JWTClaimsError:
            raise exceptions.AuthenticationFailed('Invalid token claims')
        except Exception:
            raise exceptions.AuthenticationFailed('Token decode failed')
        
        user_id = payload.get('sub')
        if not user_id:
            raise exceptions.AuthenticationFailed('Invalid token payload')

        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(username=user_id)
        
        return (user, None)
