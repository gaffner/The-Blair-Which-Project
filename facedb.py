from typing import Union, NewType, Collection, Optional
import sqlite3
import os.path
import logging
import numpy as np
import io

from facials import FaceData, FaceEncoding, ImageFormat, FaceLocation


DB_PATH = './facedb.db'

"""
DB Structure:

Faces table
- ID: number
- Encoding: str, bytes whatever
- Image: ID foreign key to Images table
- Description: str
- location: (int, int, int, int) (place in the image where the face is)
- Collections?: str - whitespace separated list of collections this face is a member of

Images table
- ID: number, key
- Image Format: URL, local path, or byte stream
- Image data: the URL, path, or byte stream
- Image description
"""

ImageIndex = NewType("ImageIndex", int)
FaceIndex = NewType("FaceIndex", int)


def adapt_nparray(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_nparray(text: bytes):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)

def adapt_imageformat(imageformat: ImageFormat):
    return imageformat.value

def convert_imageformat(text: bytes):
    return ImageFormat(text.decode())

def adapt_facelocation(location: FaceLocation):
    return ','.join(str(l) for l in location.rect())

def convert_facelocation(text: bytes):
    return FaceLocation(*tuple(int(l) for l in text.split(b',')))

def adapt_tags(tags: tuple):
    return ','.join(tags)

def convert_tags(text: bytes):
    return tuple(text.decode().split(','))


sqlite3.register_converter("nparray", convert_nparray)
sqlite3.register_adapter(np.ndarray, adapt_nparray)
sqlite3.register_converter("ImageFormat", convert_imageformat)
sqlite3.register_adapter(ImageFormat, adapt_imageformat)
sqlite3.register_converter("FaceLocation", convert_facelocation)
sqlite3.register_adapter(FaceLocation, adapt_facelocation)
sqlite3.register_converter("Tags", convert_tags)
sqlite3.register_adapter(tuple, adapt_tags)


class FaceDB(object):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.db_conn.execute("PRAGMA foreign_keys = 1")
        self.initialize_tables()
    
    def _create_table_images(self):
        cur = self.db_conn.cursor()
        cur.execute("""
        --sql
        CREATE TABLE IF NOT EXISTS images (
            ID          INTEGER PRIMARY KEY NOT NULL, 
            IMAGE_FMT   ImageFormat         NOT NULL, 
            IMAGE_DATA  TEXT                NOT NULL,
            DESCRIPTION TEXT                NOT NULL
        );
        """)
        self.db_conn.commit()
        cur.close()

    def _create_table_faces(self):
        cur = self.db_conn.cursor()
        cur.execute("""
        --sql
        CREATE TABLE IF NOT EXISTS faces (
            ID          INTEGER PRIMARY KEY NOT NULL, 
            ENCODING    nparray             NOT NULL,
            IMAGE       INTEGER,
            LOCATION    FaceLocation        NOT NULL,
            DESCRIPTION TEXT                NOT NULL,
            TAGS        Tags                NOT NULL,
            FOREIGN KEY (IMAGE)
                REFERENCES images (ID)
        );
        """)
        self.db_conn.commit()
        cur.close()
        
    def initialize_tables(self):
        self._create_table_images()
        self._create_table_faces()
    
    def add_image(self, image_format: ImageFormat, image_data: Union[str, bytes], description: str = "") -> ImageIndex:
        cur = self.db_conn.cursor()
        cur.execute("""
        --sql
        INSERT INTO images (IMAGE_FMT,IMAGE_DATA,DESCRIPTION) VALUES (?,?,?);
        """,
        (image_format, image_data, description))
        index = cur.lastrowid
        self.db_conn.commit()
        cur.close()
        return index
    
    def add_face(self, face_data: FaceData, image_index: ImageIndex = None, description: str = "", tags: Collection[str] = ()) -> FaceIndex:
        cur = self.db_conn.cursor()
        cur.execute("""
        --sql
        INSERT INTO faces (ENCODING,IMAGE,location,DESCRIPTION,TAGS) VALUES (?,?,?,?,?);
        """,
        (face_data.encoding, image_index, face_data.location, description, tags))
        index = cur.lastrowid
        self.db_conn.commit()
        cur.close()
        return index
    
    def add_faces_from_image(self, image_format: ImageFormat, image_data: Union[str, bytes], description: str = "", tags: Collection[str] = ()) -> list[FaceIndex]:
        faces = FaceData.extract_from_image(image_format, image_data)
        if not faces:
            return []
        
        image_index = self.add_image(image_format, image_data, description)
        face_indexes = [self.add_face(face_data, image_index, description, tags) for face_data in faces]
        
        return face_indexes
        
    
    def get_faces_with_tags(self, tags: Collection[str]) -> FaceData:
        pass
    
    def compare_face_to_tags():
        pass



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    facedb = FaceDB(DB_PATH)
    
    # Adding faces from local image
    face_indexes = facedb.add_faces_from_image(ImageFormat.LOCAL_PATH, '/home/amit/Downloads/group.jpg', description='group Image', tags=('hell', 'fuck'))
    print(face_indexes)
    
    print(list(facedb.db_conn.execute("""
    --sql
    SELECT faces.ID, IMAGE, IMAGE_DATA, faces.DESCRIPTION, FAces.TAGS FROM FACES LEFT OUTER JOIN images ON IMAGE = images.ID
    ;
    """)))