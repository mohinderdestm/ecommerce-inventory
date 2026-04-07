import random
import string

def generate_sku(category: str, name: str, color=None, size=None):
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{category[:3]}-{name[:3]}-{color or 'NA'}-{size or 'NA'}-{rand}".upper()






