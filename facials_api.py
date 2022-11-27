from typing import Union

import facedb
import facials


DB_PATH = './facedb.db'
face_db = facedb.FaceDB(DB_PATH)


def get_available_tags() -> list[str]:
    return face_db.get_all_tags()


def compare_stored_face_against_tags(face_id: facedb.FaceIndex, tags: list[str]) -> list[tuple[facials.FaceData, float]]:
    """
    Compare a face already stored in the existing FaceDB, by it's face ID,
    to all stored faces which have any of the entered tags.
    Example:
        to compare a face with ID `14` to all faces with one of the tags 'gefen-family' and 'hot-senioritas', run:
        compare_stored_face_against_tags(14, ['gefen-family', 'hot-senioritas'])

    Args:
        face_id (facedb.FaceIndex): ID of the face to compare in the used FaceDB
        tags (list[str]): a list of tags for constructing the list of faces to be compared against

    Returns:
        list[tuple[facials.FaceData, float]]: a list of tuples representing the distance to each compared face (the second element being the distance).
    """

    face = face_db.get_face_by_id(face_id)
    if not face:
        return []
    
    faces_against = list(face_db.get_faces_by_tags(tags))
    
    return face.compare(faces_against)


def compare_face_from_image_against_tags(image_format: facials.ImageFormat, image_data: Union[bytes, str],
                                         tags: list[str]) -> list[tuple[facials.FaceData, float]]:
    """
    Similar to `compare_stored_face_against_tags`, but instead of a stored face use a face from the entered image.
    This function currently only supports images with a single faces (for images with multiple faces, one of the faces in it will be chosen semi-randomly).
    The entered image can be a byte stream (of any common image format), or a local path. (URL to be added soon)

    Args:
        image_format (facials.ImageFormat): A descriptor for the format of the entered image, taken as the way to parse `image_data`.
            Can be ImageFormat.BYTE_STREAM, or ImageFormat.LOCAL_PATH. other options are unimplemented.
        image_data (Union[bytes, str]): In the case of ImageFormat.LOCAL_PATH, this is taken as the image path.
            In the case of ImageFormat.BYTE_STREAM, this is taken as the image byte stream.
        tags (list[str]): a list of tags for constructing the list of faces to be compared against.

    Returns:
        list[tuple[facials.FaceData, float]]: a list of tuples representing the distance to each compared face (the second element being the distance)._description_
    """
    
    face = facials.FaceData.extract_from_image(image_format, image_data)
    if not len(face):
        return []
    face = face[0]
    
    faces_against = list(face_db.get_faces_by_tags(tags))
    
    return face.compare(faces_against)


def upload_faces_from_image(image_format: facials.ImageFormat, image_data: Union[bytes, str], description: str, tags: list[str]) -> list[facedb.FaceIndex]:
    """
    Add a face to the FaceDB from any source specifiable in ImageFormat, similarly to the previous functions.
    Stores the image in a single new `images` table row,
    and EVERY detected face in a new row of it's own in the `faces` table.

    Args:
        image_format (facials.ImageFormat): see previous docstrings
        image_data (Union[bytes, str]): see previous docstrings
        description (str): a description string to be stored alongside every detected face and alongside the image.
        tags (list[str]): a list of strings to be stored alongside every detected face (tags are not stored the image).

    Returns:
        list[facedb.FaceIndex]: A list of the indexes of the new rows created in the `faces` table in FaceDB.
            These indexes can be later used to compare the faces against other face groups and whatnot.
    """
    return face_db.add_faces_from_image(image_format, image_data, description, tags)


if __name__ == '__main__':
    # Adding faces from local path
    group_face_indexes = upload_faces_from_image(facials.ImageFormat.LOCAL_PATH, './examples/group.jpg', 'from group photo', ['gefen-family'])
    print(f"Group image face indexes: {group_face_indexes}")

    # Adding faces from byte stream (Can be converted to base64 or web something like that GEFEN)
    with open('./examples/obama-collection/obama.jpeg', 'rb') as obama_f:
        obama_image_bytestream = obama_f.read()
    
    obama_face_indexes = upload_faces_from_image(facials.ImageFormat.BYTE_STREAM, obama_image_bytestream, 'obamus', ['superheroes', 'presidents'])
    print(f"Obama image face indexes: {obama_face_indexes}")
    
    # Showing all available face tags
    print(f"Available face tags: {get_available_tags()}")
    
    # Compare obama stored face against all faces with the "gefen-family" tag
    # of course the output should be formatted to something nicer than just <FaceData> but you know
    print(f"Obama comparison to gefen family: {compare_stored_face_against_tags(obama_face_indexes[0], ['gefen-family'])}")
    