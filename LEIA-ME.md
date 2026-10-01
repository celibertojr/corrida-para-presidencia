# Corrida para a Presidência: publicar e atualizar

Arquivos:
- `index.html`: o site 3D (é o único arquivo que você edita no dia a dia).
- `_worker.js`: busca o JSON da Presidência no TSE, normaliza e guarda em cache (20 s).
- `_routes.json`: só `/api/*` passa pelo Worker; o site em si é estático (grátis e ilimitado).
- `verificar_site.py`: confere se tudo subiu (`python3 verificar_site.py https://SEU-SITE.pages.dev`).

## Caminho recomendado: GitHub + Cloudflare Pages (atualização automática)

1. Crie uma conta grátis em https://github.com e em https://dash.cloudflare.com.
2. No GitHub, crie um repositório vazio chamado `corrida-presidencia` (público ou privado).
3. Coloque nele os 4 arquivos desta pasta, na raiz do repositório (botão *Add file > Upload files* no site do GitHub).
4. Na Cloudflare: *Workers e Pages > Criar > Pages > Conectar ao Git*, escolha o repositório.
5. Configuração de build: Framework = **None**; Build command = **(vazio)**; Build output directory = **/**. Clique em *Salvar e implantar*.
6. Em cerca de 1 minuto o site fica em `https://corrida-presidencia.pages.dev`.
7. Confirme: `python3 verificar_site.py https://corrida-presidencia.pages.dev`.

**Toda vez que o arquivo mudar no GitHub, a Cloudflare republica sozinha em ~1 minuto.** Se algo der errado, em *Implantações* dá para voltar à versão anterior com um clique.

## Alternativa sem GitHub: envio direto
*Workers e Pages > Criar > Pages > Fazer upload de ativos*, arraste os arquivos. Para atualizar: abra o projeto > *Criar nova implantação* e envie de novo.

## Alternativa por linha de comando (1 comando)
    npx wrangler pages deploy . --project-name corrida-presidencia
(pede login na Cloudflare na primeira vez.)

## Testar antes da eleição
- `/api/status` mostra qual URL do TSE o Worker usa.
- `/api/resultado` antes das 17h de 4/10 responde `{"ok":false,"error":"not_published"}` e o site mostra "Aguardando".
- O site **não tem simulação**: só mostra dados reais do TSE. Sem dados, os corredores ficam na largada e a página avisa "Aguardando".

## Dia 4 de outubro
A divulgação começa às 17h (Brasília). O endereço oficial usado é
`https://resultados.tse.jus.br/oficial/ele2026/6257/dados/br/br-c0001-e006257-u.json`.
Se o TSE publicar em outro caminho, crie a variável `TSE_URL` com o endereço certo (*Settings > Environment variables*) e reimplante. Não precisa mexer no código. Para achar o endereço: abra resultados.tse.jus.br, F12 > Rede, filtre por `-u.json` no resultado de Presidente.

O Worker guarda respostas 404 por 60 s. Isso evita que muitos 404 seguidos façam o TSE bloquear o IP por 10 minutos.

## Limites de custo
Requisições a `/api/*` contam como requisições do Workers: 100 mil por dia no plano gratuito. Cada aba aberta gera cerca de 120 por hora, então cabem cerca de 800 pessoas-hora por dia. Se esperar muito público, use o plano pago do Workers (a partir de US$ 5/mês; confirme no site da Cloudflare) ou aumente `POLL_MS` no `index.html`.

## Cores das camisas
Cada candidato tem camisa (`c`), cor do número (`t`) e cor secundária (`s`, mangas, calção e faixas) no bloco `CANDS`. Depois de mudar qualquer cor, rode `python3 verificar_paleta.py` (copie as cores novas para o bloco `PALETA` do script): ele mede o contraste do número e a distância entre todas as camisas, inclusive simulando daltonismo.

## Ajustes comuns (no `index.html`)
- Bloco `CANDS`: nome, número, cor da camiseta, cabelo (`gray`/`dark`), estilo (`short`/`bald`/`long`/`bob`), barba (`beard`), porte (`build` 0 a 2).
- `POLL_MS`: intervalo de atualização (padrão 30000 ms).
- Candidatos que o TSE não listar somem sozinhos da pista.

Aviso: resultado parcial, sem caráter oficial. A fonte oficial é o TSE.
