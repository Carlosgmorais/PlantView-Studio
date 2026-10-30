# Validação da versão 0.1

Ambiente: Windows 11 x64, Python 3.12.10, PySide6 6.8.3, VTK 9.3.1, PyVista 0.46.4. Leitor DWG compilado com Rust 1.99.1, target x86_64-pc-windows-gnu. Dependências exatas em `requirements-lock.txt` e `dwg-reader/Cargo.lock`.

## Testes executados

Os sete testes em `tests/verify.py` passaram. Saída integral em `tests/resultado.txt`.

1. DWG binário: criação de dois sólidos ACIS (caixa e cilindro), leitura nativa, posição fora da origem, unidades em milímetros convertidas para metros e comparação dos bytes do original antes/depois.
2. DXF: linha com coordenadas fora da origem e unidade mm; aviso de entidade TEXT não implementada.
3. IFC: parede com transformação mundial para [10,20,0] m; limites geométricos conferidos.
4. Projeto: salvar e reabrir caminhos/visibilidade/escala; rejeitar escala inválida.
5. STEP: sólido com dimensões conhecidas, transladado para [10,20,3] m; limites conferidos.
6. RVT: rejeição explícita com indicação da necessidade de SDK.
7. Interface Qt/VTK: refresh troca a geometria após salvar uma alteração, mantém câmera/visibilidade e conserva o modelo anterior quando o arquivo some.

Também foi renderizada uma maquete federada com DWG, STEP e IFC simultaneamente, sem erros de importação. A captura do viewport comprova a renderização dos três formatos em uma mesma cena. A captura simples de QWidget não inclui o conteúdo da janela nativa OpenGL; para ver a geometria use a captura `viewport.png`.

O teste inicial com a plataforma Qt `offscreen` falhou no driver OpenGL. Os testes gráficos foram refeitos com a plataforma normal `windows` e passaram.

O `PlantViewStudio.exe` gerado pelo PyInstaller também foi iniciado e testado com os três arquivos da demonstração, usando as bibliotecas e o leitor DWG incluídos no próprio pacote. O processo terminou com código 0 e produziu relatório com três modelos e lista vazia de erros. Não foi necessário abrir AutoCAD ou usar um conversor.

## Limites da evidência

- O DWG de sólidos usado na aprovação é sintético e gerado pelo mesmo codec que o lê. Isso valida integração, geometria, unidades e posicionamento para esse caso, mas não demonstra interoperabilidade completa com arquivos de produção gerados pelo AutoCAD.
- Um desenho 2D de exemplo instalado com AutoCAD também foi lido; ele não continha sólidos compatíveis e retornou a contagem de entidades ignoradas. Esse arquivo de terceiros não é redistribuído.
- Não foram fornecidos DWGs reais do usuário. Não houve teste com grandes plantas, proxies Plant 3D, Xrefs compostas ou arquivos com todas as versões DWG.
- A precisão da medição depende da triangulação; não substitui a geometria CAD exata.
- Não se testou instalação em outra máquina física ou em Windows 10.

Consulte `LEIA-ME.md` antes de usar os resultados. O estado experimental do leitor DWG é parte explícita da entrega.
