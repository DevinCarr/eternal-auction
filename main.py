#!/usr/bin/python3
import argparse
import itertools
from datetime import datetime, timedelta

from auction import Auction
from battlenet import BNetClient
from item import Item
from reagent import Reagent
from recipe import Recipe
from store import Store
from vendor_reagents import vendor_reagents

# Dethecus: 81, Connected-Realm: 154

professions = [
    # 164, # Blacksmithing
    (165, 2758), # Leatherworking
    (171, 2750), # Alchemy
    (333, 2753) # Enchanting
]


def download_listings(db, client_id, client_secret, realm=154):
    # Check to see when the latest download of the auction house before downloading again
    # The auction house only updates about every hour via the battle.net API
    last_download = db.get_last_download()
    if last_download is not None and datetime.fromisoformat(last_download) + timedelta(hours=1) > datetime.utcnow():
        return
    client = BNetClient(client_id, client_secret)
    response = client.get_auction(realm)
    auctions = response['auctions']
    items = {}
    search_items = set(db.get_all_reagent_ids())
    for auction in auctions:
        id = auction['item']['id']
        if int(id) in vendor_reagents:
            items[id] = {
                'id': id,
                'price': vendor_reagents[id],
                'quantity': -1
            }
        elif int(id) in search_items:
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
    fetch_time = datetime.utcnow()
    listings = [Auction(item['id'], item['quantity'], item['price'],
                        fetch_time) for (k, item) in items.items()]
    db.insert_auctions(listings, fetch_time)


def get_recipe(client, profession_id, skill_tier, recipe_id):
    recipe_response = client.get_recipe(recipe_id)
    try:
        if 'crafted_item' not in recipe_response:
            return None
        recipe = Recipe(recipe_id, profession_id, skill_tier, None, None, None)
        recipe.item_id = recipe_response['crafted_item']['id']
        recipe.name = recipe_response['name']
        recipe.crafted_quantity = int(recipe_response['crafted_quantity']['value'])
        recipe.reagents = [Reagent(r['reagent']['id'], r['reagent']
                                ['name'], 0, int(r['quantity']), 0) for r in recipe_response['reagents']]
        return recipe
    except:
        print('Error parsing recipe: ', recipe_id)



def fetch_recipes(db, client_id, client_secret, profession_id, skill_tier):
    # Fetch recipes only if not already cached
    recipe_count = db.recipe_count(profession_id, skill_tier)
    if recipe_count > 0:
        return
    client = BNetClient(client_id, client_secret)
    response = client.get_recipes(profession_id, skill_tier)
    categories = response['categories']
    recipes = [category['recipes'] for category in categories]
    recipes = list(itertools.chain(*recipes))
    recipes = [get_recipe(client, profession_id, skill_tier, recipe['id'])
               for recipe in recipes]
    recipes = [r for r in recipes if r is not None]
    db.add_recipes(recipes)


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
    reagents_craft = [(cost_recipe(db, r.id), r.quantity)
                      for r in reagents if r.craftable == 1]
    return Item(recipe.item_id, recipe.item_name, price=recipe_price, recipe=reagents_basic + reagents_craft)


def walk_recipe(item, depth=0):
    t = '\t' * depth
    for (i, quantity) in item.base_items:
        print(f'{t}∟>({quantity} {i.name} @ {i.price}g)')
    for (i, quantity) in item.craft_items:
        print(f'{t}∟>({quantity} {i.name} @ {i.price}g)')
        walk_recipe(i, depth+1)


def cost_recipe_args(args):
    with Store(args.store) as db:
        # Fetch recipes/reagents
        for (profession_id, skill_tier) in professions:
            fetch_recipes(db, args.client_id, args.client_secret, profession_id, skill_tier)
        # Download listings from auction house
        download_listings(db, args.client_id, args.client_secret, args.realm)
        # Cost the recipe
        recipe = cost_recipe(db, args.recipename[0])
        if not args.cost:
            print(f'\n{recipe.name} @ {recipe.price}g:')
            walk_recipe(recipe)
            items = recipe.selection()
            print('\nCost Breakdown:')
            print('gold\tamount\treagent')
            for (item, quantity) in items:
                print(f'{item.price * quantity}\t{quantity}\t{item.name}')
            print('================' + '=' *
                  max([len(i.name) for (i, q) in items]))
        print(f'{recipe.cost()} g')


def add_client_arguments(subparser):
    subparser.add_argument('--client-id', required=True,
                           type=str, help='battle.net API client id')
    subparser.add_argument('--client-secret', required=True,
                           type=str, help='battle.net API client secret')
    subparser.add_argument('--store', default='eternal.db',
                           type=str, help='sqlite database location')


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_recipes = subparsers.add_parser(
        'recipe', help='show the latest recipes')

    recipe_subparsers = parser_recipes.add_subparsers()
    parser_recipes_cost = recipe_subparsers.add_parser(
        'cost', help='find fair market value for recipe')
    add_client_arguments(parser_recipes_cost)
    parser_recipes_cost.add_argument(
        '--realm', type=int, default='154', help='wow connected-realm id')
    parser_recipes_cost.add_argument(
        '--cost', action='store_true', help='display cost only')
    parser_recipes_cost.add_argument('recipename', type=str, nargs=1)
    parser_recipes_cost.set_defaults(func=cost_recipe_args)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
