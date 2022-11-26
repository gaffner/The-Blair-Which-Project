
# gef
def get_available_collections() -> str:
    pass

def upload_face():
    """
    Encode and upload new face to DB
    :return:
    """

class FaceDataFormat(Enum):
    BYTE_STREAM = 0
    LOCAL_PATH = 1
    URL = 2

# gef
def compare_face_to_collections(face_data_format: FaceDataFormat, face_data: Union[bytes, str, FaceData],
                                collections: Collection[str]):
    """

    :param face_data: Face to compare against the collections. Can be a:
        - byte stream of the image file
        - local path to the face image
    :return:
    """