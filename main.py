#!/usr/bin/python3
import argparse
from auction import Auction
import datetime
import itertools
from reagent import Reagent

from authlib.integrations.requests_client import OAuth2Session

from battlenet import BNetClient
from recipe import Recipe
from store import Store

# Dethecus: 81, Connected-Realm: 154


def download(args):
    client = BNetClient(args.client_id, args.client_secret)
    with Store(args.store) as db:
        response = client.get_auction(args.realm)
        auctions = response['auctions']
        items = {}
        search_items = set(db.get_all_reagents())
        for auction in auctions:
            id = auction['item']['id']
            if str(id) in search_items:
                price = auction['unit_price']
                quantity = auction['quantity']
                if type(price) is int and type(quantity) is int:
                    price = round(price // 10000)  # round down to gold
                    if id not in items:
                        items[id] = {
                            'id': id,
                            'price': price,
                            'quantity': quantity
                        }
                    else:
                        items[id]['quantity'] += quantity
                        existing_price = items[id]['price']
                        if price < existing_price:
                            items[id]['price'] = price
        listings = [Auction(item['id'], item['quantity'], item['price'],
                            datetime.datetime.utcnow()) for (k, item) in items.items()]
        db.auctions.insert(listings)


def get_recipe(client, recipe):
    recipe_response = client.get_recipe(recipe.id)
    recipe.name = recipe_response['name']
    recipe.crafted_quantity = int(recipe_response['crafted_quantity']['value'])
    recipe.reagents = [Reagent(r['reagent']['id'], r['reagent']
                               ['name'], int(r['quantity'])) for r in recipe_response['reagents']]


def fetch_recipes(args, profession=171, skill_tier=2750):
    with Store(args.store) as db:
        cursor = db.recipes.get(profession, skill_tier)
        recipe = cursor.fetchone()
        if recipe is not None:
            return

        client = BNetClient(args.client_id, args.client_secret)
        response = client.get_recipes(profession, skill_tier)
        categories = response['categories']
        recipes = [category['recipes'] for category in categories]
        recipes = list(itertools.chain(*recipes))
        recipes = [Recipe(recipe['id'], profession, skill_tier, None, None)
                   for recipe in recipes]
        for recipe in recipes:
            get_recipe(client, recipe)
        db.add_recipes(recipes)


def list_recipes(args, profession=171, skill_tier=2750):
    with Store(args.store) as db:
        recipes = db.list_recipes(profession, skill_tier)
        recipes = [Recipe(*r) for r in recipes]
        for recipe in recipes:
            print(recipe.name)


def cost_recipe(args):
    with Store(args.store) as db:
        reagents = db.get_reagents(args.recipename)
        if reagents is None:
            print(f'Recipe with recipe_id: {args.recipename} not found.')
            return
        reagents = [Reagent(*r) for r in reagents]
        for reagent in reagents:
            print(f'{reagent.quantity} {reagent.name}')

def add_client_arguments(subparser):
    subparser.add_argument('--client-id', required=True,
                           type=str, help='battle.net API client id')
    subparser.add_argument('--client-secret', required=True,
                           type=str, help='battle.net API client secret')
    subparser.add_argument('--store', default='auctions.db',
                           type=str, help='sqlite database location')


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_download = subparsers.add_parser(
        'download', help='download the latest data')
    add_client_arguments(parser_download)
    parser_download.add_argument(
        '--realm', type=int, default='154', help='wow connected-realm id')
    parser_download.add_argument(
        '--items', type=str, required=True,
        action='extend', nargs='+', help='item ids to filter on')
    parser_download.set_defaults(func=download)

    parser_recipes = subparsers.add_parser(
        'recipe', help='show the latest recipes')

    recipe_subparsers = parser_recipes.add_subparsers()
    parser_recipes_fetch = recipe_subparsers.add_parser(
        'fetch', help='fetch recipes')
    add_client_arguments(parser_recipes_fetch)
    parser_recipes_fetch.set_defaults(func=fetch_recipes)
    parser_recipes_list = recipe_subparsers.add_parser(
        'list', help='list recipes')
    add_client_arguments(parser_recipes_list)
    parser_recipes_list.set_defaults(func=list_recipes)
    parser_recipes_cost = recipe_subparsers.add_parser(
        'cost', help='find fair market value for recipe')
    add_client_arguments(parser_recipes_cost)
    parser_recipes_cost.add_argument('recipename', type=str, nargs=1)
    parser_recipes_cost.set_defaults(func=cost_recipe)
    

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
