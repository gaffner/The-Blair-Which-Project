from typing import Union, NewType, Collection, Iterable, Any, Optional
import sqlite3
import numpy as np
import io

from facials import FaceData, FaceEncoding, ImageFormat, FaceLocation


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
# TODO: Maybe make tags a unique type so we don't have to set an adapter for ALL tuples?
sqlite3.register_adapter(tuple, adapt_tags)


class FaceDB(object):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.db_conn.execute("PRAGMA foreign_keys = 1")
        self.initialize_tables()
        
    def query(self, sql, parameters: Collection[Any] = None):
        execute_args = (sql, parameters) if parameters else (sql, )
        return self.db_conn.execute(*execute_args)
    
    def _create_table_images(self):
        cur = self.db_conn.cursor()
        cur.execute("""
        --sql
        CREATE TABLE IF NOT EXISTS images (
            ID              INTEGER PRIMARY KEY NOT NULL, 
            IMAGE_FORMAT    ImageFormat         NOT NULL, 
            IMAGE_DATA      TEXT                NOT NULL,
            DESCRIPTION     TEXT                NOT NULL
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
    
    def add_image(self, image_format: ImageFormat, image_data: Union[str, bytes],
                  description: str = "") -> ImageIndex:
        cur = self.db_conn.cursor()
        cur.execute("""
        --sql
        INSERT INTO images (IMAGE_FORMAT,IMAGE_DATA,DESCRIPTION) VALUES (?,?,?);
        """,
        (image_format, image_data, description))
        index = cur.lastrowid
        self.db_conn.commit()
        cur.close()
        return index
    
    def add_face(self, face_data: FaceData, image_index: ImageIndex = None,
                 description: str = "", tags: Collection[str] = ()) -> FaceIndex:
        cur = self.db_conn.cursor()
        cur.execute("""
        --sql
        INSERT INTO faces (ENCODING,IMAGE,location,DESCRIPTION,TAGS) VALUES (?,?,?,?,?);
        """,
        (face_data.encoding, image_index, face_data.location, description, tuple(tags)))
        index = cur.lastrowid
        self.db_conn.commit()
        cur.close()
        return index
    
    def add_faces_from_image(self, image_format: ImageFormat, image_data: Union[str, bytes],
                             description: str = "", tags: Collection[str] = ()) -> list[FaceIndex]:
        faces = FaceData.extract_from_image(image_format, image_data)
        if not faces:
            return []
        
        image_index = self.add_image(image_format, image_data, description)
        face_indexes = [self.add_face(face_data, image_index, description, tags) for face_data in faces]
        
        return face_indexes
        
    
    def get_faces_by_tags(self, tags: Collection[str]) -> Iterable[FaceData]:
        matches = list(
            self.query(f"""
            --sql
            SELECT ID, IMAGE, LOCATION, ENCODING, DESCRIPTION, TAGS
              FROM faces
             WHERE {' OR '.join(f"TAGS LIKE '%{tag}%'" for tag in tags)};
            """)
        )
        
        return (FaceData(image_format=ImageFormat.ID, image_data=face[1], location=face[2],
                        encoding=face[3], description=face[4], tags=face[5], id=face[0])
                for face in matches)

    def get_face_by_id(self, id: FaceIndex) -> Optional[FaceData]:
        matches = list(
            self.query("""
            --sql
            SELECT IMAGE, LOCATION, ENCODING, DESCRIPTION, TAGS
              FROM faces
             WHERE ID = (?);
            """, (id, ))
        )

        if not matches:
            return None
        
        face = matches[0]
        return FaceData(image_format=ImageFormat.ID, image_data=face[0], location=face[1],
                        encoding=face[2], description=face[3], tags=face[4])
    
    def get_all_tags(self) -> list[str]:
        # Tags are stored as comma separated strings, so we'll have to perform the `unique`ing operation in python code.
        unique_tags_combinations = [row[0] for row in self.query("""
        --sql
        SELECT DISTINCT TAGS
          FROM faces;
        """)]
        
        unique_tags = list({tag
                            for tags_combination in unique_tags_combinations
                            for tag in tags_combination})
        
        return unique_tags
         


if __name__ == '__main__':    
    facedb = FaceDB('./facedb.db')
    
    # Adding faces from an image byte stream
    with open('/home/amit/Downloads/group.jpg', 'rb') as f:
        group = f.read()

    face_indexes = facedb.add_faces_from_image(ImageFormat.BYTE_STREAM, group, description='group Image', tags=('hell', 'fuck'))
    print(face_indexes)
    
    # fetching faces by tags
    face_group = facedb.get_faces_by_tags(['hell'])
    
    # fetching single face by ID
    some_face = facedb.get_face_by_id(10)
    
    # comparing
    print(some_face.compare(list(face_group)))