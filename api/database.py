import logging
from typing import Any, Optional, Type

import shapely.geometry
import shapely.wkb
from asyncpg import Connection, connect
from asyncpg.exceptions import UndefinedFunctionError
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


async def init_extensions() -> None:
    con = await connect(str(POSTGRES_DSN))
    checks = [
        ('SELECT version() as version', None),
        ('SELECT postgis_version() as version', 'CREATE EXTENSION postgis'),
        ('SELECT pgr_version() as version', 'CREATE EXTENSION pgrouting'),
    ]
    for check_sql, init_sql in checks:
        try:
            result = await con.fetchval(query=check_sql)
            logging.info(result)
        except UndefinedFunctionError:
            await con.execute(init_sql)


db = Database(POSTGRES_DSN, init=init_con)
