# List of professions and their Shadowlands skill_tier
professions = [
    (165, 2758),  # Leatherworking
    (171, 2750),  # Alchemy
    (185, 2752),  # Cooking
    (333, 2753)   # Enchanting
]


# Map of vendor reagents that can be bought
# generally cheaper by vendors.
# NOTE: Anything that would be lower than 1g is rounded down 
# since the amount is usually low enough.
vendor_reagents = {
    '172056': 0,    # Medley of Transplanar Spices
    '172057': 0,    # Inconceivably Aged Vinegar
    '172058': 0,    # Smuggled Azerothian Produce
    '172059': 0,    # Rich Grazer Milk
    '178786': 0,    # Lusterwheat Flour
    '178787': 125,  # Orboreal Shard
    '180732': 0     # Rune Etched Vial
}

# Map of recipe ids and their associated recipe names augmented
# to be more unique and better match in-game naming
unique_recipe_format = {
    42675: ('Shatters - {}', None),
    42676: ('Shatters - {}', None)
}

unique_recipe_ranges = [
    (42502, '{} - Rank 1', 63),  # Umbrahide - Rank 1
    (42510, '{} - Rank 1', 63),  # Boneshatter - Rank 1
    (45208, '{} - Rank 2', 64),  # Umbrahide - Rank 2
    (45216, '{} - Rank 2', 64),  # Boneshatter - Rank 2
    (45224, '{} - Rank 3', 65),  # Umbrahide - Rank 3
    (45232, '{} - Rank 3', 65),  # Boneshatter - Rank 3
    (45592, '{} - Rank 4', 66),  # Umbrahide - Rank 4
    (45600, '{} - Rank 4', 66),  # Boneshatter - Rank 4
]

for range_start, recipe_format, id_context in unique_recipe_ranges:
    for recipe_id in range(range_start, range_start + 8):
        unique_recipe_format[recipe_id] = (recipe_format, id_context)

context_to_item_level = {
    63: 190,
    64: 210,
    65: 225,
    66: 235
}
