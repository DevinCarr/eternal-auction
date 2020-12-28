class Recipe:
    def __init__(self, id, profession, skilltier, name, crafted_quantity):
        self.id = id
        self.name = name
        self.profession = profession
        self.skilltier = skilltier
        self.crafted_quantity = crafted_quantity
        self.reagents = []