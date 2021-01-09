# Eternal Auction

Simple cli to find cheapest reagents for recipes and items via WoW Auction House prices.

## Example

Fetch the cheapest reagents to make Shadestone with Auction House prices: 

```
$ ./eternal.py creds add --client-id CLIENT_ID --client-secret CLIENT_SECRET

$ ./eternal.py cost 'Shadestone' --realm CONNECTED_REALM_ID

Shadestone:
∟>(5 Ground Death Blossom @ 40g)
        ∟>(2 Death Blossom @ 24g)
∟>(2 Ground Vigil's Torch @ 68g)
        ∟>(2 Vigil's Torch @ 58g)
∟>(2 Ground Widowbloom @ 120g)
        ∟>(2 Widowbloom @ 110g)
∟>(2 Ground Marrowroot @ 90g)
        ∟>(2 Marrowroot @ 88g)
∟>(2 Ground Rising Glory @ 86g)
        ∟>(2 Rising Glory @ 24g)

Cost Breakdown:
gold    amount  reagent
200     5       Ground Death Blossom
136     2       Ground Vigil's Torch
240     2       Ground Widowbloom
180     2       Ground Marrowroot
96      4       Rising Glory
====================================
852 g
```

# Requirements

- [Battle.net Developer API credentials](https://develop.battle.net/documentation/guides/getting-started)
- Python3

```shell
pip install -r requirements.txt
```

## Help

```
$ ./eternal.py --help
usage: eternal.py [-h] {creds,cost} ...

positional arguments:
  {creds,cost}
    creds       battle.net credential management
    cost        find fair market value for recipe

optional arguments:
  -h, --help    show this help message and exit
```