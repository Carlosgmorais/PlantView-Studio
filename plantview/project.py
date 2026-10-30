import json
import math
import os
from pathlib import Path
import tempfile

def save_project(path, models, camera):
    path = Path(path).resolve()
    records = []
    for model in models:
        record = {key: model[key] for key in ('path', 'visible', 'scale')}
        try: record['path'] = os.path.relpath(record['path'], path.parent)
        except ValueError: pass
        records.append(record)
    payload = {'format': 'PlantView', 'version': 1, 'models': records, 'camera': camera}
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
        temporary = f.name
        json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=False)
    try: os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def load_project(path):
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('format') != 'PlantView' or data.get('version') != 1:
        raise ValueError('Formato/versão de projeto incompatível.')
    if not isinstance(data.get('models'), list): raise ValueError('Lista de modelos inválida.')
    for m in data['models']:
        if not isinstance(m.get('path'), str) or not isinstance(m.get('visible'), bool):
            raise ValueError('Registro de modelo inválido.')
        if not isinstance(m.get('scale'), (int, float)) or not math.isfinite(m['scale']) or m['scale'] <= 0:
            raise ValueError('Escala inválida.')
        m['path'] = str((path.parent / m['path']).resolve())
    camera = data.get('camera')
    if camera is not None and (len(camera) != 3 or any(len(row) != 3 or any(not isinstance(v, (int,float)) or not math.isfinite(v) for v in row) for row in camera)):
        raise ValueError('Câmera inválida.')
    return data
