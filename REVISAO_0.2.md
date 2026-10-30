# PlantView Studio 0.2 — Revisão de código (não compilada)

## Implementado no código-fonte
- Navegação Look Around (câmera gira a partir do olho, não do ponto de órbita), arrastar esquerdo.
- Botão do meio: pan; scroll: deslocamento na direção da câmera; Shift: acelera movimentos.
- Sem controles WASD.
- Resolução inicial de cores DWG ByLayer, ByBlock (com herança de INSERT), ACI e RGB, para geometrias 3DSOLID/BODY/REGION/SURFACE já suportadas.
- Cor trafega no JSON Rust->Python e é usada pelo ator VTK em vez de paleta fixa por arquivo.
- Mantidas importação de vários arquivos, coordenadas globais convertidas a metros e F5 existentes.

## GPU — arquitetura e limitação
VTK/OpenGL já renderizava na GPU quando há contexto OpenGL acelerado. Esta revisão mantém o renderizador VTK; não reescreve decodificação DWG/ACIS ou tesselação da CPU em kernels GPU. Aceleração real depende de driver e placa. Não foi medida nesta sessão.

## Compilação necessária
O leitor Rust precisa ser recompilado e substituir `engine/plantview-dwg.exe` (o EXE anexado é da versão 0.1 e **não** produz o campo `color`). Depois recriar o pacote/EXE Python com scripts presentes no repositório.

## Validação pendente
Não foi possível executar o GUI completo porque PyVista e PySide6 não estão instalados no ambiente de testes, nem compilar o Rust pois Cargo não está presente. Compatibilidade com DWG real, herança de cores em todos os casos, proxies/ACIS e câmera interativa exigem testes Windows.

## GitHub
Criar novo repositório e publicar a pasta de código-fonte. Não publicar builds/EXEs. Verificar dependências e licença de componentes de terceiros antes de distribuição pública.
