import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plantview.gpu import configure_surface
configure_surface()
from plantview.app import main
if __name__ == '__main__':
    sys.exit(main())
