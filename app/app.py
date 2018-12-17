from contextlib import contextmanager
import sys
import json
from flask import Flask
from flask import Response
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import psycopg2
import yaml
import hvac

class Config:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self.vault_client = self._vault_client()
        self.set_vault_db()

    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as stream:
                try:
                    return yaml.load(stream)
                except yaml.YAMLError as exc:
                    sys.exit(exc)
        except FileNotFoundError:
            sys.exit("No such file or directory: '{}'".format(config_path))
        except:
            sys.exit("General error while opening config file: '{}'".format(config_path))

    def _vault_client(self):
        def auth_setup(auth_token):
            url = 'http://localhost:8200'
            client = hvac.Client(url=url, token=auth_token)
            auth_result = client.write('auth/approle/role/app/secret-id')
            assert client.is_authenticated()
            return auth_result['data']['secret_id']

        def auth_role(role_id, role_token):
            url = 'http://localhost:8200'
            client2 = hvac.Client(url=url)
            client2.token = client2.auth_approle(role_id, role_token)['auth']['client_token']
            assert client2.is_authenticated()
            return client2

        auth_token = self.config['vault']['auth_token']
        role_id = self.config['vault']['role_id']
        secret_id = auth_setup(auth_token)
        return auth_role(role_id, secret_id)

    def set_vault_db(self):
        password = self.vault_client.read('secret/data/app')['data']['data']['database_pass']
        self.config['db']['password'] = password

class BuildingsApi(Flask):
    def __init__(self, config):
        super().__init__(__name__)
        self.app_config = config
        # Register the routes and their handlers
        self.route('/')(self.index)
        self.route('/buildings')(self.buildings)
        self.route('/buildings/<building_id>')(self.building_get)
        try:
            self.db_pool = ThreadedConnectionPool(1, 20, **self.app_config['db'])
        except:
            # This a bad way of handling connection errors, but it's good enough for this project
            sys.exit("Failed to connect to database.")

    def run(self):
        super().run(**self.app_config['web'])

    @contextmanager
    def _get_db_connection(self):
        try:
            connection = self.db_pool.getconn()
            yield connection
        finally:
            self.db_pool.putconn(connection)

    @contextmanager
    def _get_db_cursor(self, commit=False):
        with self._get_db_connection() as connection:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            try:
                yield cursor
                if commit:
                    connection.commit()
            finally:
                cursor.close()

    def index(self):
        context = {'message': 'Hello world!'}
        return Response(json.dumps(context), mimetype='text/json')

    def buildings(self):
        with self._get_db_cursor() as cursor:
            buildings = db_buildings_all(cursor)
            return Response(str(buildings), mimetype='text/json')
        return Response("Database error", status_code=500)

    def building_get(self, building_id):
        with self._get_db_cursor() as cursor:
            building = db_buildings_get(cursor, building_id)
            return Response(str(building), mimetype='text/json')
        return Response("Database error", status_code=500)

def db_buildings_all(cursor):
    """ Gets all buildings from the database
    """
    cursor.execute("SELECT id, name, height, city, country FROM buildings")
    return cursor.fetchall()

def db_buildings_get(cursor, building_id):
    """ Gets a specific building from the database
    """
    cursor.execute("SELECT id, name, height, city, country FROM buildings WHERE id = {}".format(building_id))
    return cursor.fetchone()

def main():
    """ Main entrypoint for Building API
    """
    config_path = sys.argv[1]
    config = Config(config_path)

    app = BuildingsApi(config.config)
    app.run()
