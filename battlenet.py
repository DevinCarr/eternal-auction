from authlib.integrations.requests_client import OAuth2Session


class BNetClient:
    def __init__(self, client_id, client_secret, url_base='https://us.api.blizzard.com', scope='wow.profile'):
        self.url_base = url_base
        self.client = OAuth2Session(client_id, client_secret, scope=scope)
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

    def get_recipes(self, profession_id, skill_tier):
        response = self.client.get(
            f'{self.url_base}/data/wow/profession/{profession_id}/skill-tier/{skill_tier}?namespace=static-us&locale=en_US')
        response.raise_for_status()
        return response.json()

    def get_recipe(self, recipe_id):
        response = self.client.get(
            f'{self.url_base}/data/wow/recipe/{recipe_id}?namespace=static-us&locale=en_US')
        response.raise_for_status()
        return response.json()
