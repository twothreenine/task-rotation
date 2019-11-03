import random

class Number:
    def __init__(self, name):
        self.name = name
        self.assigned_letters = []

def choose_letter(number, letters):
    possible_letters = [letter for letter in letters if letter not in number.assigned_letters]
    chosen_letter = random.choice(possible_letters)
    return chosen_letter

letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]

numbers = []
for i in range(6):
    numbers.append(Number(name=i+1))

for number in numbers:
    for i in range(2):
        number.assigned_letters.append(choose_letter(number=number, letters=letters))

for number in numbers:
    print(number.name)
    for letter in number.assigned_letters:
        print(letter)
    print(" ")