class Recipe:
    def __init__(self, id, profession, skill_tier, item_id, name, crafted_quantity):
        self.id = id
        self.profession = profession
        self.skill_tier = skill_tier
        self.item_id = item_id
        self.name = name
        self.crafted_quantity = crafted_quantity
        self.reagents = []
