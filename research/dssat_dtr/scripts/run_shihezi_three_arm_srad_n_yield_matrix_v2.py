from pathlib import Path

src_path = Path('research/dssat_dtr/scripts/shihezi_three_arm_srad_n_yield_matrix.py')
src = src_path.read_text()
old = "    dates = irrigation_dates(txt)"
new = (
    "    yy = xfile.stem[4:6]\n"
    "    if yy == '19':\n"
    "        dates = ['19123','19165','19173','19182','19189','19196','19203','19210','19221','19235']\n"
    "    elif yy == '20':\n"
    "        dates = ['20126','20167','20175','20184','20191','20198','20205','20212','20223','20237']\n"
    "    else:\n"
    "        raise RuntimeError('unexpected Shihezi FileX year code: ' + yy)"
)
if src.count(old) != 1:
    raise RuntimeError(f'expected one irrigation parser call, found {src.count(old)}')
patched = src.replace(old, new, 1)
code = compile(patched, str(src_path) + ':runtime-fixed-dates', 'exec')
exec(code, {'__name__': '__main__', '__file__': str(src_path)})
