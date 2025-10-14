from typing import TypedDict, Optional, List, Literal
from datetime import datetime


class SessionData(TypedDict):
    phone: str
    pod: str
    active: bool
    count_use: int
    count_success: int
    created: datetime
    last_use: Optional[datetime]
    next_use: Optional[datetime]


ImageFormat = Literal["preview", "image"]