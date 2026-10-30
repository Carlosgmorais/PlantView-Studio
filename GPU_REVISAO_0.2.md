# PlantView Studio 0.2 — revisão de renderização GPU

## Implementado no fonte

- Inicialização do contexto OpenGL (core 3.2, double buffer, depth buffer 24-bit) antes da criação da janela Qt.
- Atores marcados estáticos (`vtkMapper.SetStatic(True)`) para o backend reusar a geometria enviada aos buffers OpenGL.
- Interpolação plana e desligamento de contornos de superfície por padrão, preservando as cores das entidades DWG.
- Antialiasing e depth peeling desabilitados por padrão para reduzir custo nas cenas industriais; transparência complexa não terá qualidade máxima.
- Ação **Diagnóstico GPU** para consultar fabricante/renderizador/versão OpenGL reportados pelo driver VTK.
- Reaproveitados o importador assíncrono, recarregamento F5 e a câmera livre da revisão anterior.

## Limitações e testes pendentes

- Os arquivos DWG, ACIS e STEP ainda são interpretados e triangulados na **CPU**; GPUs não substituem leitores de formatos CAD.
- Renderização efetiva pela GPU depende do driver OpenGL; Windows Remote Desktop e máquinas virtuais podem usar software renderer.
- Nenhum benchmark FPS ou teste de driver Windows foi executado neste ambiente.
- Atores individuais continuam sendo criados para manter a árvore de seleção por peça. Para modelos com centenas de milhares de peças, será necessário implementar batching/instancing e seleção por IDs.
- Alterações geométricas em `vtkPolyData` marcado estático requerem atualização do mapper; atualmente as atualizações F5 recriam os atores.

## Como validar no Windows

1. Compilar conforme `build-windows.ps1` e executar no PC com GPU.
2. Abrir **Diagnóstico GPU** e verificar se `renderer` indica GPU real (e não Mesa/llvmpipe/software).
3. Importar o mesmo conjunto de DWGs nas versões 0.1 e 0.2; comparar FPS, uso da GPU no Gerenciador de Tarefas, memória de vídeo, cores e coordenadas.
4. Navegar por entre tubulações com mouse e Shift e confirmar a suavidade da câmera.
5. Alterar um DWG externo, pressionar F5 e confirmar a troca da malha e a preservação da câmera.

Para diagnosticar problemas, definir `PLANTVIEW_SOFTWARE_RENDER=1` antes de iniciar desativa a solicitação explícita de perfil OpenGL (não garante renderização por software, pois o sistema decide).
