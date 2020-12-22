#!/usr/bin/python3
import argparse
import datetime
import sqlite3
from authlib.integrations.requests_client import OAuth2Session

scope = 'wow.profile'
url_base = 'https://us.api.blizzard.com'

# Dethecus: 81, Connected-Realm: 154


def init_db(db):
    conn = sqlite3.connect(db)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS auctions
    (
        id INTEGER NOT NULL,
        price INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        date TEXT NOT NULL
    )
    ''')
    conn.commit()
    return conn


def init_connection(client_id, client_secret):
    client = OAuth2Session(client_id, client_secret, scope=scope)
    client.fetch_token('https://us.battle.net/oauth/token',
                       grant_type='client_credentials')
    return client


def download(args):
    client = init_connection(args.client_id, args.client_secret)
    db = init_db(args.store)
    response = client.get(
        f'{url_base}/data/wow/connected-realm/{args.realm}/auctions?namespace=dynamic-us&locale=en_US')
    response.raise_for_status()
    auctions = response.json()['auctions']
    items = {}
    search_items = set(args.items)
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
    listings = [(item['id'], item['price'], item['quantity'],
                 datetime.datetime.utcnow()) for (k, item) in items.items()]
    db.executemany('INSERT INTO auctions VALUES (?, ?, ?, ?)', listings)
    db.commit()
    db.close()


def add_client_arguments(subparser):
    subparser.add_argument('--client-id', required=True,
                           type=str, help='battle.net API client id')
    subparser.add_argument('--client-secret', required=True,
                           type=str, help='battle.net API client secret')


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_download = subparsers.add_parser(
        'download', help='download the latest data')
    add_client_arguments(parser_download)
    parser_download.add_argument(
        '--realm', type=int, default='154', help='wow connected-realm id')
    parser_download.add_argument(
        '--store', type=str, default='auction.db', 
        help='auction sqlite database location')
    parser_download.add_argument(
        '--items', type=str, required=True,
        action='extend', nargs='+', help='item ids to filter on')
    parser_download.set_defaults(func=download)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
