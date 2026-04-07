import random
import string
from datetime import datetime


def generate_sku(brand: str = "", category_name: str = "") -> str:

    # Brand prefix: first 3 letters of brand, uppercased
    brand_part = (brand[:3] if brand else "PRD").upper().replace(" ", "")

    # Category prefix: first 3 letters of category, uppercased
    cat_part = (category_name[:3] if category_name else "GEN").upper().replace(" ", "")

    # Timestamp component: YYMM
    ts_part = datetime.now().strftime("%y%m")

    # Random suffix: 4 alphanumeric chars
    rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

    return f"{brand_part}-{cat_part}-{ts_part}{rand_part}"