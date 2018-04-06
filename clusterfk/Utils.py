import itertools

#TODO add more colors or make usage dynamic
#solarized color scheme
COLORS = {
"yellow":   "#b58900",
"orange":   "#cb4b16",
"red":      "#dc322f",
"darkred":  "#800000",
"magenta":  "#d33682",
"violet":   "#6c71c4",
"blue":     "#268bd2",
"cyan":     "#2aa198",
"mint":     "#8df796",
"palegreen": "#00ff00",
"green":    "#859900",
"grey":     "#cccccc",
"black":    "#000000",
"grey1":    "#333333",
"grey2":    "#666666",
"grey3":    "#999999",
"grey4":    "#1f1f1f",

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
    ret =  0
    for i in range(len(list)):
        ret += (list[len(list) - 1 - i] * pow(2,i))
    return ret

#bitwise (nibble) operations
def rotl(num, i, size=4):
    if i == 0:
        return num

    ret = ((num << i) | (num >> (size - i)))
    if size == 4:
        return ret & MASK_4
    elif size == 8:
        return ret & MASK_8
    else:
        assert(False)

def rotr(num, i, size=4):
    if i == 0:
        return num

    ret = ((num >> i) | (num << (size - i)))
    if size == 4:
        return ret & MASK_4
    elif size == 8:
        return ret & MASK_8
    else:
        assert(False)