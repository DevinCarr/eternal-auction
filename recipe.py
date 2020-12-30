class Recipe:
    def __init__(self, id, profession, skilltier, item_id, name, crafted_quantity):
        self.id = id
        self.profession = profession
        self.skilltier = skilltier
        self.item_id = item_id
        self.name = name
        self.crafted_quantity = crafted_quantity
        self.reagents = []
