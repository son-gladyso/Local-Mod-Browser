# Local MOD Browser

[简体中文](../../README.md) · [English](../../README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)

Estas opções de idioma traduzem o README, não a interface do aplicativo nem todos os guias vinculados.

<p align="center"><img src="../../docs/assets/logo-small.png" alt="Logotipo do Local MOD Browser" width="112"></p>

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Licença](https://img.shields.io/badge/license-MIT-2ea44f)
![Contrato de API](https://img.shields.io/badge/API%20contract-2.5.0-6f42c1)
[![CI](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml/badge.svg)](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml)

> **Sua biblioteca de MODs deveria ser mais do que uma pilha de pastas que só cresce.**
>
> Transforme “lembro que tinha esse MOD” em “consigo encontrá-lo, conferi-lo e continuar trabalhando em segundos” com um espaço de trabalho local, pesquisável e recuperável que pode colaborar com IA.
>
> **Baixou um MOD e depois esqueceu por que queria usá-lo ou o que ele faz?** Resumos, descrições de funções e tags existentes ajudam a recuperar esse contexto. Você pode registrar manualmente planos futuros nas notas das seleções (loadouts); o navegador não deduz automaticamente seus motivos originais para baixar algo.

[Começar](#five-minute-quick-start) · [Baixar v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2) · [IA e CLI](#ai-and-cli) · [Limites de segurança](#privacy-and-security) · [Abrir uma issue](https://github.com/son-gladyso/Local-Mod-Browser/issues)

<a id="turn-scattered-mods-into-a-useful-personal-catalog"></a>

## Transforme MODs espalhados em um catálogo pessoal útil

Local MOD Browser é um navegador de catálogos locais de MODs para Windows, um ambiente de manutenção de metadados e uma plataforma de colaboração com IA. Em vez de baixar mais conteúdo para você, ele transforma metadados de diretórios que você possui, mantém ou tem autorização explícita para usar em um sistema local no qual pode pesquisar, filtrar, comparar, favoritar, editar, traduzir e manter informações ao longo do tempo.

Ele é para você se algum destes problemas parecer familiar:

- Os MODs estão espalhados por unidades, jogos e pastas de backup, e encontrar um arquivo demora demais.
- Você baixou MODs, mas não lembra mais o que cada um faz ou por que queria usá-lo. Resumos, descrições de funções e tags que já estão no catálogo ajudam a relacionar novamente os arquivos com seu propósito.
- É difícil comparar várias versões ou cópias, e você não quer sobrescrever um original por engano.
- Favoritos, progresso de tradução, informações de autores e listas de arquivos ficam separados e são difíceis de recuperar após reinstalar.
- Você quer ajuda de IA para organizar sem que o serviço envie seus caminhos locais, inventário ou banco de dados a terceiros. Cada cliente externo de IA tem seu próprio comportamento de compartilhamento de dados.
- Edições ou traduções em lote interrompidas não deveriam deixar registros gravados pela metade, envios duplicados ou estados sem explicação.

Ele oferece um fluxo de trabalho local claro:

```text
Your directory metadata → index and search → details / tags / file comparison → favorites / loadouts
                                                      ↓
                                     revisions / translation jobs / resumable batches
                                                      ↓
                                     browser, CLI and MCP over one local API
```

O código atual oferece notas nas seleções e campos editáveis de MOD, como `function`, `details` e `tags`. Isso não significa que exista um campo de notas específico por MOD para “por que eu o baixei”. Recuperar o contexto depende das informações já presentes ou adicionadas por você; uma intenção original ausente não é reconstruída automaticamente.

<a id="see-the-product-before-installing"></a>

## Conheça o produto antes de instalar

Estas capturas de tela vêm dos **oito registros Demo inteiramente fictícios** do repositório. Elas não contêm MODs reais, recursos de jogos nem dados de sites de terceiros. Mostram a compilação pública real após a inicialização, não uma simulação de design:

![Catálogo da demonstração pública com filtros](../../docs/assets/demo-browse.png)

![Painel de detalhes da demonstração pública](../../docs/assets/demo-detail.png)

![Pesquisa por palavras-chave na demonstração pública](../../docs/assets/demo-search.png)

![Layout para telas estreitas da demonstração pública](../../docs/assets/demo-mobile.png)

Veja o passo a passo completo e reproduzível em [`docs/demo-walkthrough.md`](../../docs/demo-walkthrough.md).

<a id="user-supplied-screenshots-from-actual-use"></a>

### Capturas de uso real fornecidas pelo usuário

Estas imagens mostram a biblioteca local do próprio usuário, incluindo navegação, filtros e detalhes de uma coleção maior. Elas não são dados incluídos no programa nem a demonstração reproduzível de oito registros acima. As contagens de itens e jogos e as miniaturas refletem o ambiente do usuário no momento da captura, não conteúdo incluído na instalação.

![Uso real: biblioteca de MODs de vários jogos](../../docs/assets/real-use/library-overview.png)

*Navegação por cartões na biblioteca de vários jogos do usuário.*

![Uso real: filtrar por finalidade](../../docs/assets/real-use/purpose-filters.png)

*Filtragem por finalidade mantendo os cartões e o contexto dos filtros visíveis.*

![Uso real: painel de detalhes de um MOD](../../docs/assets/real-use/mod-detail-panel.png)

*Inspecione uma entrada ao lado da visualização atual do catálogo.*

As outras três imagens: [arquivos e variantes](../../docs/assets/real-use/files-and-variants.png), [Central de IA e tarefas](../../docs/assets/real-use/ai-task-center.png) e [Central de downloads](../../docs/assets/real-use/download-center.png).

Veja a [galeria de uso real](../../docs/real-use-gallery.md#english) para todas as seis imagens e as notas sobre seus estados. As imagens da Central de IA e tarefas e da Central de downloads apenas registram estados visíveis na interface local do usuário. Elas não comprovam que uma tarefa ou um download foi concluído com sucesso, nem que os mesmos recursos estejam incluídos no código público ou na versão pública atuais.

Nomes e miniaturas de jogos e MODs podem envolver direitos de terceiros. Eles não passam a ter licença MIT por aparecerem neste repositório. A galeria não distribui os MODs subjacentes, os recursos de jogos nem a biblioteca de origem, e não concede permissão para reutilizar conteúdo de terceiros.

<a id="decide-in-30-seconds-whether-it-fits"></a>

### Decida em 30 segundos se atende ao que você precisa

| Se você quer… | A resposta do Local MOD Browser |
| --- | --- |
| Pesquisar MODs de vários jogos e unidades em um só lugar | Configure várias fontes locais com um índice unificado e consultável |
| Lembrar para que serve um MOD baixado | Consulte resumos, descrições de funções e tags existentes; registre planos manualmente nas notas das seleções |
| Selecionar um arquivo exato de um MOD | Comparação e seleção explícita por arquivo; um conjunto inteiro não é adicionado a uma seleção por padrão |
| Pausar e retomar traduções ou trabalho de catalogação | Tarefas segmentadas, concessões temporárias, recibos, cursores de eventos e recuperação |
| Usar IA sem que o serviço envie seu inventário privado | HTTP / CLI / MCP locais com um contrato compartilhado e escuta somente na interface de loopback por padrão |
| Recuperar trabalho após migração ou atualização | Backups pareados, diário de restauração, histórico de versões e identidades estáveis de recursos |

<a id="who-is-it-for"></a>

### Para quem é?

- Jogadores com vários jogos, fontes de MODs ou anos de arquivos acumulados.
- Criadores e responsáveis pela manutenção que buscam, comparam, traduzem e organizam informações de MODs com frequência.
- Pessoas que querem assistência de IA mantendo o controle dos dados no próprio computador.
- Qualquer pessoa que prefira automação reproduzível, inspecionável e recuperável a clicar e torcer para dar certo.

<a id="what-is-it-not"></a>

### O que ele não é?

Não é um site de download de MODs, um instalador, uma ferramenta para burlar proteções nem um serviço de hospedagem remota. Ele não decide se um MOD é seguro, compatível ou tem uma licença que permite seu uso. Organiza informações que você já possui e está autorizado a usar, tornando cada alteração mais visível e controlável. Não baixa, redistribui, instala nem executa arquivos de MODs.

![Antes e depois: pastas espalhadas tornam-se um catálogo local](../../docs/assets/before-after.svg)

<a id="what-you-get"></a>

## O que você recebe

<a id="a-mod-browser-built-for-long-term-use"></a>

### Um navegador de MODs feito para uso duradouro

- Filtre rapidamente por jogo, palavras-chave, tags combinadas, estado da tradução, autor, data e informações de arquivos.
- Mantenha uma navegação estável entre listas, detalhes e histórico sem voltar às pastas para recuperar o contexto.
- Veja imagens, textos de autores, listas de arquivos e links de origem; compare cópias específicas de arquivos em vez de apenas nomes de MODs.
- Favorite entradas importantes e salve seleções importáveis e exportáveis para continuar após reinstalar ou mover diretórios.
- Use telas largas ou estreitas; os filtros complexos se recolhem e os resultados importantes continuam em destaque.

<a id="a-metadata-maintenance-workbench"></a>

### Um ambiente de manutenção de metadados

- Revise alterações com `preview` antes de `apply`, reduzindo edições acidentais e riscos de operações em lote.
- Gerencie traduções por campo e segmento, com lotes, progresso, verificações de qualidade, interrupção e retomada, e repetição idempotente.
- Tarefas em segundo plano oferecem concessões temporárias, renovação, transferência e cursores de eventos para que outra IA ou uma página reaberta possa continuar.
- Gravações importantes têm chaves de idempotência estáveis e recibos autoritativos. Após uma interrupção de rede, confira o resultado antes de decidir tentar novamente.
- O SQLite usa WAL e sincronização FULL, com um diário de restauração e backups pareados para priorizar a integridade dos dados.

<a id="a-local-platform-ai-can-use-correctly"></a>

### Uma plataforma local que a IA pode usar corretamente

- Navegador, CLI e MCP opcional compartilham um contrato, de modo que a IA não precisa simular cliques no navegador.
- 70 operações estáveis abrangem pesquisa, detalhes, revisões, favoritos, seleções, traduções e gerenciamento de tarefas.
- Cinco fluxos de trabalho determinísticos orientam a IA a encontrar, conferir, alterar, reler e relatar.
- A API local escuta em `127.0.0.1` por padrão. O serviço não chama um modelo de propósito geral nem envia dados automaticamente à nuvem.
- Em caso de exceção, os clientes recebem apenas um identificador de solicitação. Logs de diagnóstico locais são armazenados separadamente para evitar o vazamento de caminhos e rastros de pilha para quem chama o serviço.

<a id="core-capabilities"></a>

## Capacidades principais

| Cenário | Capacidades | Problema resolvido |
| --- | --- | --- |
| Encontrar informações | Pesquisa de texto completo, paginação, tags combinadas, filtros de autor/data/estado da tradução | “Lembro mais ou menos, mas não sei onde está” |
| Inspecionar detalhes | Detalhes, imagens, links de origem, listas de arquivos, histórico de revisões | “O que mudou nesta versão?” |
| Fazer uma seleção | Comparação exata de arquivos, favoritos, importação/exportação de seleções | “Preciso desta cópia, não do conjunto inteiro por engano” |
| Editar metadados | Prévia/aplicação, versionamento, listas de campos permitidos, restauração do histórico | “A limpeza em lote ainda deve ser reversível” |
| Traduzir | Tarefas segmentadas, verificações de qualidade, pausa/retomada, recibos idempotentes | “Um texto longo interrompido não deveria recomeçar do zero” |
| Colaborar com IA | HTTP, CLI, MCP, concessões temporárias, transferência, cursores de eventos | “Permitir que diferentes assistentes continuem com segurança” |
| Proteger dados | WAL/FULL, backups pareados, diário de restauração, bloqueios de ciclo de vida | “Recuperar após uma atualização ou falha” |

<a id="privacy-and-security"></a>

## Privacidade e segurança

O Local MOD Browser tem limites explícitos:

- **Somente os metadados que você fornece são indexados.** O repositório não inclui bibliotecas originais de MODs dos usuários, arquivos compactados, bancos de dados, backups, exportações nem tokens de execução. As capturas selecionadas fornecidas por usuários são documentação separada, não dados de teste nem downloads de conteúdo.
- **Ele não baixa, redistribui, instala nem executa MODs.** É um gerenciador de metadados, não um programa de download ou um instalador.
- **Ele escuta localmente por padrão.** O serviço se vincula a `127.0.0.1` e não foi projetado como serviço de rede local ou público.
- **Nenhuma conta de terceiros é necessária.** O MCP opcional é apenas um ponto de entrada de protocolo local e não chama automaticamente um modelo remoto. Um cliente externo de IA pode enviar dados consultados ao seu provedor; verifique as configurações do cliente e o escopo da autorização antes de conectá-lo.
- **Você é responsável por obter autorização para os dados de terceiros.** Siga os termos, a política de API e a licença de conteúdo de cada site ou serviço.

Leia a [política de segurança](../../SECURITY.md), o [guia de contribuição](../../CONTRIBUTING.md) e os [avisos de terceiros](../../THIRD_PARTY_NOTICES.md). Os caminhos padrão do ambiente de execução, banco de dados, tokens, diagnósticos, exportações e artefatos de teste estão no `.gitignore` para reduzir commits acidentais. Isso não protege arquivos já rastreados, arquivos adicionados à força nem dados em outros locais. Sempre revise as alterações preparadas antes de fazer commit.

<a id="supported-platform"></a>

## Plataforma compatível

- Windows 10/11 x64.
- Ambiente de execução fixado: CPython 3.13.15 x64 e SQLite 3.53.4.
- A configuração inicial precisa de acesso à rede para baixar e verificar o ambiente fixado; um Python do sistema executa o script de preparação.
- Fontes, hashes e licenças do ambiente de execução estão em [`runtime-lock.json`](../../runtime-lock.json).
- Linux e macOS não são compatíveis atualmente. O serviço principal usa a biblioteca padrão do Python sem um framework adicional de backend.

<a id="five-minute-quick-start"></a>

## Início rápido em cinco minutos

<a id="1-get-the-code-and-prepare-local-configuration"></a>

### 1. Obtenha o código e prepare a configuração local

```powershell
git clone https://github.com/son-gladyso/Local-Mod-Browser.git
cd Local-Mod-Browser
New-Item -ItemType Directory -Force data | Out-Null
Copy-Item config\sources.example.json data\sources.json
```

<a id="2-install-the-pinned-runtime-and-launch"></a>

### 2. Instale o ambiente de execução fixado e inicie

```powershell
python tools\bootstrap_runtime.py
.\.runtime\python.exe -X utf8 launcher.py --no-browser
```

Você também pode clicar duas vezes em `启动MOD浏览器.cmd` no repositório. O inicializador exibe uma URL local; abra-a para explorar o catálogo fictício de demonstração e o fluxo de trabalho de uma biblioteca vazia. Nenhuma biblioteca real de MODs é necessária para a primeira inicialização.

Para baixar diretamente o código público, use `Local-Mod-Browser-2.5.2-source.zip` da [versão v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2). O arquivo `SHA256SUMS.txt` que o acompanha permite verificar a integridade do arquivo compactado.

<a id="3-connect-your-own-catalog"></a>

### 3. Conecte seu próprio catálogo

Edite `data\sources.json`, ignorado pelo Git:

```json
[
  {
    "key": "mygame",
    "title": "My Game",
    "root": "D:\\Mods\\My Game",
    "outputDir": "D:\\Mods\\My Game\\catalog"
  }
]
```

Coloque um `catalog-data.json` em cada `outputDir`. Os caminhos relativos são resolvidos a partir do diretório que contém `sources.json`; você também pode apontar `LOCAL_MOD_BROWSER_SOURCES` para outra configuração. Veja [`config/sources.example.json`](../../config/sources.example.json) e [`examples/demo-game/catalog-data.json`](../../examples/demo-game/catalog-data.json).

<a id="4-check-the-service-and-local-api"></a>

### 4. Verifique o serviço e a API local

```powershell
.\.runtime\python.exe -X utf8 ai.py doctor
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
```

Abra `/api/docs` para consultar o contrato legível por máquinas e `/api/health` para verificar o estado do ambiente de execução, do banco de dados e do serviço.

<a id="what-does-a-first-successful-run-look-like"></a>

## Como é uma primeira execução bem-sucedida?

Comece com os registros fictícios incluídos, sem importar sua biblioteca: inicie o serviço → abra a URL local → pesquise uma amostra → abra os detalhes → volte à lista. Esse pequeno ciclo verifica navegação e pesquisa antes de organizar uma unidade inteira.

Prepare Windows 10/11 x64, um Python do sistema capaz de executar o script de preparação e acesso à rede para o primeiro download do ambiente de execução. O uso comum não exige IA nem MCP; as dependências de testes para desenvolvedores estão no [guia de contribuição](../../CONTRIBUTING.md).

**Sucesso significa:** o catálogo fictício está visível, pesquisa e detalhes são utilizáveis e você consegue inspecionar os resultados de `ai.py doctor`. Carregar uma página, por si só, não verifica a configuração de suas próprias fontes, o comportamento de recuperação nem todas as operações da plataforma.

<a id="common-questions"></a>

## Perguntas frequentes

**Por que a grande biblioteca das capturas de tela não aparece após o download?** São capturas de uso real fornecidas pelo usuário, não dados distribuídos. O repositório inclui oito registros Demo fictícios; configure suas próprias fontes separadamente.

**Ele verifica e entende automaticamente todos os MODs das minhas unidades?** Não. A entrada é a configuração de fontes e o `catalog-data.json` de cada `outputDir`, não uma interpretação universal de pastas arbitrárias. Confira os caminhos e metadados com o [exemplo de configuração](../../config/sources.example.json).

**Ele pode lembrar por que baixei um MOD?** Resumos, descrições de funções e tags existentes ajudam a rever seu propósito; você pode editar metadados e escrever planos manualmente nas notas das seleções. Ele não consegue deduzir uma intenção original esquecida a partir dos arquivos, e este README não promete um campo separado por MOD para o motivo do download.

**Por que a lista está vazia?** Confira se `data\sources.json` é válido, a partir de qual diretório de configuração os caminhos relativos são resolvidos e se cada `outputDir` de destino contém `catalog-data.json`. Depois, siga o [guia do usuário](../../docs/user-guide.md). Não publique um banco de dados privado em uma Issue.

**Preciso conectar IA para navegar?** Não. Navegador e CLI funcionam diretamente. O MCP opcional é uma interface local, não um interruptor automático de modelo na nuvem; o cliente externo que você escolher tem seus próprios limites de dados.

**A Central de downloads do uso real mostra que a versão pública baixa MODs?** Não. Ela registra a interface local de um usuário com a lista de downloads vazia e o Nexus desconectado. A versão pública continua descrita como não baixando, instalando ou executando MODs.

**Posso acessar de outros dispositivos ou da internet?** Ele escuta em `127.0.0.1` por padrão; não o implante como serviço de rede local ou público. Atualmente, plataformas diferentes do Windows também não são compatíveis.

<a id="find-the-code-for-your-change"></a>

### Encontre o código para sua alteração

- Navegação e interação: comece em `static/`; verifique listas, detalhes, estados vazios/de erro e comportamento em telas estreitas.
- Fontes e pesquisa: comece em `catalog.py` e nos exemplos de configuração; teste entradas válidas e inválidas com catálogos sintéticos.
- Operações da plataforma: leia `contracts.py`, `platform_api.py` e os testes relacionados em conjunto para manter HTTP, CLI e MCP alinhados.
- Persistência ou tarefas em segundo plano: leia primeiro o [guia de arquitetura](../../docs/architecture.md); cubra interrupção, nova tentativa e recuperação sem trocar durabilidade por velocidade.

Comandos e requisitos de PR estão no [guia de contribuição](../../CONTRIBUTING.md); tarefas iniciais estão em [Roteiro e contribuições](#roadmap-and-contributing).

<a id="ai-and-cli"></a>

## IA e CLI

A CLI é um ponto de entrada estável para scripts e IA sem operações simuladas de mouse:

```powershell
.\.runtime\python.exe -X utf8 ai.py tour
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
.\.runtime\python.exe -X utf8 ai.py doctor
```

Fluxo de trabalho seguro recomendado:

1. Leia as capacidades e a documentação de interfaces para conferir as operações compatíveis com esta versão.
2. Pesquise e leia os recursos antes de enviar `preview`; não adivinhe a identidade de um arquivo pela ordem em um array.
3. Confira os identificadores dos recursos, as versões e as diferenças na prévia e, depois, aplique com uma `idempotencyKey` estável.
4. Aguarde os estados finais reais das tarefas em segundo plano, verificando os resultados por releitura dos dados de negócio e recibos autoritativos. `queued` não significa concluído.
5. Após uma interrupção, confira os recibos e os cursores de eventos antes de continuar, transferir o trabalho ou tentar novamente.

Veja [`docs/user-guide.md`](../../docs/user-guide.md), [`docs/ai-platform-guide.md`](../../docs/ai-platform-guide.md) e [`docs/architecture.md`](../../docs/architecture.md).

<a id="verification-and-quality-gates"></a>

## Verificação e controles de qualidade

Iniciar com sucesso não basta para considerar o projeto concluído. A versão pública mantém scripts reproduzíveis de aceitação com dados sintéticos:

```powershell
# Python regression
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v

# Startup, collaboration and contract
.\.runtime\python.exe -X utf8 tests\startup_acceptance.py
.\.runtime\python.exe -X utf8 tests\collaboration_acceptance.py
python -m pip install jsonschema==4.26.0
python -X utf8 tests\contract_audit.py --fixture

# Frontend syntax
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
```

A aceitação pelo navegador também exige `npm install` e os navegadores do Playwright. A CI do Windows instala automaticamente o ambiente de execução fixado e executa regressões de Python, auditoria de contrato e verificações de JavaScript. Veja o [guia de contribuição](../../CONTRIBUTING.md).

<a id="project-map"></a>

## Mapa do projeto

```text
Local-Mod-Browser/
├─ server.py                    local HTTP service and unified error boundary
├─ platform_api.py              70 platform operations and business rules
├─ contracts.py                 shared HTTP/CLI/MCP contract and schemas
├─ catalog.py                   source configuration, indexing, and query projections
├─ ai.py                        CLI for scripts and AI
├─ mcp_adapter.py               optional local MCP entry point
├─ static/                      browser interface
├─ tests/                       regression, contract, startup, collaboration, performance and soak checks
├─ tools/bootstrap_runtime.py   pinned runtime installation and verification
└─ docs/                        user, AI platform, and architecture guides
```

<a id="roadmap-and-contributing"></a>

## Roteiro e contribuições

A versão pública atual é `v2.5.2` e o contrato de API é `2.5.0`. As prioridades são:

- Tornar o trabalho com metadados locais mais rápido e fácil de revisar, sem ampliar a coleta de dados.
- Manter consistentes os comportamentos de API, CLI e MCP, com falhas explicáveis e recuperáveis.
- Proteger os dados por meio de testes sintéticos e aceitação reproduzível; nunca usar inventários privados como dados públicos de teste.
- Ampliar adaptadores de fontes somente com autorização clara de conteúdo e dentro dos termos de terceiros.

Veja [`ROADMAP.md`](../../ROADMAP.md) para a direção atual. Documentação, testes reproduzíveis, acessibilidade e pequenas melhorias na configuração de fontes são boas primeiras contribuições.

Issues, melhorias de documentação e Pull Requests são bem-vindos. Leia [CONTRIBUTING.md](../../CONTRIBUTING.md) primeiro. Não envie caminhos pessoais, inventários, bancos de dados, tokens visíveis em capturas de tela nem conteúdo de terceiros não autorizado. Alterações externas passam por revisão; CI, aprovação do responsável pelo código, conversas resolvidas, verificações de privacidade e testes focados são exigidos antes da integração em `main`.

Se resolver um problema real, dê uma Star, compartilhe com alguém cujas pastas de MODs estejam saindo do controle ou envie uma Issue concreta. Feedback claro e reproduzível ajuda mais do que “ficou bonito” ou uma solicitação vaga; melhorias aceitas permanecem revisáveis no histórico público.

<a id="start-with-one-small-improvement"></a>

### Comece com uma pequena melhoria

Para uma primeira contribuição, escolha uma tarefa existente:

- [Perguntas frequentes da primeira execução (#3)](https://github.com/son-gladyso/Local-Mod-Browser/issues/3): acrescente solução de problemas de instalação do ambiente de execução, configuração de fontes e arquivos de catálogo ausentes, com etapas de verificação.
- [Documentação e validação da configuração de fontes (#2)](https://github.com/son-gladyso/Local-Mod-Browser/issues/2): explique os campos e caminhos relativos e cubra erros com configurações sintéticas.
- [Estados vazios e de erro acessíveis (#1)](https://github.com/son-gladyso/Local-Mod-Browser/issues/1): ajude usuários de teclado e leitores de tela a entender a próxima ação.

Verifique a discussão e o estado atuais da issue antes de declarar seu escopo. Pequenas correções de documentação podem ir diretamente para um PR; discuta primeiro recursos maiores, mudanças no modelo de dados e adaptadores de fontes, seguindo o guia de contribuição. Você não precisa fornecer sua própria biblioteca de MODs para contribuir.

<a id="license"></a>

## Licença

O código do projeto usa a [licença MIT](../../LICENSE). Avisos sobre o ambiente de execução de terceiros e dependências opcionais estão em [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md). A MIT não concede direitos sobre MODs, recursos de jogos, dados de sites, textos de autores nem qualquer outro conteúdo de terceiros.
