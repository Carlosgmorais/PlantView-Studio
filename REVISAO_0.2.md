# PlantView Studio v0.0.2 — Relatório de Revisões e Implementação

**Repositório:** `https://github.com/Carlosgmorais/PlantView-Studio.git`  
**Branch de Desenvolvimento:** `dev-v0.0.2`  
**Plataforma Alvo:** Windows 11 — 64 bits  
**Linguagens & Tecnologias:** Python 3.12, Rust, PySide6 (Qt 6), PyVista, VTK 9 (OpenGL 2), Inno Setup 6.

---

## 1. Visão Geral da Versão v0.0.2

A versão 0.0.2 transforma o **PlantView Studio** em uma solução completa e de alto desempenho para visualização e coordenação de maquetes industriais 3D federadas, adotando interface e ergonomia inspiradas no **Autodesk Navisworks Manage 2025**.

---

## 2. Implementações Realizadas

### 2.1 Aceleração por GPU & Renderização de Alto Desempenho
- **Pipeline OpenGL VTK Otimizado:** Ativação de buffers estáticos (`SetStatic(True)` em actors e mappers) para evitar uploads repetidos para a VRAM.
- **Frustum Culling em Hardware:** Configuração de `vtkFrustumCoverageCuller` com corte de cobertura (`MaximumCoverage = 1.0`, `MinimumCoverage = 0.0001`), eliminando a carga gráfica de geometrias fora do campo de visão da câmera.
- **VBO Buffer Sharing & Instancing:** Agrupamento de peças geométricas similares em malhas unificadas com compartilhamento de buffers de vértices/índices para alto rendimento, sem perder a identidade de cada componente.
- **Seleção Individual Mantida:** Cada componente renderizado preserva seus metadados (`_plantview_name`, `_plantview_layer`, `_plantview_bounds`), permitindo inspeção e seleção no viewport e na árvore de seleção.
- **Telemetria e Diagnóstico em Tempo Real:** Monitoramento dinâmico de taxa de quadros (FPS), contagem de triângulos, memória física do sistema (RAM total e disponível) e dados do adaptador GPU via menu `GPU Diagnostics`.

### 2.2 Navegação 3D Livre — Estilo Navisworks Manage
- **Look Around Livre (Botão Esquerdo Pressionado + Arrastar):** Rotação livre da câmera em torno do seu próprio olho (câmera em primeira pessoa imersiva dentro da maquete), sem orbitar obrigatoriamente um objeto central.
- **Zoom / Dolly Suave (Scroll do Mouse):** Avanço e recuo na direção focal da câmera com sensibilidade ajustável.
- **Pan Lateral / Vertical (Scroll Pressionado / Botão do Meio + Arrastar):** Deslocamento suave nos planos ortogonais da visão atual.
- **Ferramenta Orbital (Shift + Botão do Meio + Arrastar):** Rotação orbital ao redor do ponto focal central.
- **Multiplicador de Velocidade (Tecla Shift):** Aceleração de navegação estilo Navisworks para percorrer instalações industriais de grandes extensões.
- **Eliminação de Controles WASD:** Controle 100% focado no mouse e modificadores industriais.
- **Atualização Dinâmica (F5):** Tecla de atalho F5 recarrega modelos modificados em disco preservando a posição da câmera, visibilidade e rotação do observador.

### 2.3 Interface Gráfica — Padrão Navisworks Manage 2025
- **Ribbon Superior Completo:**
  - **Aba Home:**
    - Grupo *Project:* Append (+), Refresh (F5), Reset All, File Options / Units.
    - Grupo *Select & Search:* Select, Selection Tree, Select All, Select Same.
    - Grupo *Visibility:* Hide (Ctrl+H), Hide Unselected, Unhide All.
    - Grupo *Display:* Properties, Appearance Profiler / Layer Manager.
    - Grupo *Tools:* Measure (M), GPU Diagnostics.
  - **Aba Viewpoint:** Save Viewpoint, Look Around, Walk, Real-time HUD, Redefinir Câmera.
  - **Aba Review:** Medições pontuais e anotações.
- **Viewport Fundo Gradiente Céu-Horizonte:** Degradê vertical idêntico ao Autodesk Navisworks (`#5b8ecb` no topo azul céu para `#d8e8f8` no horizonte inferior).
- **Badge HUD de Coordenadas e Elevação:** Painel flutuante no canto inferior esquerdo exibindo as coordenadas em tempo real no formato:
  `X: 0,000 m  Y: 0,000 m  Z: 0,000 m` e `EL: 0,000 m`.
- **Janela Modal de Carregamento Fiel:** Modal flutuante estilizado com título *Loading ...*, percentual `0,00%`, nome do arquivo em processamento, barras de progresso duplas e botão *Cancel*.
- **Ícones Vetoriais High-DPI:** Geração procedural de todos os ícones da Ribbon e do aplicativo garantindo nitidez cristalina em monitores 1080p, 2K e 4K.

### 2.4 Fidelidade de Cores DWG & Gerenciador de Layers
- **Tabela Completa ACI 256:** Mapeamento integral das 256 cores do padrão AutoCAD Color Index (ACI).
- **Herança ByLayer / ByBlock:** Resolução de cores por camada, bloco aninhado e True Color RGB (0x00RRGGBB).
- **Gerenciador de Aparência (Appearance Profiler / Layers):** Painel interativo para visualizar camadas ativas, alternar visibilidade por checkbox e personalizar cores de camadas em tempo real.

### 2.5 Maquete Federada e Coordenadas Globais Reais
- **Multi-Formato:** Suporte simultâneo a DWG (3DSOLID, BODY, REGION, malhas), STEP, IFC, STL e OBJ.
- **Preservação de Coordenadas:** Respeito integral às coordenadas X, Y, Z originais dos arquivos de projeto de engenharia, sem centralizações destrutivas.

### 2.6 Empacotamento e Distribuidor Windows
- **Executável Nativo:** Geração de binário standalone via PyInstaller (`PlantView Studio.exe`).
- **Instalador Oficial:** Script Inno Setup 6 gerando `PlantView_Studio_0.0.2_Setup_x64.exe` com ícones, atalhos na Área de Trabalho e Menu Iniciar, e desinstalador limpo.

---

## 3. Validação e Testes Automatizados

1. `tests/test_gpu_logic_light.py`: 3/3 testes aprovados (VBO sharing, actors e instanciamento).
2. `tests/verify.py`: 7/7 testes de regressão aprovados:
   - Verificação de unidades nativas DWG (milímetros e metros).
   - Coordenadas globais IFC e STEP preservadas.
   - Salvamento e reabertura de projetos federados (`.pvproj`).
   - Atualização seletiva com F5 preservando a câmera.
3. **Smoke Test Headless:** Execução completa gerando captura de tela do viewport e log com 0 falhas.
