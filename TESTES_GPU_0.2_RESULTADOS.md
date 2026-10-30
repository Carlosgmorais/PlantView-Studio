# PlantView Studio 0.2 — resultados dos testes neste ambiente

Data: 2026-10-30.

## Executados
- Integridade do arquivo ZIP original: PASSOU (`ZipFile.testzip`).
- Sintaxe de todos os 10 arquivos `.py` encontrados: PASSOU (`ast.parse`/`compileall`).
- Teste isolado `test_gpu_logic_light.py`: 3 de 3 PASSARAM.
  - Fingerprint igual para translações de uma mesma malha.
  - Fingerprint diferente para geometria modificada.
  - Agrupamento de cinco malhas iguais e separação por cor, reduzindo seis peças a dois atores (mock).
- API `vtkGlyph3DMapper` do VTK 9.6.2: instância construída corretamente.

## Não executados / não validados
- Suite `tests/verify.py`: indisponíveis `pyvista` e `PySide6` neste ambiente; importação falha em `ModuleNotFoundError: No module named 'pyvista'`.
- Leitor DWG em Rust e validação de sólidos DWG reais: não executados.
- Renderização OpenGL em GPU física Windows, FPS e consumo VRAM: não executados.
- Navegação do mouse, interface gráfica, cores de arquivos DWG reais e F5: não testados end-to-end.
- Seleção de instâncias individuais não implementada; o agrupamento gera um ator para várias peças.

## Reproduzir no Windows
1. Instalar Python e bibliotecas de `requirements.txt` e compilar o componente Rust conforme instruções do projeto.
2. Executar `python tests/test_gpu_logic_light.py` e `python tests/verify.py`.
3. Abrir um DWG com peças repetidas e cores diferentes; conferir árvore, separação por cor, coordenadas e atualização F5.
4. Medir FPS/VRAM antes/depois, com a mesma GPU, resolução, câmera e conjunto de modelos.

O teste com mocks verifica a lógica de agrupamento, não desempenho real do hardware gráfico.
