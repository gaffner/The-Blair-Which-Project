from typing import NewType, Tuple, Union, Collection
import face_recognition
import numpy as np
import io
from enum import Enum


FaceEncoding = NewType("FaceEncoding", np.ndarray)


class FaceLocation(object):
    def __init__(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self.x1: int = x1
        self.y1: int = y1
        self.x2: int = x2
        self.y2: int = y2
    
    @staticmethod
    def from_fr_rect(fr_rect: tuple[int, int, int, int]) -> 'FaceLocation':
        x1: int = fr_rect[3]
        y1: int = fr_rect[0]
        x2: int = fr_rect[1]
        y2: int = fr_rect[2]
        return FaceLocation(x1, y1, x2, y2)
        
        
    def fr_rect(self) -> tuple[int, int, int, int]:
        """
        Represent this location in the format expected by `face_recognition` for `rect` args.
        """
        return (self.y1, self.x2, self.y2, self.x1)
    
    def rect(self) -> tuple[int, int, int, int]:
        """
        Represent this location as an (x1, y1, x2, y2) coordinate tuple,
        as expected by `PIL` and other sane libraries.
        """
        return (self.x1, self.y1, self.x2, self.y2)
        

class ImageFormat(Enum):
    BYTE_STREAM = 'BYTE_STREAM'
    LOCAL_PATH = 'LOCAL_PATH'
    URL = 'URL'
    ID = 'ID'


class FaceData(object):
    def __init__(self,
                 image_format: ImageFormat,
                 image_data: Union[str, bytes, int],
                 location: Union[FaceLocation, tuple[int, int, int, int]],
                 encoding: FaceEncoding = None,
                 **extra_properties):
        self.image_data: Union[str, bytes, int] = image_data
        self.image_format: ImageFormat = image_format
        
        self.location: FaceLocation
        if isinstance(location, tuple):
            location = FaceLocation(location)
        self.location = location
            
        self.encoding: FaceEncoding
        if encoding is None:
            self.encoding = FaceData.encode(image_data, location)
        else:
            self.encoding = encoding
            
        self.extra_properties = extra_properties

    def compare(self, other_faces: Collection['FaceData']) -> list[tuple['FaceData', float]]:
        other_encodings = [other.encoding for other in other_faces]
        distances = face_recognition.face_distance(other_encodings, self.encoding)
        return [(face, distance) for face, distance in zip(other_faces, distances)]
    
    def cropped_face_image(self, image_format: ImageFormat = None, image_data: Union[str, bytes] = None):
        """
        Return a byte stream of the image of this face, cropped to contain only this face (using self.location).
        If an `image_format` and `image_data` are entered as arguments, these will be used instead of the ones stored in `self` - 
        this is needed for the case of a `self.image_format == ImageFormat.ID`, as the real image data is contained in a `FaceDB`.
        """
        pass

    @staticmethod
    def extract_from_image(image_format: ImageFormat,
                           image_data: Union[str, bytes, int]) -> list['FaceData']:
        if image_format == ImageFormat.BYTE_STREAM:
            image_file = io.BytesIO(image_data)
            image = face_recognition.load_image_file(image_file)
        elif image_format == ImageFormat.LOCAL_PATH:
            image = face_recognition.load_image_file(image_data)
        else:
            raise NotImplementedError
            
        face_locations = face_recognition.face_locations(image)
        if not face_locations:
            return []

        return [
            FaceData(image_format, image_data, FaceLocation.from_fr_rect(location),
                    face_recognition.face_encodings(image, known_face_locations=[location])[0])
            for location in face_locations
        ]



if __name__ == '__main__':
    obama_1_faces = FaceData.extract_from_image(ImageFormat.LOCAL_PATH, './examples/obama-collection/obama.jpeg')
    print([face.image_data for face in obama_1_faces])

    obama = obama_1_faces[0]
    
    obama_2_faces = FaceData.extract_from_image(ImageFormat.LOCAL_PATH, './examples/obama-collection/obama_pointing.jpg')
    print(obama.compare(obama_2_faces))