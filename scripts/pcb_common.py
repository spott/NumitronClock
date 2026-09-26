"""Shared helpers for scripts run with the installed KiCad pcbnew Python."""
from pathlib import Path
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware/top-board"
BOARD = PROJECT / "NumitronTop.kicad_pcb"


def vec(x, y):
    return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))


def mm(point):
    return pcb.ToMM(point.x), pcb.ToMM(point.y)


def save(board, filename=BOARD):
    # pcbnew can serialize incomplete project settings while saving a board.
    # The native .kicad_pro remains authoritative and must be preserved.
    project = PROJECT / "NumitronTop.kicad_pro"
    original = project.read_bytes()
    try:
        pcb.SaveBoard(str(filename), board)
    finally:
        project.write_bytes(original)


def stock_library():
    import os
    return Path(os.environ.get("KICAD_FOOTPRINT_DIR",
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"))


def load_footprint(fpid):
    library, name = fpid.split(":")
    directory = (PROJECT / "libraries" if library == "Numitron" else stock_library()) / (library + ".pretty")
    fp = pcb.FootprintLoad(str(directory), name)
    if fp is None:
        raise RuntimeError("Unable to load " + fpid)
    fp.SetFPIDAsString(fpid)
    return fp


def text(board, value, x, y, layer, size=.8, thickness=.12):
    item = pcb.PCB_TEXT(board)
    item.SetText(value)
    item.SetPosition(vec(x,y))
    item.SetTextSize(vec(size,size))
    item.SetTextThickness(pcb.FromMM(thickness))
    item.SetLayer(layer)
    item.SetMirrored(layer == pcb.B_SilkS)
    board.Add(item)
    return item
