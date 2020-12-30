#!/usr/bin/python3
import argparse
import datetime
import itertools
import random

from auction import Auction
from battlenet import BNetClient
from item import Item
from reagent import Reagent
from recipe import Recipe
from store import Store

# Dethecus: 81, Connected-Realm: 154


def download(args):
    client = BNetClient(args.client_id, args.client_secret)
    with Store(args.store) as db:
        response = client.get_auction(args.realm)
        auctions = response['auctions']
        items = {}
        search_items = set(db.get_all_reagent_ids())
        for auction in auctions:
            id = auction['item']['id']
            if int(id) in search_items:
                price = auction['unit_price'] if 'unit_price' in auction else auction['buyout']
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
        if len(items.items()) <= 0:
            print('no items found in reagents to record')
            return
        fetch_time = datetime.datetime.utcnow()
        listings = [Auction(item['id'], item['quantity'], item['price'],
                            fetch_time) for (k, item) in items.items()]
        db.insert_auctions(listings, fetch_time)


def get_recipe(client, recipe):
    recipe_response = client.get_recipe(recipe.id)
    recipe.item_id = recipe_response['crafted_item']['id']
    recipe.name = recipe_response['name']
    recipe.crafted_quantity = int(recipe_response['crafted_quantity']['value'])
    recipe.reagents = [Reagent(r['reagent']['id'], r['reagent']
                               ['name'], 0, int(r['quantity'])) for r in recipe_response['reagents']]


def fetch_recipes(args, profession=171, skill_tier=2750):
    with Store(args.store) as db:
        client = BNetClient(args.client_id, args.client_secret)
        response = client.get_recipes(profession, skill_tier)
        categories = response['categories']
        recipes = [category['recipes'] for category in categories]
        recipes = list(itertools.chain(*recipes))
        recipes = [Recipe(recipe['id'], profession, skill_tier, None, None, None)
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


def cost_recipe(db, recipe_id):
    recipe = db.get_recipe(recipe_id)
    if recipe is None:
        print(f'Recipe with recipe name: {recipe_id} not found.')
        return
    recipe = Recipe(*recipe)
    recipe_price = db.get_price(recipe.item_id)
    recipe_price = recipe_price[0] if recipe_price is not None else None
    reagents = db.get_reagents_price(recipe.id)
    reagents = [Reagent(*r) for r in reagents]
    reagents_basic = [(Item(r.id, r.name, price=r.price), r.quantity)
                      for r in reagents if r.craftable == 0]
    reagents_craft = [(cost_recipe(db, r.name), r.quantity)
                      for r in reagents if r.craftable == 1]
    return Item(recipe.item_id, recipe.name, price=recipe_price, recipe=reagents_basic + reagents_craft)


def walk_recipe(item, depth=0):
    t = '\t' * depth
    for (i, quantity) in item.base_items:
        print(f'{t}({quantity} {i.name} {i.price}g)')
    for (i, quantity) in item.craft_items:
        print(f'{t}({quantity} {i.name} @ {i.price}g)')
        walk_recipe(i, depth+1)


def cost_recipe_args(args):
    with Store(args.store) as db:
        recipe = cost_recipe(db, args.recipename[0])
        print('Recipe:')
        walk_recipe(recipe)
        items = recipe.selection()
        print('Cost Breakdown:')
        print('gold\tamount\treagent')
        for (item, quantity) in items:
            # [(stone, 2), (herb2, 2)]
            print(f'{item.price * quantity}\t{quantity}\t{item.name}')
        print('================' + '=' *
              max([len(i.name) for (i, q) in items]))
        print(f'{recipe.cost()} g')


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
    parser_recipes_cost.set_defaults(func=cost_recipe_args)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
