import os
import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from datetime import datetime, timedelta


class Auth():
    hasher = CryptContext(schemes=['bcrypt'])
    secret = 'APP_SECRET_STRING'

    def encode_password(self, password):
        return self.hasher.hash(password)
    
    def verify_password(self, password, encode_password):
        return self.hasher.verify(password, encode_password)
    
    def encode_token(self, username):
        payload = {
            'exp' : datetime.utcnow() + timedelta(days=0, minutes=30),
            'iat' : datetime.utcnow(),
            'scope' : 'успешный токен',
            'sub' : username
        }
        return jwt.encode(
            payload,
            self.secret,
            algorithm='HS256'
        )
    
    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            if (payload['scope'] == 'access_token'):
                return payload['sub']
            raise HTTPException(status_code=401, detail=' scope невалидный токен')
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail=' срок действия токена истек')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail=' невалидный токен')
        

    def encode_refresh_token(self, username):
        payload = {
            'exp': datetime.utcnow() + timedelta(days=0, hours=10),
            'iat': datetime.utcnow(),
            'scope': 'свежий токен',
            'sub': username
        }
        return jwt.encode(
            payload,
            self.secret,
            algorithm='HS256'
        )
    def refresh_token(self, refresh_token):
        try:
            payload = jwt.decode(refresh_token, self.secret, algorithms=['HS256'])
            if (payload['scope'] == 'refresh_token'):
                username = payload['sub']
                new_token = self.encode_token(username)
                return new_token
            raise HTTPException(status_code=401, detail="невалидный scope токен")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="свежесть токена истекла")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="неверный свежий токен")












