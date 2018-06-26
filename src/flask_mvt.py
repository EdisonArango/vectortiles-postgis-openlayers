# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import shutil
import math
import psycopg2

from flask import Flask, render_template, make_response

templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=templates_dir)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, 'cache')

DB_HOST = 'db'  # Docker db host
DB_USER = 'geo'
DB_PASSWORD = 'geo'
DB_NAME = 'geo24'

GEO_TABLE = 'regiones_chile'
ID_COLUMN = 'gid'
NAME_COLUMN = 'nombre'

def tile_ul(x, y, z):
    n = 2.0 ** z
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return lon_deg, lat_deg


def get_tile(z, x, y):
    xmin, ymin = tile_ul(x, y, z)
    xmax, ymax = tile_ul(x + 1, y + 1, z)

    tile = None

    tilefolder = "{}/{}/{}".format(CACHE_DIR, z, x)
    tilepath = "{}/{}.pbf".format(tilefolder, y)
    if not os.path.exists(tilepath):
        conn = psycopg2.connect('dbname={0} user={1} password={2} host={3}'.format(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST))
        cur = conn.cursor()

        query = "SELECT ST_AsMVT(tile) FROM " \
                "(SELECT {id_column}, {name_column}, ST_AsMVTGeom(geom, ST_Makebox2d(ST_transform(ST_SetSrid(ST_MakePoint(%s,%s),4326),3857),ST_transform(ST_SetSrid(ST_MakePoint(%s,%s),4326),3857)), 4096, 0, false)" \
                " AS geom FROM {table}) AS tile".format(table=GEO_TABLE, id_column=ID_COLUMN, name_column=NAME_COLUMN)
        cur.execute(query, (xmin, ymin, xmax, ymax))
        tile = str(cur.fetchone()[0])

        if not os.path.exists(tilefolder):
            os.makedirs(tilefolder)

        with open(tilepath, 'wb') as f:
            f.write(tile)
            f.close()

        cur.close()
        conn.close()
    else:
        tile = open(tilepath, 'rb').read()

    return tile


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/tiles')
@app.route('/tiles/<int:z>/<int:x>/<int:y>', methods=['GET'])
def tiles(z=0, x=0, y=0):
    tile = get_tile(z, x, y)
    response = make_response(tile)
    response.headers['Content-Type'] = "application/octet-stream"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
