#V5fD7s
import random
import string
def genotp():
    otp=''
    for i in range(2):
        otp=otp+random.choice(string.ascii_uppercase)+random.choice(string.digits)+random.choice(string.ascii_lowercase)
    return otp