# PlantView Studio — v0.0.2

Aplicativo desktop Windows independente para visualização e coordenação de maquetes industriais 3D federadas. Interface inspirada no **Autodesk Navisworks Manage**, com aceleração por GPU, navegação livre imersiva e preservação de cores originais DWG.

---

## 1. Destaques da Versão v0.0.2

- **Aceleração por GPU:** Renderização otimizada com buffers estáticos OpenGL/VTK, Frustum Culling em hardware (`vtkFrustumCoverageCuller`), compartilhamento VBO e seleção individual de componentes.
- **Navegação 3D Livre (Estilo Navisworks):**
  - **Look Around:** Botão esquerdo do mouse pressionado + arrastar gira a visão a partir da posição da câmera (primeira pessoa imersiva dentro da maquete).
  - **Pan:** Scroll pressionado (botão do meio) + arrastar desloca a câmera lateral e verticalmente.
  - **Ferramenta Orbital:** Shift + Scroll pressionado (botão do meio) + arrastar orbita em torno do ponto de foco.
  - **Zoom / Dolly:** Roda do mouse (scroll) avança e recua suavemente.
  - **Shift Multiplier:** Tecla Shift acelera a movimentação para percorrer grandes distâncias na maquete.
  - **F5:** Atualiza modelos modificados no disco sem resetar a câmera nem a visibilidade.
- **Interface Navisworks Manage:**
  - Ribbon superior com abas (*Home*, *Viewpoint*, *Review*) e grupos (*Project*, *Select & Search*, *Visibility*, *Display*, *Tools*).
  - Fundo com gradiente suave degradê do céu ao horizonte (`#5b8ecb` a `#d8e8f8`).
  - Painel HUD de Coordenadas e Elevação no canto inferior esquerdo (`X: ... m  Y: ... m  Z: ... m`, `EL: ... m`).
  - Tela modal de carregamento estilizada (*Loading ...*) com percentual, nome do arquivo e barras de progresso duplas.
- **Fidelidade de Cores DWG:**
  - Tabela canônica de 256 cores ACI (AutoCAD Color Index).
  - Suporte a ByLayer, ByBlock e True Color RGB.
  - Gerenciador de Aparência (*Appearance Profiler / Layers*) com controle de cores e visibilidade de camadas.
- **Distribuição Pronta:** Executável nativo standalone e instalador oficial Windows via Inno Setup 6 (`release/PlantView_Studio_0.0.2_Setup_x64.exe`).

---

## 2. Comandos e Atalhos de Teclado

| Ação | Atalho / Mouse | Descrição |
|---|---|---|
| **Look Around** | Botão Esquerdo + Arrastar | Olhar livremente ao redor na posição atual da câmera |
| **Pan** | Botão do Meio (Scroll) + Arrastar | Mover a câmera lateralmente e verticalmente |
| **Órbita** | Shift + Botão do Meio + Arrastar | Girar a visão em torno do ponto central focal |
| **Zoom** | Roda do Mouse (Scroll) | Avançar ou recuar na direção da visão |
| **Velocidade Rápida** | Manter Shift pressionado | Multiplicador de velocidade para navegação |
| **Atualizar Modelos** | **F5** | Recarrega arquivos modificados preservando a câmera |
| **Append** | **Ctrl + I** | Adicionar novos modelos à maquete federada |
| **Ocultar** | **Ctrl + H** | Oculta o modelo ou elemento selecionado |
| **Unhide All** | **Home -> Unhide All** | Restaura a visibilidade de todos os modelos |
| **Medição** | **M** | Mede a distância 3D entre dois pontos da geometria |
| **Salvar / Abrir** | **Ctrl + S / Ctrl + O** | Salvar e carregar maquete federada (`.pvproj`) |

---

## 3. Gerando o Executável e Instalador

Para compilar e gerar o pacote completo e instalador Windows:

```powershell
.\build-windows.ps1
```

Ou execute pelo prompt de comando:
```cmd
GERAR_INSTALADOR.bat
```

Os artefatos gerados são salvos em:
- Executável Portátil: `dist\PlantView Studio\PlantView Studio.exe`
- Instalador Windows: `release\PlantView_Studio_0.0.2_Setup_x64.exe`
