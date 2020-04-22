import shapely.geometry
import shapely.wkb

from fastapi import Request


async def get_db(request: Request):
    async with request.app.db.acquire() as con:
        def encode_geometry(geometry):
            if not hasattr(geometry, '__geo_interface'):
                raise TypeError(f'{geometry} does not conform to the '
                                'geo intergace')
            shape = shapely.geometry.asShape(geometry)
            return shapely.wkb.dumps(shape)

        def decode_geometry(wkb):
            return shapely.wkb.loads(wkb)

        await con.set_type_codec(
            'geometry',
            encoder=encode_geometry,
            decoder=decode_geometry,
            format='binary'
        )
        yield con
