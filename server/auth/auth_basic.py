from jwt import algorithms
import base64



def verify_user(user, username, password):
    key = user.key
    sig = calculate_digest(username, password, key)
    if user.password == sig:
        return True
    return False

def calculate_digest(user, password, key):
    sign_in = str(user) + str(password)
    HMACAlgorithm = algorithms.HMACAlgorithm
    alg_obj = HMACAlgorithm(HMACAlgorithm.SHA256)
    sig = alg_obj.sign(sign_in, key)
    return base64.urlsafe_b64encode(sig)