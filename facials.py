import face_recognition as fr
from typing import Any, Collection, List, NewType, TypedDict, Generator, Optional
import numpy as np


FaceEncoding = NewType('FaceEncoding', np.ndarray)


class FaceMetadata(TypedDict, total=False):
    image_path: str
    rect: Optional[Any]


class FaceData(FaceMetadata):
    encoding: FaceEncoding


class FaceDistance(TypedDict):
    face: FaceMetadata
    distance: float


def _encode_face(face_metadata: FaceMetadata) -> FaceEncoding:
    image = fr.load_image_file(face_metadata['image_path'])

    return fr.face_encodings(image, **{
        **({'known_face_locations': [face_metadata['rect']]} if 'rect' in face_metadata else {}),
    })[0]


def encode_face(face_metadata: FaceMetadata) -> FaceData:
    return FaceData(encoding=_encode_face(face_metadata), **face_metadata)


def generate_face_collection(faces: Collection[FaceMetadata]) -> Generator[FaceData, None, None]:
    return (encode_face(face_metadata) for face_metadata in faces)


def compare_face(face_collection: Collection[FaceData], face: FaceData) -> List[FaceDistance]:
    distances = fr.face_distance(
        [f['encoding'] for f in face_collection],
        face['encoding']
    )
    return [FaceDistance(face={k: face_metadata[k] for k in face_metadata if k in FaceMetadata.__annotations__},
                         distance=distance)
            for face_metadata, distance in zip(face_collection, distances)]


# Example
if __name__ == '__main__':
    obama_collection = list(generate_face_collection([
        FaceMetadata(image_path='examples/obama-collection/obama.jpeg'),
        FaceMetadata(image_path='examples/obama-collection/obama2_0.jpg'),
        FaceMetadata(image_path='examples/obama-collection/obama_pointing.jpg')
    ]))

    print(
        "Similarity of obama_pointing.jpg to the entire obama collection:\n",
        compare_face(obama_collection,
                     encode_face(FaceMetadata(image_path='examples/obama-collection/obama_pointing.jpg')))
    )
