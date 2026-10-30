# Revisão de importação, navegação e executável

## Atualizações de Câmera Primeira Pessoa e Alto Desempenho (60 FPS)
- **Câmera Primeira Pessoa Real (Look Around):** Rotação com pivô estritamente travado no ponto do olho (`eye`), eliminando o drift e o roll do horizonte. Guia horizontal (Yaw) em torno do eixo global Z-up `[0, 0, 1]` e inclinação vertical (Pitch) com clamp entre -88.5° e +88.5°, reproduzindo com fidelidade a navegação em primeira pessoa do Autodesk Navisworks Manage.
- **Taxa Dinâmica de Interação VTK:** Durante arrasto do mouse, ativação automática de `SetDesiredUpdateRate(30.0)` para renderização imediata sem travamentos, retornando a `0.001` em repouso.
- **Batching de Malhas em Modelos Grandes:** Em maquetes com milhares de peças (tubulações, suportes, perfis), os componentes não-instanciados são agrupados por `(Camada, Cor)` em atores compostos (`PolyData.merge`), reduzindo draw calls de milhares para poucas dezenas. Isso elimina o travamento/lag ao girar a câmera e acelera drasticamente a taxa de quadros (FPS).
- **Árvore de Seleção Completa Preservada:** Mesmo com o agrupamento gráfico em GPU, todos os nomes e metadados dos componentes continuam listados individualmente na árvore hierárquica e na listagem de propriedades.
- **Diagnóstico Explícito de Entidades DWG:** Ao abrir arquivos DWG com entidades de arame/wireframe (linhas, polilinhas, arcos) ou versões ACIS não-tessaláveis pelo motor nativo, o sistema agora reporta explicitamente a contagem e tipos de entidades contidas no arquivo em vez de falhas genéricas.
- **Cache Local de Geometria:** Reutilização instantânea de malhas já convertidas em `%LOCALAPPDATA%\PlantView Studio\Cache`.
- **Cancelamento e Encerramento Seguro:** Suporte a cancelamento durante a decodificação com timeout de 5 minutos.

## Validação

11 testes automatizados passaram. Os movimentos da câmera também foram verificados com VTK. O executável final carregou equipamentos.dwg (2 peças), estrutura.step (1 peça) e parede.ifc (1 peça), sem erros, com inspeção da imagem gerada.

No pequeno exemplo DWG de 2 peças, a leitura inicial levou 1,26 s e a reabertura com cache 0,013 s.

## Compilação

Executar a partir da raiz: `python -m PyInstaller --noconfirm PlantViewStudio.spec`.
O resultado é `dist/PlantView Studio.exe`. O script `build-windows.ps1` e o instalador foram ajustados ao arquivo único.
