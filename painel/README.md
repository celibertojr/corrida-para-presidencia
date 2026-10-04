# Painel de controle (programa de mesa)

Programa em Python, **separado do site**, para acompanhar no computador se tudo está funcionando no dia da apuração. Não é publicado na Cloudflare: o site usa só `public/` e `src/`.

## O que mostra
- Luzes de estado: TSE respondendo, site no ar, site lendo o TSE e dados chegando (verde / amarelo / vermelho).
- Apuração: % de urnas, seções totalizadas e horário da última totalização.
- Totais: eleitorado, comparecimento, abstenção, válidos, brancos e nulos.
- Classificação dos 13 candidatos, que se reordena sozinha (setas ▲/▼).
- Botões para abrir o site, os resultados do TSE e o `/api/verificar`.

## Quando consulta (pelo relógio do computador)
| Horário | Consultas |
|---|---|
| antes das 16h30 | uma ao abrir; depois, só pelo botão ⟳ |
| 16h30 às 17h | a cada 60 s (TSE e site respondendo) |
| a partir das 17h | a cada `--intervalo` segundos (padrão 30) |

## Como rodar
```bash
python painel_corrida.py
python painel_corrida.py --intervalo 20
```
Só biblioteca padrão do Python (Tkinter). No Linux: `sudo apt install python3-tk`.
