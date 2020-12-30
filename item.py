import itertools


class Item:
    def __init__(self, id, name, price=None, recipe=[]):
        self.id = id
        self.name = name
        self.price = price
        self.base_items = [(item, quantity)
                           for (item, quantity) in recipe if not item.craftable]
        self.craft_items = [(item, quantity)
                            for (item, quantity) in recipe if item.craftable]
        self.craftable = len(recipe) > 0

    def __component_cost(self):
        base_items_cost = [quantity * item.cost()
                           for (item, quantity) in self.base_items]
        craft_items_cost = [quantity * item.cost()
                            for (item, quantity) in self.craft_items]
        return sum(base_items_cost) + sum(craft_items_cost)

    def cost(self):
        if not self.craftable:
            return self.price

        total_component_cost = self.__component_cost()
        return total_component_cost if self.price is None or total_component_cost < self.price else self.price

    def expand_quantity(self, items, quantity):
        return [(item, quantity * q) for (item, q) in items]

    def selection(self):
        if not self.craftable:
            return [(self, 1)]

        # Less than is used to favor the time savings when equal for
        # the cost of components since recipes take time to create.
        if self.price is None or self.__component_cost() < self.price:
            craft_items_selection = [self.expand_quantity(
                item.selection(), quantity) for (item, quantity) in self.craft_items]
            craft_items_selection = list(
                itertools.chain(*craft_items_selection))
            return self.base_items + craft_items_selection
        else:
            return [(self, 1)]


# herb1 = Item(2, "herb1", price=2)
# herb2 = Item(3, "herb2", price=2)
# stone = Item(4, "stone", price=3, recipe=[(herb1, 2)])
# potion = Item(1, "potion", price=12, recipe=[(stone, 2), (herb2, 2)])

# print(potion.cost())
# items = potion.selection()
# for (item, quantity) in items:
#     print(f'({item.name}, {quantity})')  # [(stone, 2), (herb2, 2)]
