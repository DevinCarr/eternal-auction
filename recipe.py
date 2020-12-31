class Recipe:
    def __init__(self, id, profession, skill_tier, name, item_id, crafted_quantity, item_name=None):
        self.id = id
        self.profession = profession
        self.skill_tier = skill_tier
        self.name = name
        self.item_id = item_id
        self.crafted_quantity = crafted_quantity
        self.item_name = item_name
        self.reagents = []
