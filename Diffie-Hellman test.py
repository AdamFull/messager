import random


g = random.randint(1, 100)
p = random.randint(100, 1000)

a=random.randint(1, 1000)
b=random.randint(1, 210)

A = (g**a) % p
B = (g**b) % p

keyA = (B**a) % p
keyB = (A**b) % p

print("KEY A: %s, KEY B: %s." % (keyA, keyB))