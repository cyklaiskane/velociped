from typing import Any, Type, Optional
import logging
import shapely.geometry
import shapely.wkb
from asyncpg import Connection
from databases import Database
from shapely.geometry.base import BaseGeometry

from api.config import POSTGRES_DSN


async def init_con(con: Connection) -> None:
    def encode_geometry(geometry: Any) -> bytes:
        if not hasattr(geometry, '__geo_interface'):
            raise TypeError(f'{geometry} does not conform to the geo interface')
        shape = shapely.geometry.asShape(geometry)
        return shapely.wkb.dumps(shape)

    def decode_geometry(wkb: bytes) -> Optional[Type[BaseGeometry]]:
        try:
            return shapely.wkb.loads(wkb)
        except Exception as e:
            logging.warn(e)
            logging.debug(wkb)
            return None

    await con.set_type_codec(
        'geometry', encoder=encode_geometry, decoder=decode_geometry, format='binary',
    )


db = Database(POSTGRES_DSN, init=init_con)
