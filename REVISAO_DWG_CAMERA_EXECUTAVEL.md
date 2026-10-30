# Revisão de importação, navegação e executável

- Cache local para reutilizar geometria DWG quando o arquivo e o motor não mudam.
- Cancelamento durante a leitura nativa, tempo decorrido e encerramento após 5 minutos.
- Erro explícito para DWG sem geometria visualizável.
- Correspondência entre nomes e atores da árvore, mantendo os nomes das instâncias e separando grupos por camada.
- Remoção do descarte por cobertura mínima que podia ocultar peças pequenas.
- Enquadramento de modelos adicionados e perspectiva na navegação.
- Botão do meio para mover, Shift + botão do meio para orbitar e rodinha para avançar/recuar. Olhar ao redor preserva a posição da câmera.
- Restauração dos controles de navegação após configurar a seleção de superfícies.
- Visual atualizado da faixa de ferramentas, árvore, painéis e carregamento; fundo preservado.
- Executável único com motor DWG, licenças e bibliotecas dinâmicas IFC. Correção do conflito entre ICU do Poppler e ICU do Windows usado pelo Qt.

## Validação

11 testes automatizados passaram. Os movimentos da câmera também foram verificados com VTK. O executável final carregou equipamentos.dwg (2 peças), estrutura.step (1 peça) e parede.ifc (1 peça), sem erros, com inspeção da imagem gerada.

No pequeno exemplo DWG de 2 peças, a leitura inicial levou 1,26 s e a reabertura com cache 0,013 s. Isso não representa o desempenho em arquivos grandes nem inclui a extração inicial do executável único.

O leitor DWG continua experimental: não suporta todas as entidades/versões e não resolve automaticamente referências externas. O DWG original que travou e o vídeo Navisworks não foram disponibilizados; a falha específica e a equivalência exata da navegação não foram reproduzidas. Não havia referência visual do Bemlab disponível nesta revisão.

## Compilação

Executar a partir da raiz: `python -m PyInstaller --noconfirm PlantViewStudio.spec`.
O resultado é `dist/PlantView Studio.exe`. O script `build-windows.ps1` e o instalador foram ajustados ao arquivo único.

O executável gerado foi validado com SHA-256: `B462CC3FF966EE5D28A3747FA73AC5DB84410AE1167A392B648E643F54B037E2` (296.159.015 bytes). O binário é entregue separadamente, sem inclusão no histórico Git.
