# Economia de contexto

Implementação local em 28/09/2026, adaptada do [vibe-coding-toolkit](https://github.com/soumatheusgomes/vibe-coding-toolkit) para o Marketing OS. Não é a instalação de um pacote RTK nem de toda a coleção de plugins.

## O que está ativo

- `AGENTS.md` curto como entrada canônica, com rotas por tipo de trabalho. `CLAUDE.md` continua apontando para essa mesma entrada.
- Documento anterior preservado integralmente em `docs/system/referencia-agente-completa.md`. Suas regras aplicáveis continuam obrigatórias; o mapa extenso é consultado por assunto.
- Memória existente em duas camadas, sem criar outro banco ou duplicar BRAND/AUDIENCE.
- Leitor `scripts/contexto.py`, sem dependências externas. Executa consultas explícitas de leitura e oferece recuperação integral quando corta uma resposta longa.
- Doctor verifica a existência das novas referências e continua verificando os caminhos do documento completo anterior.

O agente recebe a orientação de usar essas consultas em AGENTS.md. Não foi instalado hook global ou interceptação transparente de comandos do Codex; comandos nativos continuam disponíveis. As configurações pessoais e o modelo usado pelo usuário não foram alterados.

## Comandos

Executar na raiz com um Python funcional:

```powershell
python scripts/contexto.py status
python scripts/contexto.py diff
python scripts/contexto.py diff AGENTS.md --completo
python scripts/contexto.py diff --staged
python scripts/contexto.py log
python scripts/contexto.py buscar 'CTA' marketing/templates
python scripts/contexto.py ler marketing/strategy/DIRECAO-CRIATIVA.md --inicio 1 --linhas 40
python scripts/contexto.py medir
python scripts/contexto.py estatisticas
python scripts/contexto.py original ID_DA_CONSULTA
```

Nesta máquina, o executável Python validado anteriormente fica em `C:\Users\User\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`. Se o alias `python` abrir a Microsoft Store, use esse caminho com `&` no PowerShell. Em outro computador, basta Python 3.10+; Git e ripgrep são necessários apenas para suas respectivas consultas.

`status` usa a forma curta do Git; `diff` mostra estatísticas por padrão e `--completo` solicita os trechos alterados. `log` consulta dez commits. `buscar` faz busca literal, nunca expressão de shell. `ler` solicita uma faixa numerada e informa o total de linhas. Até mesmo `--completo` pode ter saída abreviada: nesse caso o aviso informa como recuperar o original.

Resultados completos e metadados de tamanho ficam em `data/contexto/`, já ignorado pelo Git. Não usar o leitor para despejar credenciais: assim como qualquer leitura de terminal, o texto pedido pode aparecer na conversa e no registro local. Não há envio a serviço externo, API paga ou chamada adicional a modelo.

Erros mantêm código de saída e conteúdo. Se não for possível salvar o resultado completo, a resposta é exibida sem corte. Nenhum comando de commit, push, exclusão, instalação ou publicação é exposto pelo leitor. Para operações não cobertas, usar o comando nativo.

## Como medir

`medir` compara caracteres da antiga entrada com a nova, somando os dois índices que permanecem obrigatórios. A estimativa em tokens usa caracteres/4, não um tokenizador de modelo. `estatisticas` contabiliza caracteres realmente omitidos pelo leitor em relação à saída que ele capturou, incluindo o custo do aviso. Não compara status curto com status longo nem estima saídas de comandos que não executou.

Esses números não são economia de fatura. Conversa, respostas, imagens, ferramentas, skills, cache e forma de cobrança também influenciam o consumo. O histórico já enviado nesta conversa não é removido; o contexto inicial menor beneficia principalmente novas sessões que carregarem a configuração atualizada.

## Fontes e escolhas

- [RTK: padrão de proxy](https://github.com/soumatheusgomes/vibe-coding-toolkit/blob/main/docs/tools/03-rtk-token-proxy.md): o repositório descreve um padrão, não distribui o binário pessoal. Aqui há uma implementação própria, explícita e sem hook, com saída completa recuperável.
- [Template de entrada](https://github.com/soumatheusgomes/vibe-coding-toolkit/blob/main/templates/CLAUDE.md.template): aplicado o princípio de entrada curta e fonte única compartilhada. Não importamos delegação obrigatória nem etapas extras para tarefas simples.
- [Memória por tópico](https://github.com/soumatheusgomes/vibe-coding-toolkit/blob/main/docs/tools/09-claude-memory-system.md): mantida a memória já existente; índice leve e detalhes sob demanda.

Não foram instalados Superpowers, Ponytail, Caveman, Graphify, Obsidian ou novos MCPs: não são necessários para esta otimização local. As validações de marketing e seus requisitos de evidência não foram desativados.

## Validação e reversão

Medição local após a implementação, em 28/09/2026:

| Conteúdo | Antes, caracteres | Depois, caracteres |
|---|---:|---:|
| AGENTS.md | 26.799 | 6.267 |
| Entrada + dois índices obrigatórios | 31.201 | 10.669 |

Redução deste conjunto: 65,8%. Estimativa grosseira por caracteres/4: de 7.800 para 2.667 tokens. Os demais custos não foram medidos. O valor pode mudar com futuras edições; executar `medir` para recalcular.

Verificação executada: 11 testes do leitor passaram; doctor em modo CI passou; manifesto de capacidades permaneceu atualizado. O doctor relatou ausência opcional de PyYAML, impedindo sua checagem de pisos/vereditos ECO, sem falha nas verificações técnicas executadas. Não se trata de veredito ECO nem de confirmação de economia faturada.

```powershell
python -m unittest discover -s tests -p test_contexto.py -v
python scripts/doctor.py --ci
python -m scripts.capability_manifest check
```

Para voltar à entrada anterior, restaurar AGENTS.md a partir da referência completa preservada, depois retirar apenas as adições desta implementação ao doctor e os arquivos novos se não forem mais usados. Não restaurar ou apagar alterações anteriores do usuário.
