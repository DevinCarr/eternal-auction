import sqlite3
from reagent import Reagent


class Store:
    def __init__(self, database):
        self.database = database
        self.conn = sqlite3.connect(self.database)
        self.__auctions = AuctionsTable(self)
        self.__downloads = DownloadsTable(self)
        self.__recipes = RecipesTable(self)
        self.__reagents = ReagentsTable(self)
        self.__quantities = QuantitiesTable(self)
        self.__credentials = CredentialsTable(self)
        self.__cache = CacheTable(self)
        self.__initialize()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.conn.close()

    def __initialize(self):
        self.__auctions.create_if_exists()
        self.__downloads.create_if_exists()
        self.__recipes.create_if_exists()
        self.__reagents.create_if_exists()
        self.__quantities.create_if_exists()
        self.__credentials.create_if_exists()
        self.__cache.create_if_exists()

    def add_auctions(self, listings, datetime):
        self.__auctions.insert(listings)
        self.__downloads.insert(datetime)

    def get_last_download(self):
        cur = self.conn.execute(
            'SELECT datetime FROM downloads ORDER BY datetime DESC LIMIT 1')
        datetime = cur.fetchone()
        return datetime[0] if datetime is not None else None

    def get_reagents_price(self, recipe_id):
        datetime = self.get_last_download()
        if datetime is None:
            print('download from auction house first before searching.')
            return None
        cur = self.conn.execute('''
        SELECT q.item_id, r.name, r.craftable, q.quantity, a.price
        FROM quantities q
        INNER JOIN reagents r
            ON q.item_id = r.item_id
            AND recipe_id = ?
        INNER JOIN (
            SELECT * FROM auctions
            WHERE datetime = ?
        ) a ON q.item_id = a.item_id
        ''', (recipe_id, datetime))
        return cur.fetchall()

    def get_price(self, item_id):
        datetime = self.get_last_download()
        if datetime is None:
            print('download from auction house first before searching.')
            return None
        cur = self.conn.execute('''
            SELECT price
            FROM auctions
            WHERE item_id = ? and datetime = ?
            ''', (item_id, datetime))
        return cur.fetchone()

    def get_price_by_name(self, item_name):
        cur = self.conn.execute('''
            SELECT item_id
            FROM reagents
            WHERE name = ?
            ''', (item_name,))
        item_id = cur.fetchone()
        if item_id is None:
            return None
        return self.get_price(item_id[0])

    def get_price_history(self, item_name):
        cur = self.conn.execute('''
            SELECT item_id
            FROM reagents
            WHERE name = ?
            ''', (item_name,))
        item_id = cur.fetchone()
        if item_id is None:
            return None
        cur = self.conn.execute('''
            SELECT *
            FROM auctions
            WHERE item_id = ?
            ''', (item_id[0],))
        return cur.fetchall()

    def add_recipes(self, recipes):
        self.__recipes.insert(recipes)
        for recipe in recipes:
            self.__reagents.upsert(recipe.item_id, recipe.item_name, 1)
            self.__reagents.insert_list(recipe.reagents)
            self.__quantities.insert(recipe.id, recipe.reagents)

    def get_recipe(self, id):
        recipe = None
        cur = self.conn.execute('''
                SELECT r.*, i.name FROM (SELECT *
                FROM recipes
                WHERE item_id = ?) r
                INNER JOIN reagents AS i
                ON r.item_id = i.item_id
            ''', (id,))
        recipe = cur.fetchone()
        if recipe is None:
            cur = self.conn.execute('''
                SELECT r.*, i.name FROM (SELECT *
                FROM recipes
                WHERE name = ?) r
                INNER JOIN reagents AS i
                ON r.item_id = i.item_id
            ''', (id,))
            recipe = cur.fetchone()
        return recipe

    def get_recipe_count(self, profession, skill_tier):
        cur = self.conn.execute(
            'SELECT COUNT(*) FROM recipes WHERE profession = ? AND skilltier = ?', (profession, skill_tier))
        return cur.fetchone()[0]

    def get_all_reagent_ids(self):
        cur = self.conn.execute('SELECT item_id FROM reagents')
        return [i[0] for i in cur.fetchall()]

    def get_all_reagents(self):
        cur = self.conn.execute('SELECT * FROM reagents')
        return cur.fetchall()

    def get_credentials(self):
        return self.__credentials.get()

    def add_or_replace_credentials(self, client_id, client_secret, datetime):
        creds = self.__credentials.get()
        if creds is not None:
            self.__credentials.clear()
        self.__credentials.insert(client_id, client_secret, datetime)

    def clear_credentials(self):
        self.__credentials.clear()

    def get_cache(self):
        return self.__cache.get()

    def update_cache(self, realm_name):
        self.__cache.update(realm_name)


