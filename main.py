from datetime import datetime, timedelta

from dearpygui import simple
from dearpygui.core import *
from dearpygui.demo import *

from eternal import cost_recipe, download_listings
from realms import realms
from store import Store

db_path = 'eternal.db'
add_value('selected_realm_id', 0)


def post_setup():
    auction_sync_update(None, None)

    add_value('selected_reagent_name', '')
    add_value('selected_reagent_gold', '')
    add_value('show_login_window', False)
    realm_id = None
    with Store(db_path) as db:
        realm_name = db.get_cache()
    if realm_name is None:
        return
    realm_name = realm_name[0]
    realms_dict = {name: id for (name, id) in realms}
    realm_select_callback(realm_name, (realm_name, realms_dict[realm_name]))


def get_all_items():
    with Store(db_path) as db:
        return sorted([r[1] for r in db.get_all_reagents()])


def realm_select_callback(sender, data):
    realm_name, connected_realm_id = data
    add_data('selected_realm_id', connected_realm_id)
    log_debug(f'Selected Realm: {connected_realm_id}')
    set_item_label('Realm Select##mainmenu', f'Realm: {realm_name}')
    with Store(db_path) as db:
        db.update_cache(realm_name)
    configure_item(sender, check=True)


def auction_sync_update(sender, data):
    log_debug(f'Realm sync check')
    with Store(db_path) as db:
        last_synced = db.get_last_download()
        label = 'Last Sync: > 1 hour ago'
        configure_item('Run Sync##auctionmenusync', enabled=True)
        if last_synced is not None and datetime.fromisoformat(last_synced) + timedelta(hours=1) > datetime.utcnow():
            label = 'Last Sync: < 1 hour ago'
            configure_item('Run Sync##auctionmenusync', enabled=False)
        set_item_label('##auctionmenusynctime', label)


def auction_sync(sender, data):
    with Store(db_path) as db:
        # Get battle.net credentials
        creds = db.get_credentials()
        if creds is None:
            log_error('No battle.net credentials cached')
            return
        (client_id, client_secret, _) = creds
        log_debug(f'Downloading realm: {data}')
        download_listings(db, client_id, client_secret, data)


def auction_sync_run_callback(sender, data):
    realm_id = get_data('selected_realm_id')
    log_debug(f'Syncing Realm: {realm_id}')
    if realm_id is not None:
        set_item_label('##auctionmenusynctime', 'Syncing...')
        configure_item('Run Sync##auctionmenusync', enabled=False)
        run_async_function(auction_sync, realm_id,
                           return_handler=auction_sync_update)


def reagent_select_callback(sender, data):
    with Store(db_path) as db:
        set_value('selected_reagent_name', get_value(sender))
        reagent = db.get_price_by_name(get_value(sender))
        if reagent is None:
            set_value('reagent_gold_auction', f'No auctions')
        else:
            set_value('reagent_gold_auction', f'{reagent[0]} gold')
        recipe = cost_recipe(db, get_value(sender))
        if recipe is None:
            hide_item('group##cheapestprice')
            hide_item('header##recipebreakdown')
            hide_item('header##costbreakdown')
        else:
            # Set cheapest price
            set_value('reagent_gold_cheapest', f'{recipe.cost()} gold')
            show_item('group##cheapestprice')
            # Set Recipe
            delete_item('header##recipebreakdown', children_only=True)
            walk_recipe(recipe, 'header##recipebreakdown')
            add_separator(parent='header##recipebreakdown')
            show_item('header##recipebreakdown')
            # Set Cost Breakdown
            cost_breakdown = [[item.price * quantity, item.price, quantity, item.name]
                              for (item, quantity) in recipe.selection()]
            set_table_data('table##costbreakdown', cost_breakdown)
            show_item('header##costbreakdown')
        # Set Historical Price
        history = db.get_price_history(get_value(sender))
        if history is not None and len(history) > 0:
            historyx = [datetime.fromisoformat(dt).timestamp() for (
                id, price, quantity, dt) in history]
            historyy = [price for (id, price, quantity, dt) in history]
            add_line_series(
                'plot##price', f'{get_value(sender)}', historyx, historyy)
        show_item('group##displayreagent')


