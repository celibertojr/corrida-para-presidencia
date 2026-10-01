# Corrida para a Presidência: publicar e atualizar

Site 3D (Three.js) com os 13 candidatos à Presidência 2026 numa corrida de atletismo.
Só usa dados reais do TSE; não há simulação. Antes da apuração os corredores ficam na largada.

## Estrutura
- `public/index.html`: o site inteiro (página, 3D, cores e candidatos no bloco `CANDS`).
- `src/worker.js`: Worker que busca o JSON do TSE, normaliza e guarda em cache (`/api/resultado`, `/api/status`).
- `wrangler.jsonc`: configuração do Cloudflare Workers (arquivos de `public/` servidos direto).
- `verificar_site.py`: teste do site publicado. `verificar_paleta.py`: confere cores (contraste e daltonismo).

## Publicar (Cloudflare Workers, grátis)
1. Cloudflare > Computação > Workers e Pages > Criar > Importar um repositório > `corrida-para-presidencia`.
2. Nome do projeto: `corrida-para-presidencia`. Comando da build: vazio. Comando de implantação: `npx wrangler deploy`. Implantar.
3. Domínio próprio (recomendado, deixa o cache de borda funcionar e o site atender muitos acessos): no Worker, *Configurações > Domínios e rotas > Adicionar > Domínio personalizado*, por exemplo `corrida.seudominio.com`.
4. Teste: `python3 verificar_site.py https://SEU-ENDERECO`.

## Atualizar
Edite o arquivo no GitHub e faça *Commit*; a Cloudflare publica sozinha em cerca de 1 minuto.
Para voltar uma versão: Worker > Implantações > reverter.

## Testar
- `/api/status` mostra a URL do TSE em uso. `/api/resultado` responde `ok:false, not_published` se o TSE ainda não publicou, ou os dados reais.
- Antes de a apuração começar, o site mostra "Aguardando apuração". Não existe modo de demonstração.

## Dia 4 de outubro
A divulgação começa às 17h (Brasília). URL oficial usada:
`https://resultados.tse.jus.br/oficial/ele2026/6257/dados/br/br-c0001-e006257-u.json`
Se o TSE mudar o caminho, crie a variável `TSE_URL` no Worker (Configurações > Variáveis e segredos) com a URL correta.

## Limites do plano grátis
- 100 mil execuções do Worker por dia (só `/api/*` conta; a página e os arquivos não). Com atualização a cada 30 s e cache de 20 s, comporta cerca de 800 horas de visualização por dia.
- O TSE bloqueia por IP depois de muitas requisições; por isso o Worker consulta o TSE no máximo uma vez a cada 20 s.
