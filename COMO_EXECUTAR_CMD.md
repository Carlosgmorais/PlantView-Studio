# PlantView Studio 0.2 — executar pelo Prompt de Comando (Windows)

1. Extraia todo o ZIP em uma pasta local (por exemplo, `C:\PlantViewStudio`). Não execute os scripts diretamente dentro do ZIP.
2. Instale **Python 3.12 x64** e mantenha internet disponível na primeira instalação de dependências.
3. Abra o **CMD** e execute:

   ```bat
   cd /d C:\PlantViewStudio\PlantViewStudio
   INICIAR_PLANTVIEW.cmd
   ```

   Se extrair somente a pasta `PlantViewStudio`, ajuste o caminho.

4. No primeiro uso, o script cria `.venv`, instala `requirements.txt` e inicia a interface. Nas execuções seguintes, reutiliza `.venv`.
5. Para obter diagnóstico, execute `DIAGNOSTICO.cmd`, que salva `diagnostico-cmd.txt`.

**Comandos disponíveis:** `INICIAR_PLANTVIEW.cmd` (prepara, verifica e inicia); `INSTALAR_DEPENDENCIAS.cmd` (reinstala bibliotecas); `DIAGNOSTICO.cmd` (versões e GPU reportada pelo Windows); `iniciar.cmd` (atalho compatível).

**Importante:** este método executa o código Python via CMD, **não** transforma o projeto em executável nativo. O leitor DWG já vem incluído como `engine\plantview-dwg.exe`, compilado para Windows x64. As bibliotecas gráficas são instaladas no computador do usuário. Para compilar seu próprio leitor Rust, use `dwg-reader` e as instruções originais. A GPU é usada para renderização quando o driver/VTK fornece OpenGL acelerado; o diagnóstico do Windows não comprova que foi realmente utilizado. Não há testes de FPS em uma GPU Windows nesta entrega.

Em PCs sem acesso à internet, execute primeiro `INSTALAR_DEPENDENCIAS.cmd` com internet ou use a versão Windows x64 já empacotada.
