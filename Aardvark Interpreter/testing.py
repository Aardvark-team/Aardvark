import cProfile

giant_dict = {
    "a": 1,
    "b": 2,
    "c": 3,
    "d": 4,
    "e": 5,
    "f": 6,
    "g": 7,
    "h": 8,
    "i": 9,
    "j": 10,
    "k": 11,
    "l": 12,
    "m": 13,
    "n": 14,
    "o": 15,
    "p": 16,
    "q": 17,
    "r": 18,
    "s": 19,
    "t": 20,
    "u": 21,
    "v": 22,
    "w": 23,
    "x": 24,
    "y": 25,
    "z": 26,
    "aardvark": {"a": 1, "b": 2, "c": 3},
    "aardvark2": {"a": 1, "b": 2, "c": 3},
    "aardvark3": {"a": 1, "b": 2, "c": 3},
    "aardvark4": {"a": 1, "b": 2, "c": 3},
    "aardvark5": {"a": 1, "b": 2, "c": 3},
    "aardvark6": {"a": 1, "b": 2, "c": 3},
    "aardvark7": {"a": 1, "b": 2, "c": 3},
    "aardvark8": {"a": 1, "b": 2, "c": 3},
    "aardvark9": {"a": 1, "b": 2, "c": 3},
    "aardvark10": {"a": 1, "b": 2, "c": 3},
    "question": 1,
    "answer": -1,
    "hello": "world",
    "python": ["slow", "hard", "bad", "weak"],
}
keys = list(giant_dict.keys())


def not_stored():
    z = 0
    for j in range(10):
        for x in keys:
            for y in keys:
                for i in range(1000):
                    if giant_dict[x] == giant_dict[y] or giant_dict[x] == i:
                        z += 1
    print(z)
    return z


def stored():
    z = 0
    for j in range(10):
        for x in keys:
            valx = giant_dict[x]
            for y in keys:
                valy = giant_dict[y]
                for i in range(1000):
                    if valx == valy or valx == i:
                        z += 1
    print(z)
    return z


cProfile.run("not_stored()", sort="tottime")
cProfile.run("stored()", sort="tottime")
