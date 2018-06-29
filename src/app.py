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


TABLES = {
    'ecuador_provincial': {
        'id_column': 'gid',
        'name_column': 'dpa_despro'
    },
    'ecuador_cantonal': {
        'id_column': 'gid',
        'name_column': 'dpa_despro'
    },
    'ecuador_parroquial': {
        'id_column': 'gid',
        'name_column': 'dpa_despro'
    }
}


def tile_ul(x, y, z):
    n = 2.0 ** z
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return lon_deg, lat_deg


def get_tile(table, z, x, y):
    xmin, ymin = tile_ul(x, y, z)
    xmax, ymax = tile_ul(x + 1, y + 1, z)

    tile = None

    tilefolder = "{}/{}/{}/{}".format(CACHE_DIR, table, z, x)
    tilepath = "{}/{}.pbf".format(tilefolder, y)
    if not os.path.exists(tilepath):
        conn = psycopg2.connect('dbname={0} user={1} password={2} host={3}'.format(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST))
        cur = conn.cursor()

        id_column = TABLES[table]['id_column']
        name_column = TABLES[table]['name_column']

        query = "SELECT ST_AsMVT(tile) FROM " \
                "(SELECT {id_column}, {name_column}, ST_AsMVTGeom(geom, ST_Makebox2d(ST_transform(ST_SetSrid(ST_MakePoint(%s,%s),4326),3857),ST_transform(ST_SetSrid(ST_MakePoint(%s,%s),4326),3857)), 4096, 0, false)" \
                " AS geom FROM {table}) AS tile".format(table=table, id_column=id_column, name_column=name_column)
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


def get_tile_geojson(table):
    conn = psycopg2.connect('dbname={0} user={1} password={2} host={3}'.format(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST))
    cur = conn.cursor()

    id_column = TABLES[table]['id_column']

    # query = "SELECT jsonb_build_object('type', 'FeatureCollection', 'features', jsonb_agg(features)) " \
    #         "FROM (SELECT jsonb_build_object(" \
    #         " 'type', 'Feature', 'id', {id_column}," \
    #         " 'geometry', ST_AsGeoJSON(geom)," \
    #         " 'properties', to_jsonb(inputs) - '{id_column}' - 'geom'" \
    #         ") FROM (SELECT * FROM {table}) inputs) features;".format(table=GEO_TABLE, id_column=ID_COLUMN)
    query = "SELECT ST_AsGeoJSON(geom) FROM {table}".format(table=table, id_column=id_column)
    cur.execute(query)
    row = cur.fetchone()
    features = "["
    while row:
        features += str(row[0]) + ','
        row = cur.fetchone()
    features = features[:-1] + "]"
    json = '{ "type": "FeatureCollection", "features": ' + features + ' }'
    file = "{}/{}/{}".format(CACHE_DIR, table, 'geo_json.json')
    with open(file, 'wb') as f:
        f.write(json)
        f.close()
    return json


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/tiles')
@app.route('/tiles/<string:table>/<int:z>/<int:x>/<int:y>', methods=['GET'])
def tiles(table='ecuador_provincial', z=0, x=0, y=0):
    tile = get_tile(table, z, x, y)
    response = make_response(tile)
    response.headers['Content-Type'] = "application/octet-stream"
    return response


@app.route('/geo_json')
@app.route('/geo_json/<string:table>')
def geo_json(table='ecuador_provincial'):
    tile = get_tile_geojson(table)
    response = make_response(tile)
    response.headers['Content-Type'] = "application/json"
    return response


if __name__ == "__main__":
    if 'SERVER' in os.environ:
        app.run(host="0.0.0.0", port=80)
    else:
        app.run(host="0.0.0.0", port=5000)
