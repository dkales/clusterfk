import itertools
from copy import deepcopy

# TODO add more colors or make usage dynamic
# solarized color scheme
COLORS = {
    "yellow": "#b58900",
    "orange": "#cb4b16",
    "red": "#dc322f",
    "darkred": "#800000",
    "magenta": "#d33682",
    "lightcoral": "#F08080",
    "violet": "#6c71c4",
    "blue": "#268bd2",
    "cyan": "#2aa198",
    "mint": "#8df796",
    "palegreen": "#00ff00",
    "green": "#859900",
    "grey": "#cccccc",
    "black": "#000000",
    "grey1": "#454545",
    "grey2": "#666666",
    "grey3": "#999999",
    "grey4": "#C0C0C0",
    "maroon": "#800000",
    "yellow2": "#FFFF00",
    "olive": "#808000",
    "aqua": "#00FFFF",
    "purple": "#800080",
    "teal":"#008080",
    "nicered":"#723149",
    "intenseblue":"#1a46d7",
    "lightgreen": "#ccedb5",
    "bluegrey": "#416778",
    "creme": "#dfd9bf",
    "pink": "#fbd7ff",
    "nicegreen": "#7ea876",
    "nicepurple": "#8113f8",
    "foggyblue": "#8113f8",
    "yellow3": "#eadd5c"
}

json_schema = {
    "type": "object",
    "properties": {
        "cipher": {
            "type": "string",
            "enum": [
                "Mantis",
                "Qarma",
                "DeoxysBC"
            ]
        },
        "rounds": {
            "type": "integer"
        },
        "states": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "state": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "integer",
                                    "minimum": 0,
                                },
                                "minItems": 1,
                                "maxItems": 16,
                            },
                            "minItems": 4,
                            "maxItems": 4,
                        },
                        "minItems": 4,
                        "maxItems": 4,
                    }
                }
            },
            "uniqueItems": True
        }
    },
    "required": ["cipher", "states"]
}


def initDDT(sbox):
    size = len(sbox)
    ddt = [[0 for _ in range(size)] for _ in range(size)]
    for in1, in2 in itertools.product(range(size), repeat=2):
        out1, out2 = sbox[in1], sbox[in2]
        ddt[in1 ^ in2][out1 ^ out2] += 1
    return ddt


MASK_4 = 15
MASK_8 = 255


def first(set):
    return iter(set).next()


def listtobool(list):
    ret = 0
    for i in range(len(list)):
        ret += (list[len(list) - 1 - i] * pow(2, i))
    return ret


# Galois Multiplication
# taken from https://gist.github.com/raullenchai/2920069
def galoisMult(a, b):
    p = 0
    hiBitSet = 0
    for i in range(8):
        if b & 1 == 1:
            p ^= a
        hiBitSet = a & 0x80
        a <<= 1
        if hiBitSet == 0x80:
            a ^= 0x1b
        b >>= 1
    return p % 256


# bitwise (nibble) operations
def rotl_bitwise(num, i, size=4):
    if i == 0:
        return num

    ret = ((num << i) | (num >> (size - i)))
    if size == 4:
        return ret & MASK_4
    elif size == 8:
        return ret & MASK_8
    else:
        assert (False)


def rotr_bitwise(num, i, size=4):
    if i == 0:
        return num

    ret = ((num >> i) | (num << (size - i)))
    if size == 4:
        return ret & MASK_4
    elif size == 8:
        return ret & MASK_8
    else:
        assert (False)


# rowwise (list) operations
def rotl_list(lst, i, size=4):
    if i is 0:
        return lst

    new_lst = rotl_list_by_one(lst, size)
    for _ in range(i - 1):
        new_lst = rotl_list_by_one(new_lst, size)
    return new_lst


def rotr_list(lst, i, size=4):
    if i is 0:
        return lst

    new_lst = rotr_list_by_one(lst, size)
    for _ in range(i - 1):
        new_lst = rotr_list_by_one(new_lst, size)
    return new_lst


def rotl_list_by_one(lst, size=4):
    new_lst = [0 for _ in range(size)]
    new_lst[size - 1] = deepcopy(lst[0])
    for i in range(size - 1):
        new_lst[i] = lst[i + 1]
    return new_lst


def rotr_list_by_one(lst, size=4):
    new_lst = [0 for _ in range(size)]
    new_lst[0] = deepcopy(lst[size - 1])
    for i in range(size - 1, 0, -1):
        new_lst[i] = deepcopy(lst[i - 1])
    return new_lst
