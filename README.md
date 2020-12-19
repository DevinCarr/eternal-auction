# Eternal Auction

Simple cli to download WoW auction house and capture prices for certain items.

## Example

Fetch from the Auction House: 
- Death Blossom (169701)
- Widowbloom (168583)
- Vigil's Torch (170554)
- Marrowroot (168589)
- Rising Glory (168586)
- Nightshade (171315)

```shell
$ ./auction.py download --client-id CLIENT_ID --client-secret CLIENT_SECRET --realm CONNECTED_REALM_ID --items 169701 168583 170554 168589 168586 171315
```