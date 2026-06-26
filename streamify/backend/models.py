from dataclasses import dataclass


@dataclass
class Stream:
    name: str
    url_id: int
    category_id: int
