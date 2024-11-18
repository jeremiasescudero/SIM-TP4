import bisect

def truncate(number, ndigits=4):
    factor = 10 ** ndigits
    return int(number * factor) / factor

def calcular_uniforme(rnd, rango):
    return rango[0] + (rango[1] - rango[0]) * rnd
