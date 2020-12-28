import sqlite3
from enum import Enum


class Store:
    def __init__(self, database):
        self.conn = None
        self.database = database
        self.auctions = AuctionsTable(self)
        self.__recipes = RecipesTable(self)
        self.__reagents = ReagentsTable(self)
        self.__quantities = QuantitiesTable(self)

    def __enter__(self):
        self.conn = sqlite3.connect(self.database)
        self.__initialize()
        return self

    def __exit__(self, type, value, traceback):
        self.conn.close()

    def __initialize(self):
        self.auctions.create_if_exists()
        self.__recipes.create_if_exists()
        self.__reagents.create_if_exists()
        self.__quantities.create_if_exists()

    def add_recipes(self, recipes):
        self.__recipes.insert(recipes)
        for recipe in recipes:
            self.__reagents.insert(recipe.reagents)
            self.__quantities.insert(recipe.id, recipe.reagents)

    def get_reagents(self, recipe_name):
        cur = self.conn.execute('SELECT recipe_id FROM recipes WHERE name = ?', recipe_name)
        recipe_id = cur.fetchone()
        if recipe_id is None:
            return None
        cur = self.conn.execute('''
            SELECT q.item_id, i.name, q.quantity
            FROM quantities q
            INNER JOIN items i
                ON q.item_id = i.item_id
                AND recipe_id = ?
            ''', recipe_id)
        return cur.fetchall()
            
    def list_recipes(self, profession, skilltier):
        cur = self.conn.execute('SELECT * FROM recipes WHERE profession = ? AND skilltier = ?', (profession, skilltier))
        return cur.fetchall()

    def get_all_reagents(self):
        cur = self.conn.execute('SELECT item_id FROM reagents')
        return cur.fetchall()


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
            id INTEGER NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            date TEXT NOT NULL
        )
        ''')
        self.store.conn.commit()

    def insert(self, auctions):
        auctions_insert = [(a.id, a.price, a.quantity, a.datetime)
                           for a in auctions]
        self.store.conn.executemany('INSERT INTO auctions VALUES (?, ?, ?, ?)', auctions_insert)
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
            crafted_quantity INTEGER NOT NULL
        )
        ''')
        self.store.conn.commit()

    def insert(self, recipes):
        recipes_insert = [(r.id, r.profession, r.skilltier,
                           r.name, r.crafted_quantity) for r in recipes]
        self.store.conn.executemany(
            'INSERT INTO recipes VALUES (?, ?, ?, ?, ?)', recipes_insert)
        self.store.conn.commit()


class ReagentsTable(Table):
    def create_if_exists(self):
        self.store.conn.execute('''
        CREATE TABLE IF NOT EXISTS reagents
        (
            item_id INTEGER NOT NULL PRIMARY KEY,
            name TEXT NOT NULL,
            craftable INTEGER NOT NULL
        )
        ''')
        self.store.conn.commit()

    def insert(self, items):
        items_insert = [(i.id, i.name, 1) for i in items]
        self.store.conn.executemany(
            'INSERT OR IGNORE INTO reagents VALUES (?, ?, ?)', items_insert)
        self.store.conn.commit()


class QuantitiesTable(Table):
    def create_if_exists(self):
        self.store.conn.execute('''
        CREATE TABLE IF NOT EXISTS quantities
        (
            item_id INTEGER NOT NULL,
            recipe_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL
        )
        ''')
        self.store.conn.commit()

    def get(self, recipe_id):
        cur = self.store.conn.execute('SELECT * FROM quantities WHERE recipe_id = ?', recipe_id)
        return cur.fetchall()

    def insert(self, recipe_id, items):
        quantities_insert = [(i.id, recipe_id, i.quantity) for i in items]
        self.store.conn.executemany(
            'INSERT OR IGNORE INTO quantities VALUES (?, ?, ?)', quantities_insert)
        self.store.conn.commit()
