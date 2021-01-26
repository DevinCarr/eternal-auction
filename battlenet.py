from authlib.integrations.requests_client import OAuth2Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class BNetClient:
    def __init__(self, client_id, client_secret, url_base='https://us.api.blizzard.com', scope='wow.profile'):
        self.url_base = url_base
        self.client = OAuth2Session(client_id, client_secret, scope=scope)
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.client.mount('https://', adapter)
        self.client.fetch_token('https://us.battle.net/oauth/token',
                                grant_type='client_credentials')

    def get_auction(self, connected_realm):
        response = self.client.get(
            f'{self.url_base}/data/wow/connected-realm/{connected_realm}/auctions?namespace=dynamic-us&locale=en_US')
        response.raise_for_status()
        return response.json()

    def get_item(self, item_id):
        response = self.client.get(
            f'{self.url_base}/data/wow/item/{item_id}?namespace=static-us&locale=en_US')
        response.raise_for_status()
        return response.json()

    def get_professions(self):
        response = self.client.get(
            f'{self.url_base}/data/wow/profession/index?namespace=static-us&locale=en_US')
        response.raise_for_status()
        return response.json()

    def get_profession(self, profession_id):
        response = self.client.get(
            f'{self.url_base}/data/wow/profession/{profession_id}?namespace=static-us&locale=en_US')
        response.raise_for_status()
        return response.json()

    def get_realms(self):
        response = self.client.get(
            f'{self.url_base}/data/wow/realm/index?namespace=dynamic-us&locale=en_US')
        response.raise_for_status()
        return response.json()

    def get_connected_realms(self):
        realms = self.get_realms()
        realms = [self.get_realm(r['slug']) for r in realms['realms']]
        realms = [(r['name'], r['connected_realm']['href']) for r in realms if r['is_tournament'] == False]
        return [(name, cr[cr.find('connected-realm/') + len('connected-realm/'): cr.find('?')]) for (name, cr) in realms]

    def get_realm(self, realm_slug):
        response = self.client.get(
            f'{self.url_base}/data/wow/realm/{realm_slug}?namespace=dynamic-us&locale=en_US')
        response.raise_for_status()
        return response.json()

    def get_recipes(self, profession_id, skill_tier):
        response = self.client.get(
            f'{self.url_base}/data/wow/profession/{profession_id}/skill-tier/{skill_tier}?namespace=static-us&locale=en_US')
        response.raise_for_status()
        return response.json()

    def get_recipe(self, recipe_id):
        response = self.client.get(
            f'{self.url_base}/data/wow/recipe/{recipe_id}?namespace=static-us&locale=en_US')
        print(response.status_code)
        # response.raise_for_status()
        return response.json()
