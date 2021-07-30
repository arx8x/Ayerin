from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MediaType(Enum):
    IMAGE = 1
    VIDEO = 2
    AUDIO = 3
    VIDEOAUDIO = 5


@dataclass
class MediaObject:
    url: str
    mediatype: MediaType
    filesize: Optional[int] = 0
    height: Optional[int] = 0
    width: Optional[int] = 0
    duration: Optional[int] = 0
    caption: Optional[str] = None
    file_name: Optional[str] = None
    local_path: Optional[str] = None
    thumbnail: Optional[str] = None
