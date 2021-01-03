from datetime import datetime
import unittest

from auction import Auction
from constants import professions, vendor_reagents, unique_recipe_format
from item import Item
from reagent import Reagent
from recipe import Recipe
from store import Store

utc_now = datetime.utcnow()

listings = [
    Auction('1', 1, 1, utc_now),
    Auction('2', 2, 2, utc_now),
    Auction('3', 3, 3, utc_now)
]

recipe = Recipe(1, 1, 1, 'test recipe', '1', 1, 'item name')
recipe.reagents = [
    Reagent('2', 'reagent 1', 0, 2, 2),
    Reagent('3', 'reagent 2', 0, 3, 3)
]

def seed_db(db):
        db.add_recipes([recipe])
        db.add_auctions(listings, utc_now)

class TestStore(unittest.TestCase):
    def setUp(self):
        self.db = Store(':memory:')
        self.db.add_recipes([recipe])
        self.db.add_auctions(listings, utc_now)

    def test_get_last_download(self):
        last_download = self.db.get_last_download()
        self.assertEqual(last_download, str(utc_now))

    def test_get_reagents_price(self):
        reagents = self.db.get_reagents_price(recipe.id)
        self.assertEqual(len(reagents), 2)
        reagents = [(Reagent(*r), r1) for r in reagents for r1 in recipe.reagents if r1.id == r[0]]
        self.assertEqual(len(reagents), 2)
        for (reagent, expected_reagent) in reagents:
            self.assertEqual(reagent.name, expected_reagent.name)
            self.assertEqual(reagent.price, expected_reagent.price)

    def test_get_price(self):
        self.assertEqual(self.db.get_price('1')[0], 1)
        self.assertEqual(self.db.get_price_by_name('reagent 1')[0], 2)

    def test_get_recipe(self):
        recipe = Recipe(*self.db.get_recipe(1))
        self.assertEqual(recipe.id, 1)
        self.assertEqual(recipe.name, 'test recipe')
        recipe = Recipe(*self.db.get_recipe('test recipe'))
        self.assertEqual(recipe.id, 1)
        self.assertEqual(recipe.name, 'test recipe')

    def test_get_recipe_count(self):
        count = self.db.get_recipe_count(1, 1)
        self.assertEqual(count, 1)

    def test_get_all_reagent_ids(self):
        reagent_ids = self.db.get_all_reagent_ids()
        self.assertEqual(len(reagent_ids), 3)
        self.assertListEqual(reagent_ids, ['1', '2', '3'])
