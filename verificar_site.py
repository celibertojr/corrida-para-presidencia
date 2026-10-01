#!/usr/bin/env python3
"""
verificar_site.py — confere se o "Corrida para a Presidência" subiu e está lendo o TSE.

Uso:
    python3 verificar_site.py https://SEU-PROJETO.pages.dev

Só usa a biblioteca padrão do Python 3 (nada para instalar).
Saída: uma linha OK/ATENÇÃO/FALHA por verificação e um resumo no final.
"""
import json
import sys
import urllib.error
import urllib.request

def buscar(url, timeout=15):
    """Baixa uma URL e devolve (status_http, cabecalhos, corpo_em_texto)."""
    req = urllib.request.Request(url, headers={"User-Agent": "verificar-site/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:          # 4xx/5xx ainda trazem corpo útil
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    base = sys.argv[1].rstrip("/")
    falhas = 0

    def linha(nivel, msg):
        nonlocal falhas
        print(f"[{nivel:8}] {msg}")
        if nivel == "FALHA":
            falhas += 1

    # 1) A página do site abre e é a nossa?
    try:
        st, _, corpo = buscar(base + "/")
        ok = st == 200 and "Corrida para a Presidência" in corpo and "three" in corpo.lower()
        linha("OK" if ok else "FALHA", f"página inicial: HTTP {st}, {len(corpo):,} bytes")
    except Exception as e:
        linha("FALHA", f"página inicial inacessível: {e}")
        return 1

    # 2) O Worker está no ar e qual URL do TSE ele usa?
    try:
        st, _, corpo = buscar(base + "/api/status")
        info = json.loads(corpo)
        linha("OK", f"Worker no ar; lendo o TSE em: {info.get('upstream')} (fonte: {info.get('src')})")
    except Exception as e:
        linha("FALHA", f"/api/status não respondeu como JSON (o _worker.js foi enviado?): {e}")
        return 1

    # 3) O que o TSE está devolvendo agora?
    try:
        st, cab, corpo = buscar(base + "/api/resultado")
        d = json.loads(corpo)
        if d.get("ok"):
            cands = d.get("cands", [])
            top = sorted(cands, key=lambda c: c["vap"], reverse=True)[:2]
            nomes = ", ".join(f'{c["nm"]} ({c["pvap"]:.1f}%)' for c in top)
            linha("OK", f'DADOS RECEBIDOS: {d["pst"]:.1f}% das urnas, {len(cands)} candidatos; líderes: {nomes}')
            if d.get("stale"):
                linha("ATENÇÃO", "o TSE falhou e o site está mostrando o último dado guardado")
        elif d.get("error") == "not_published":
            linha("ATENÇÃO", "o TSE ainda não publicou (normal antes das 17h do dia 4/10). "
                             "Se já passou desse horário, revise TSE_URL (veja o LEIA-ME).")
        else:
            linha("FALHA", f"erro ao ler o TSE: {d.get('error')} (HTTP {st})")
        cc = cab.get("Cache-Control") or cab.get("cache-control")
        linha("OK" if cc else "ATENÇÃO", f"cache do Worker: {cc}")
    except Exception as e:
        linha("FALHA", f"/api/resultado inválido: {e}")

    print("\nRESULTADO:", "tudo certo" if falhas == 0 else f"{falhas} falha(s)")
    return 0 if falhas == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
