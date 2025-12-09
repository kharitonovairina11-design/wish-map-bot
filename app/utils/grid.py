from math import ceil, sqrt
from typing import List, Tuple


def choose_grid(count: int) -> Tuple[int, int]:
    """
    Adaptive grid selection for 3-9 wishes:
    3 -> 3x1, 4 -> 2x2, 5-6 -> 2x3, 7-9 -> 3x3
    """
    if count == 3:
        return (3, 1)
    elif count == 4:
        return (2, 2)
    elif count <= 6:
        return (2, 3)
    else:  # 7-9
        return (3, 3)


def place_cells(rows: int, cols: int, canvas_w: int, canvas_h: int, count: int) -> List[Tuple[int, int, int, int]]:
    """
    Return bounding boxes (x0, y0, x1, y1) for each cell.
    Only returns boxes for the actual number of images (count).
    """
    cell_w = canvas_w // cols
    cell_h = canvas_h // rows
    boxes = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= count:
                break
            x0, y0 = c * cell_w, r * cell_h
            boxes.append((x0, y0, x0 + cell_w, y0 + cell_h))
            idx += 1
        if idx >= count:
            break
    return boxes