def login_submit_callback(sender, data):
    with Store(db_path) as db:
        client_id = get_value('clientid')
        client_secret = get_value('clientsecret')
        if client_id is not None and len(client_id) > 0 and client_secret is not None and len(client_secret) > 0:
            db.add_or_replace_credentials(
                client_id.strip(' '), client_secret.strip(' '), datetime.utcnow())
            set_value('clientid', '')
            set_value('clientsecret', '')


def on_render(sender, data):
    delta_time = str(round(get_delta_time(), 4))
    total_time = str(round(get_total_time(), 4))


def walk_recipe(reagent, parent, default_open=False):
    id_base = 'r_' if parent == 'header##recipebreakdown' else parent + '_'
    n = 0
    for (item, quantity) in reagent.base_items:
        id = id_base + str(n)
        n += 1
        add_tree_node(
            name=id, label=f'{quantity} {item.name} @ {item.price}g', tip='AH Price', bullet=True, parent=parent)
        end()
    for (index, (item, quantity)) in enumerate(reagent.craft_items):
        id = id_base + str(n + index)
        add_tree_node(name=id, label=f'{quantity} {item.name} @ {item.price}g',
                      tip='AH Price', default_open=default_open, parent=parent)
        walk_recipe(item, id, default_open)
        end()


with simple.window('##main', label='Eternal Auction'):
    with menu_bar('MenuBar##mainmenu'):
        add_menu_item('Login##mainmenu', callback=lambda sender,
                      data: show_item('##login'))
        with menu('Realm Select##mainmenu'):
            for (name, id) in sorted(realms):
                add_menu_item(
                    name, check=False, callback=realm_select_callback, callback_data=(name, id))
        with menu('Auction##mainmenu'):
            add_menu_item('##auctionmenusynctime', enabled=False)
            add_menu_item('Run Sync##auctionmenusync',
                          enabled=False, callback=auction_sync_run_callback)

    with group('group##selectionreagent'):
        add_input_text('Search##reagentsearch', hint='Eternal Cauldron')
        add_combo('Items##reagentcombo', items=get_all_items(),
                  callback=reagent_select_callback)
        add_separator()
    with group('group##displayreagent', show=False):
        with group('group##auctionprice', horizontal=True):
            add_text('Auction Price: ')
            add_text('', source='reagent_gold_auction')
        with group('group##cheapestprice', horizontal=True):
            add_text('Cost of Materials: ')
            add_text('', source='reagent_gold_cheapest')
        add_separator()
    with collapsing_header('header##recipebreakdown', label='Recipe', default_open=True):
        pass
    with collapsing_header('header##costbreakdown', label='Shopping List', default_open=True):
        add_table('table##costbreakdown', [
                  'Total (g)', 'AH Price (g)', 'Amount', 'Reagent'])
    with collapsing_header('header##history', label='Historical Price'):
        add_plot('plot##price', label='Historical Price', y_axis_name='AH Price (g)',
                 yaxis_lock_min=True, height=400, xaxis_time=True)

with simple.window('##login', label='Battle.net Login', show=False, no_collapse=True, width=350, height=150, x_pos=15, y_pos=40):
    add_text('Battle.net Login')
    add_input_text('Client ID##clientid',
                   hint='<client id>', source='clientid')
    add_input_text('Client Secret##clientsecret', password=True,
                   hint='<client secret>', source='clientsecret')
    add_button('Login##loginsave', callback=login_submit_callback)


post_setup()

set_render_callback(callback=on_render)
set_main_window_title('Eternal Auction')
set_main_window_size(800, 800)
start_dearpygui(primary_window='##main')
