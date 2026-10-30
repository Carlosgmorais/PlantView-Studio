# Revis�o de importa��o, navega��o e execut�vel

- Cache local para reutilizar geometria DWG quando o arquivo e o motor n�o mudam.
- Cancelamento durante a leitura nativa, tempo decorrido e encerramento ap�s 5 minutos.
- Erro expl�cito para DWG sem geometria visualiz�vel.
- Correspond�ncia entre nomes e atores da �rvore, mantendo os nomes das inst�ncias e separando grupos por camada.
- Remo��o do descarte por cobertura m�nima que podia ocultar pe�as pequenas.
- Enquadramento de modelos adicionados e perspectiva na navega��o.
- Bot�o do meio para mover, Shift + bot�o do meio para orbitar e rodinha para avan�ar/recuar. Olhar ao redor preserva a posi��o da c�mera.
- Restaura��o dos controles de navega��o ap�s configurar a sele��o de superf�cies.
- Visual atualizado da faixa de ferramentas, �rvore, pain�is e carregamento; fundo preservado.
- Execut�vel �nico com motor DWG, licen�as e bibliotecas din�micas IFC. Corre��o do conflito entre ICU do Poppler e ICU do Windows usado pelo Qt.

## Valida��o

11 testes automatizados passaram. Os movimentos da c�mera tamb�m foram verificados com VTK. O execut�vel final carregou equipamentos.dwg (2 pe�as), estrutura.step (1 pe�a) e parede.ifc (1 pe�a), sem erros, com inspe��o da imagem gerada.

No pequeno exemplo DWG de 2 pe�as, a leitura inicial levou 1,26 s e a reabertura com cache 0,013 s. Isso n�o representa o desempenho em arquivos grandes nem inclui a extra��o inicial do execut�vel �nico.

O leitor DWG continua experimental: n�o suporta todas as entidades/vers�es e n�o resolve automaticamente refer�ncias externas. O DWG original que travou e o v�deo Navisworks n�o foram disponibilizados; a falha espec�fica e a equival�ncia exata da navega��o n�o foram reproduzidas. N�o havia refer�ncia visual do Bemlab dispon�vel nesta revis�o.

## Compila��o

Executar a partir da raiz: `python -m PyInstaller --noconfirm PlantViewStudio.spec`.
O resultado � `dist/PlantView Studio.exe`. O script `build-windows.ps1` e o instalador foram ajustados ao arquivo �nico.

O execut�vel gerado foi validado com SHA-256: `B462CC3FF966EE5D28A3747FA73AC5DB84410AE1167A392B648E643F54B037E2` (296.159.015 bytes). O bin�rio � entregue separadamente, sem inclus�o no hist�rico Git.
