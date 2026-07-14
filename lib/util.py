import random
import time


def random_id() -> str:
    return f"{random.getrandbits(48):x}{int(time.time() * 1000):x}"