class Table:
    def __init__(self, store):
        self.store = store

    def create_if_exists(self):
        pass


class AuctionsTable(Table):
    def create_if_exists(self):
        self.store.conn.execute('''
        CREATE TABLE IF NOT EXISTS auctions
        (
            item_id TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            datetime TEXT NOT NULL
        )
        ''')
        self.store.conn.commit()

    def insert(self, auctions):
        auctions_insert = [(a.id, a.price, a.quantity, a.datetime)
                           for a in auctions]
        self.store.conn.executemany(
            'INSERT INTO auctions VALUES (?, ?, ?, ?)', auctions_insert)
        self.store.conn.commit()


class DownloadsTable(Table):
    def create_if_exists(self):
        self.store.conn.execute('''
        CREATE TABLE IF NOT EXISTS downloads
        (
            datetime TEXT NOT NULL
        )
        ''')
        self.store.conn.commit()

    def insert(self, datetime):
        self.store.conn.execute(
            'INSERT INTO downloads VALUES (?)', (datetime,))
        self.store.conn.commit()


class RecipesTable(Table):
    def create_if_exists(self):
        self.store.conn.execute('''
        CREATE TABLE IF NOT EXISTS recipes
        (
            recipe_id INTEGER NOT NULL PRIMARY KEY,
            profession INTEGER NOT NULL,
            skilltier INTEGER NOT NULL,
            name TEXT NOT NULL,
            item_id TEXT NOT NULL,
            crafted_quantity INTEGER NOT NULL
        )
        ''')
        self.store.conn.commit()

    def insert(self, recipes):
        recipes_insert = [(r.id, r.profession, r.skill_tier, r.name,
                           r.item_id, r.crafted_quantity) for r in recipes]
        self.store.conn.executemany(
            'INSERT INTO recipes VALUES (?, ?, ?, ?, ?, ?)', recipes_insert)
        self.store.conn.commit()


class ReagentsTable(Table):
    def create_if_exists(self):
        self.store.conn.execute('''
        CREATE TABLE IF NOT EXISTS reagents
        (
            item_id TEXT NOT NULL PRIMARY KEY,
            name TEXT NOT NULL,
            craftable INTEGER NOT NULL
        )
        ''')
        self.store.conn.commit()

    def upsert(self, item_id, name, craftable):
        self.store.conn.execute('''
        INSERT INTO reagents
        VALUES (?, ?, ?)
        ON CONFLICT (item_id)
        DO UPDATE SET craftable = ?
        ''', (item_id, name, craftable, craftable))
        self.store.conn.commit()

    def insert_list(self, items):
        items_insert = [(i.id, i.name, 0) for i in items]
        self.store.conn.executemany(
            'INSERT OR IGNORE INTO reagents VALUES (?, ?, ?)', items_insert)
        self.store.conn.commit()


class QuantitiesTable(Table):
    def create_if_exists(self):
        self.store.conn.execute('''
        CREATE TABLE IF NOT EXISTS quantities
        (
            item_id TEXT NOT NULL,
            recipe_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL
        )
        ''')
        self.store.conn.commit()

    def get(self, recipe_id):
        cur = self.store.conn.execute(
            'SELECT * FROM quantities WHERE recipe_id = ?', recipe_id)
        return cur.fetchall()

    def insert(self, recipe_id, items):
        quantities_insert = [(i.id, recipe_id, i.quantity) for i in items]
        self.store.conn.executemany(
            'INSERT OR IGNORE INTO quantities VALUES (?, ?, ?)', quantities_insert)
        self.store.conn.commit()


class CredentialsTable(Table):
    def create_if_exists(self):
        self.store.conn.execute('''
        CREATE TABLE IF NOT EXISTS credentials
        (
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL,
            datetime TEXT NOT NULL
        )
        ''')
        self.store.conn.commit()

    def get(self):
        cur = self.store.conn.execute('SELECT * FROM credentials')
        return cur.fetchone()

    def insert(self, client_id, client_secret, datetime):
        self.store.conn.execute(
            'INSERT INTO credentials VALUES (?, ?, ?)', (client_id, client_secret, datetime))
        self.store.conn.commit()

    def clear(self):
        self.store.conn.execute('DELETE FROM credentials')
        self.store.conn.commit()


class CacheTable(Table):
    def create_if_exists(self):
        self.store.conn.execute('''
        CREATE TABLE IF NOT EXISTS cache
        (
            realm_name INTEGER NOT NULL
        )
        ''')
        self.store.conn.commit()

    def get(self):
        cur = self.store.conn.execute('SELECT * FROM cache')
        return cur.fetchone()

    def update(self, realm_name):
        self.store.conn.execute('DELETE FROM cache')
        self.store.conn.execute('INSERT INTO cache VALUES (?)', (realm_name,))
        self.store.conn.commit()
