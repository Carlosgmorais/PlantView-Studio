# PlantView Studio — 0.1 experimental

Aplicativo desktop Windows independente para reunir modelos 3D em uma maquete. Interface própria em Qt, sem vínculo com Autodesk ou Navisworks. Código-fonte entregue localmente; nada publicado no GitHub.

## Abrir a versão pronta

1. Extraia **todo** o ZIP Windows para uma pasta local.
2. Abra `PlantViewStudio.exe`. Mantenha a pasta `_internal` junto do executável.
3. Clique em **Adicionar modelos**, escolha um ou vários arquivos e aguarde o relatório.
4. Para experimentar, use os arquivos da pasta `examples`.

A versão pronta inclui o runtime Python, Qt, o motor 3D e o leitor DWG. Não requer instalação de Python, AutoCAD, Navisworks, ODA ou conversor. Não é um instalador e não altera associações de arquivos. O executável não possui assinatura digital comercial. A primeira inicialização pode demorar devido ao carregamento das bibliotecas.

## DWG: requisito principal e limites reais

O fluxo é **Adicionar o DWG original → visualizar na posição original → Atualizar modelos quando o arquivo mudar**. Não há exportação manual. O DWG é lido localmente por `plantview-dwg.exe`, componente compilado e incluído no pacote, usando as bibliotecas abertas **acadrust** e **opencadkernel**. Ele interpreta os sólidos ACIS e gera uma malha de visualização temporária; essa é a representação interna, não uma alteração do arquivo DWG.

- Leitura experimental de `3DSOLID`, `BODY`, `REGION` e superfícies com dados ACIS interpretáveis pelo motor.
- Blocos comuns são percorridos preservando base, translação, rotação e escala. Não centralizamos os modelos ao carregá-los. Enquadrar muda apenas a câmera.
- Unidades reconhecidas do desenho são convertidas para metros. Para desenhos sem unidade reconhecida, selecione a unidade correta antes de adicionar. O padrão é milímetros.
- Xrefs **não são carregadas automaticamente**; MINSERT, proxies, objetos Plant 3D/Civil 3D e entidades não implementadas são reportados. Adicionar uma Xref separadamente usa as coordenadas desse arquivo, não a transformação aplicada pelo arquivo hospedeiro.
- Linhas, textos, cotas, malhas poligonais DWG e outras entidades fora do leitor de sólidos desta versão não são renderizadas. São contadas no relatório quando reconhecidas pelo parser.
- Um arquivo pode ser parcialmente carregado. Consulte os avisos de faces/corpos ausentes. Nem toda perda do parser necessariamente gera diagnóstico.
- As bibliotecas declaram várias gerações DWG até o formato 2018; isso **não é uma garantia de compatibilidade com todos os desenhos**. Esta versão não equivale à cobertura nem ao desempenho do Navisworks.
- A validação usa amostras controladas e os testes listados em `VALIDACAO.md`. É necessário validar seus DWGs industriais reais antes de uso de produção.

## Comandos

| Ação | Como usar |
|---|---|
| Adicionar | **Adicionar modelos** ou Ctrl+I; aceita vários arquivos |
| Atualizar/refresh | **Atualizar modelos** ou **F5**; relê todos os arquivos referenciados |
| Orbitar | Arraste com o botão esquerdo |
| Mover a câmera | Shift + arrastar |
| Zoom | Roda do mouse |
| Enquadrar | **Enquadrar** ou F |
| Ocultar/exibir | Caixa de seleção do modelo na árvore |
| Isolar | Selecione o modelo ou um de seus elementos e clique em **Isolar** |
| Restaurar visibilidade | **Mostrar todos** |
| Remover | Selecione o modelo e clique em **Remover** |
| Medir | Ative **Medir** e pressione P sobre duas superfícies |
| Salvar/abrir projeto | Ctrl+S / Ctrl+O |

**Refresh:** salve o desenho no programa em que está editando e então pressione F5 no PlantView. A atualização conserva câmera, ordem e visibilidade. Uma falha de leitura mantém a última geometria daquele modelo e gera mensagem no relatório. Medições anteriores são removidas, pois a geometria pode ter mudado. Não há monitoramento automático de alterações nem recarregamento de edições ainda não salvas. Arquivos parcialmente gravados devem ser atualizados novamente depois que a gravação terminar.

As medidas são distâncias entre pontos da malha, em metros, sem snap CAD exato. Não use como medição de fabricação. O projeto `.pvproj` salva caminhos relativos quando possível, unidade alternativa, visibilidade e câmera. Ele **não embute os arquivos**. Ao compartilhar, mantenha os modelos junto do projeto e preserve as pastas relativas. Arquivos ausentes são indicados no relatório.

## Outros formatos

| Formato | Implementação |
|---|---|
| STEP/STP | Open CASCADE; triangulação com tolerância linear de 0,5 mm, convertido para metros; um nó por arquivo |
| IFC | IfcOpenShell; geometria com coordenadas mundiais, identificador por produto; sem árvore espacial BIM completa nem painel de propriedades |
| DXF | ezdxf: LINE, polilinhas compatíveis, arcos, círculos, elipses, splines e 3DFACE; sólidos ACIS DXF ainda não suportados |
| STL/OBJ/PLY/VTP | Malhas; unidade escolhida pelo usuário antes da importação |
| RVT/NWC/NWD | Não suportados; nenhum SDK nativo incluído |

Não inclui clash detection, cortes, planejamento 4D, quantificação, edição CAD, materiais originais, atualização incremental ou garantia para maquetes muito grandes. Usa memória para todas as geometrias carregadas. A visibilidade é controlada por arquivo, não por elemento individual. A árvore lista os elementos importados.

## Executar e compilar o código-fonte

Recomendado: Windows 10/11 x64, driver gráfico atualizado, 8 GB de RAM ou mais, espaço livre para bibliotecas e modelos. Validado neste ambiente Windows 11 x64; outras máquinas precisam de teste.

Para executar pelo código-fonte, instale **Python 3.12 x64**, abra PowerShell nesta pasta e execute:

```powershell
.\setup-windows.ps1
.\iniciar.cmd
```

Para gerar novamente o executável:

```powershell
.\build-windows.ps1
```

O resultado fica em `dist\PlantViewStudio`. Distribua a pasta inteira, não apenas o EXE. `requirements.txt` fixa as dependências principais; `requirements-lock.txt` registra o ambiente usado na entrega.

Para recompilar o motor DWG, instale Rust estável com toolchain Windows e compilador/linker compatível:

```powershell
cargo build --release --locked --manifest-path dwg-reader/Cargo.toml
Copy-Item dwg-reader\target\release\plantview-dwg.exe engine\plantview-dwg.exe
```

As fontes das duas bibliotecas DWG estão em `dwg-reader/vendor`, com suas licenças. O arquivo `Cargo.lock` fixa dependências. A compilação inicial precisa de internet para obter os pacotes Rust restantes. A execução do aplicativo não precisa de internet.

Testes:

```powershell
.\.venv\Scripts\python.exe tests\verify.py
```

Leia `THIRD_PARTY.md` para atribuições e fontes. As fontes do leitor, interface e scripts estão incluídas para permitir manutenção sem serviços externos.
