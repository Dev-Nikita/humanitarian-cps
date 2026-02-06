import random
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import requests

@dataclass
class NetworkProfile:
    loss: float = 0.0           # packet loss probability [0..1]
    delay_ms: float = 0.0       # mean additional delay
    jitter_ms: float = 0.0      # jitter (uniform +/-)

class NetworkEmulator:
    def __init__(self, profile: NetworkProfile):
        self.profile = profile
        self.session = requests.Session()

    def _apply(self):
        if self.profile.loss > 0.0:
            if random.random() < self.profile.loss:
                raise TimeoutError("Simulated packet loss")
        d = self.profile.delay_ms
        j = self.profile.jitter_ms
        if d > 0.0 or j > 0.0:
            extra = d + (random.uniform(-j, j) if j > 0.0 else 0.0)
            if extra > 0:
                time.sleep(extra / 1000.0)

    def post_json(self, url: str, payload: dict, timeout: float = 10.0):
        self._apply()
        return self.session.post(url, json=payload, timeout=timeout)

    def get(self, url: str, timeout: float = 10.0):
        self._apply()
        return self.session.get(url, timeout=timeout)
