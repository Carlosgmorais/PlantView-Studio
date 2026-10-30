from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [('engine', 'engine')]
binaries = []
hidden = []
for package in ['pyvista', 'pyvistaqt', 'ifcopenshell', 'OCP', 'ezdxf']:
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hidden += h
hidden += collect_submodules('vtkmodules')
a = Analysis(['run.py'], pathex=['.'], binaries=binaries, datas=datas,
             hiddenimports=hidden, excludes=['IPython', 'pytest', 'tkinter', 'trame', 'casadi', 'cadquery'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='PlantViewStudio',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='PlantViewStudio')
