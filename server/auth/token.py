import jwt

def genarate_token(payload, secret, headers=None):
    token = jwt.encode(payload, secret, algorithm='HS256', headers=headers)
    return token

def decode_token(token, secret):
    return jwt.decode(token, secret)


