from dataclasses import dataclass


@dataclass(slots=True)
class ImageData:
    url: str
    real_url: str = ''
    modelVersionId: str = ''
    postId: str = ''
    imageId: str = ''
    is_parsed: bool = False


@dataclass(slots=True)
class VersionIdData:
    version_name: str
    model_id: str
    model_name: str
    creator: str
