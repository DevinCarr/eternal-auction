#!/usr/bin/python3
import argparse
import itertools
from datetime import datetime, timedelta

from auction import Auction
from battlenet import BNetClient
from constants import professions, vendor_reagents, unique_recipe_format
from item import Item
from reagent import Reagent
from recipe import Recipe
from store import Store

# Dethecus: 81, Connected-Realm: 154


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
        id = str(auction['item']['id'])
        if 'context' in auction['item']:
            id_context = auction['item']['context']
            id = f'{id}-{id_context}'
        if id in vendor_reagents:
            items[id] = {
                'id': id,
                'price': vendor_reagents[id],
                'quantity': -1
            }
        elif id in search_items:
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
    db.add_auctions(listings, fetch_time)


def unique_recipe(recipe_id, recipe_name, item_id):
    # Some recipes have multiple ranks with the same name and
    # no other identifiers besides unique items produced and recipe ids.
    # This is provides a hook to distinguish the different ranks in their name.
    # It also helps provide uniqueness when searching for a recipe.
    if recipe_id in unique_recipe_format:
        recipe_format, id_context = unique_recipe_format[recipe_id]
        name = recipe_format.format(recipe_name)
        return (name, f'{item_id}-{id_context}' if id_context is not None else item_id)
    return (recipe_name, item_id)


def get_recipe(client, profession_id, skill_tier, recipe_id):
    recipe_response = client.get_recipe(recipe_id)
    if 'crafted_item' not in recipe_response:
        return None
    recipe = Recipe(recipe_id, profession_id, skill_tier, None, None, None)
    recipe_name, item_id = unique_recipe(
        recipe_id, recipe_response['name'], recipe_response['crafted_item']['id'])
    recipe.item_id = item_id
    recipe.name = recipe_name
    recipe.item_name = recipe_name
    recipe.crafted_quantity = int(
        recipe_response['crafted_quantity']['value'])
    recipe.reagents = [Reagent(r['reagent']['id'], r['reagent']
                                ['name'], 0, int(r['quantity']), 0) for r in recipe_response['reagents']]
    return recipe


def fetch_recipes(db, client_id, client_secret, profession_id, skill_tier):
    # Fetch recipes only if not already cached
    recipe_count = db.get_recipe_count(profession_id, skill_tier)
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
        return None
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
            fetch_recipes(db, args.client_id, args.client_secret,
                          profession_id, skill_tier)
        # Download listings from auction house
        download_listings(db, args.client_id, args.client_secret, args.realm)
        # Cost the recipe
        recipe = cost_recipe(db, args.recipename[0])
        if recipe is None:
            item_price = db.get_price_by_name(args.recipename[0])
            if item_price is None:
                print(f'Recipe with recipe name: {args.recipename[0]} not found.')
            else:
                if not args.cost:
                    print(f'\n{args.recipename[0]} @ {item_price[0]}g')
                else:
                    print(f'{item_price[0]}')
            return
        if not args.cost:
            if recipe.price is not None:
                print(f'\n{recipe.name} @ {recipe.price}g:')
            else:
                print(f'\n{recipe.name}:')
            walk_recipe(recipe)
            items = recipe.selection()
            print('\nCost Breakdown:')
            print('gold\tamount\treagent')
            for (item, quantity) in items:
                print(f'{item.price * quantity}\t{quantity}\t{item.name}')
            print('================' + '=' *
                  max([len(i.name) for (i, q) in items]))
        print(f'{recipe.cost()}')


def add_client_arguments(subparser):
    subparser.add_argument('--client-id', required=True,
                           type=str, help='battle.net API client id')
    subparser.add_argument('--client-secret', required=True,
                           type=str, help='battle.net API client secret')
    subparser.add_argument('--realm', default='154', 
                           type=int, help='wow connected-realm id')
    subparser.add_argument('--store', default='eternal.db',
                           type=str, help='sqlite database location')


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_cost = subparsers.add_parser(
        'cost', help='find fair market value for recipe')

    add_client_arguments(parser_cost)
    parser_cost.add_argument(
        '--cost', action='store_true', help='display cost only')
    parser_cost.add_argument('recipename', type=str, nargs=1)
    parser_cost.set_defaults(func=cost_recipe_args)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
