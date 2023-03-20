"""
    Proof that Python works by reference meaning the other code will work as intended
"""
class Object_Test:
    def __init__(self, v):
        self.value = v

    def set_value(self, v):
        self.value = v

class ValueChanger:
    def __init__(self, obj):
        self.object = obj

    def change_obj(self):
        self.object.set_value(self.object.value + 1)

    def routine(self):
        values = [self.object.value]
        self.change_obj()

        values.append(self.object.value)

        return values



def main():
    o = Object_Test(123)
    c = ValueChanger(o)
    v = c.routine()

    print(v)