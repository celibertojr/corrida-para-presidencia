#!/usr/bin/env python3
"""
verificar_paleta.py — confere se as camisas dos 13 candidatos são distinguíveis
e se o número é legível.

Duas medidas:
  1) Contraste WCAG entre a cor do número e a cor da camisa (>= 4.5 é bom para texto;
     usamos também contorno, então aceitamos >= 4.5 sem contorno como "folgado").
  2) Distância de cor CIEDE2000 (ΔE00) entre TODOS os pares de camisas.
     Regra prática: ΔE00 >= 20 é "claramente diferente" à primeira vista;
     10 a 20 é "parecido"; abaixo de 10 é "quase igual".
  3) Mesma distância simulando daltonismo (protanopia/deuteranopia), porque
     vermelho/verde e azul/roxo se confundem para ~8% dos homens.
"""
import itertools, math, sys

# nome: (partido, camisa, secundária, número)   — cores vindas do palette do partido
PALETA = {
    "Lula":               ("PT",        "#E11D2E", "#FFFFFF", "#FFFFFF"),
    "Renan Santos":       ("Missão",    "#0B0D10", "#FFC20E", "#FFC20E"),
    "Hertz Dias":         ("PSTU",      "#D81FA0", "#FFFFFF", "#FFFFFF"),
    "Edmilson Costa":     ("PCB",       "#FFD400", "#E11D2E", "#8E0F1A"),
    "Flávio Bolsonaro":   ("PL",        "#2A5BE8", "#FFD400", "#FFFFFF"),
    "Clariana Barão":     ("DC",        "#8FBFFF", "#2A5BE8", "#0B2A6F"),
    "Leonardo Avalanche": ("PRTB",      "#5CB82E", "#FFD400", "#0D2B05"),
    "Rui Costa Pimenta":  ("PCO",       "#7A1F2B", "#FFD400", "#FFD400"),
    "Zema":               ("Novo",      "#FF7A00", "#FFFFFF", "#1B1B1B"),
    "Wilson Grassi":      ("Democrata", "#17226B", "#FFFFFF", "#FFFFFF"),
    "Caiado":             ("PSD",       "#0B6B5E", "#FFD400", "#FFFFFF"),
    "Augusto Cury":       ("Avante",    "#0097B2", "#FF7A00", "#04222B"),
    "Samara":             ("UP",        "#F5F5F5", "#14181F", "#14181F"),
}

def hex2rgb(h):                         # "#RRGGBB" -> (r,g,b) em 0..1
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

def lin(c):                             # sRGB -> linear
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance(rgb):                     # luminância relativa (WCAG)
    r, g, b = (lin(c) for c in rgb); return 0.2126*r + 0.7152*g + 0.0722*b

def contraste(a, b):                    # razão de contraste WCAG (1 a 21)
    la, lb = luminance(hex2rgb(a)), luminance(hex2rgb(b))
    hi, lo = max(la, lb), min(la, lb); return (hi + 0.05) / (lo + 0.05)

def rgb2lab(rgb):                       # sRGB -> CIE Lab (D65)
    r, g, b = (lin(c) for c in rgb)
    x = (0.4124*r + 0.3576*g + 0.1805*b) / 0.95047
    y = (0.2126*r + 0.7152*g + 0.0722*b)
    z = (0.0193*r + 0.1192*g + 0.9505*b) / 1.08883
    f = lambda t: t ** (1/3) if t > 0.008856 else 7.787*t + 16/116
    fx, fy, fz = f(x), f(y), f(z)
    return 116*fy - 16, 500*(fx - fy), 200*(fy - fz)

def de2000(l1, l2):                     # CIEDE2000 (Sharma et al., 2005)
    L1, a1, b1 = l1; L2, a2, b2 = l2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2); Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm**7 / (Cm**7 + 25**7)))
    a1p, a2p = (1+G)*a1, (1+G)*a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    if C1p*C2p == 0: dh = 0
    elif dh > 180: dh -= 360
    elif dh < -180: dh += 360
    dHp = 2*math.sqrt(C1p*C2p)*math.sin(math.radians(dh/2))
    Lpm, Cpm = (L1+L2)/2, (C1p+C2p)/2
    if C1p*C2p == 0: hpm = h1p + h2p
    elif abs(h1p-h2p) <= 180: hpm = (h1p+h2p)/2
    elif h1p+h2p < 360: hpm = (h1p+h2p+360)/2
    else: hpm = (h1p+h2p-360)/2
    T = (1 - 0.17*math.cos(math.radians(hpm-30)) + 0.24*math.cos(math.radians(2*hpm))
         + 0.32*math.cos(math.radians(3*hpm+6)) - 0.20*math.cos(math.radians(4*hpm-63)))
    dth = 30*math.exp(-((hpm-275)/25)**2)
    Rc = 2*math.sqrt(Cpm**7/(Cpm**7+25**7))
    Sl = 1 + 0.015*(Lpm-50)**2/math.sqrt(20+(Lpm-50)**2)
    Sc, Sh = 1 + 0.045*Cpm, 1 + 0.015*Cpm*T
    Rt = -math.sin(math.radians(2*dth))*Rc
    return math.sqrt((dLp/Sl)**2 + (dCp/Sc)**2 + (dHp/Sh)**2 + Rt*(dCp/Sc)*(dHp/Sh))

# Matrizes de simulação de daltonismo (Machado et al., 2009, severidade 1.0), em RGB linear
SIM = {
    "protanopia":   [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
    "deuteranopia": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
}
def simular(rgb, m):
    lr = [lin(c) for c in rgb]
    out = [max(0, min(1, sum(m[i][j]*lr[j] for j in range(3)))) for i in range(3)]
    enc = lambda c: 12.92*c if c <= 0.0031308 else 1.055*c**(1/2.4) - 0.055
    return tuple(enc(c) for c in out)

def main():
    nomes = list(PALETA)
    print("== Legibilidade do número (contraste WCAG; >=4.5 bom, >=7 ótimo)")
    ruim = 0
    for n in nomes:
        p, cam, sec, num = PALETA[n]; c = contraste(cam, num)
        marca = "ok " if c >= 4.5 else "BAIXO"
        ruim += c < 4.5
        print(f"  {marca}  {n:20} {p:10} camisa {cam} número {num}  contraste {c:4.1f}")
    for tag, conv in [("visão normal", lambda rgb: rgb),
                      ("protanopia", lambda rgb: simular(rgb, SIM["protanopia"])),
                      ("deuteranopia", lambda rgb: simular(rgb, SIM["deuteranopia"]))]:
        labs = {n: rgb2lab(conv(hex2rgb(PALETA[n][1]))) for n in nomes}
        pares = sorted(((de2000(labs[a], labs[b]), a, b) for a, b in itertools.combinations(nomes, 2)))
        print(f"\n== Distância entre camisas, {tag} (ΔE00; alvo >= 20) — 5 pares mais próximos")
        for d, a, b in pares[:5]:
            print(f"  {'ok ' if d >= 20 else 'PERTO'}  {d:5.1f}  {a} x {b}")
        if tag == "visão normal": pior = pares[0][0]
    print(f"\nnúmeros com contraste baixo: {ruim}; menor distância (visão normal): {pior:.1f}")
    return 0 if ruim == 0 and pior >= 20 else 1

if __name__ == "__main__":
    sys.exit(main())
