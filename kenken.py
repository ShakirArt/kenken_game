import random
import sys
import time
from math import prod
import pygame

CAGE_SIZES = (1, 2, 2, 2, 3, 3, 4)  

def make_latin_square(n):
    rows, cols, syms = list(range(n)), list(range(n)), list(range(1, n + 1))
    random.shuffle(rows)
    random.shuffle(cols)
    random.shuffle(syms)
    return [[syms[(rows[r] + cols[c]) % n] for c in range(n)] for r in range(n)]


def cage_ok(op, target, values):
    if op == "":
        return values[0] == target
    if op == "+":
        return sum(values) == target
    if op == "*":
        return prod(values) == target
    if op == "-":
        return abs(values[0] - values[1]) == target
    if op == "/":
        return max(values) == target * min(values)
    return False


def pick_rule(values):
    if len(values) == 1:
        return "", values[0]
    if len(values) == 2:
        hi, lo = max(values), min(values)
        ops = ["+", "*", "-"] + (["/"] if hi % lo == 0 else [])
        op = random.choice(ops)
        return op, {"+": hi + lo, "*": hi * lo, "-": hi - lo, "/": hi // lo}[op]
    op = random.choice("+*")
    return op, sum(values) if op == "+" else prod(values)


def make_cages(solution):
    n = len(solution)
    cage_id = [[-1] * n for _ in range(n)]
    cages = []
    order = [(r, c) for r in range(n) for c in range(n)]
    random.shuffle(order)

    for r, c in order:
        if cage_id[r][c] != -1:
            continue
        cid = len(cages)
        cells = [(r, c)]
        cage_id[r][c] = cid
        for _ in range(random.choice(CAGE_SIZES) - 1):
            frontier = []
            for cr, cc in cells:
                neighbors = [
                    (cr - 1, cc),  
                    (cr + 1, cc),  
                    (cr, cc - 1), 
                    (cr, cc + 1)   
                ]
                for nr, nc in neighbors:
                    if 0 <= nr < n and 0 <= nc < n and cage_id[nr][nc] == -1:
                        frontier.append((nr, nc))
            if not frontier:
                break
            nr, nc = random.choice(frontier)
            cage_id[nr][nc] = cid
            cells.append((nr, nc))
        cells.sort()
        op, target = pick_rule([solution[a][b] for a, b in cells])
        cages.append((op, target, cells))
    return cage_id, cages


def count_solutions(n, cage_id, cages, limit=2):
    board = [[0] * n for _ in range(n)]
    row_used = [set() for _ in range(n)]
    col_used = [set() for _ in range(n)]
    found = 0

    def cage_possible(r, c):
        op, target, cells = cages[cage_id[r][c]]
        vals = [board[a][b] for a, b in cells if board[a][b]]
        if len(vals) == len(cells):
            return cage_ok(op, target, vals)
        if op == "+":
            return sum(vals) < target          
        if op == "*":
            return target % prod(vals) == 0
        return True

    def fill(i):
        nonlocal found
        if found >= limit:
            return
        if i == n * n:
            found += 1
            return
        r, c = divmod(i, n)
        for v in range(1, n + 1):
            if v in row_used[r] or v in col_used[c]:
                continue
            board[r][c] = v
            row_used[r].add(v)
            col_used[c].add(v)
            if cage_possible(r, c):
                fill(i + 1)
            board[r][c] = 0
            row_used[r].discard(v)
            col_used[c].discard(v)

    fill(0)
    return found


def generate_puzzle(n):
    while True:
        solution = make_latin_square(n)
        for _ in range(40):
            cage_id, cages = make_cages(solution)
            if count_solutions(n, cage_id, cages) == 1:
                return solution, cage_id, cages


BOARD_PX = 540                   
MARGIN = 20
HEADER = 64
BOARD_X, BOARD_Y = MARGIN, HEADER + 14
PANEL_X = BOARD_X + BOARD_PX + MARGIN
PANEL_W = 220
WIN_W = PANEL_X + PANEL_W + MARGIN
WIN_H = BOARD_Y + BOARD_PX + MARGIN
SIZES = (3, 4, 5, 6)


FONT_STACK = "jetbrainsmono,firacode,consolas,sfmono,menlo,dejavusansmono,couriernew,monospace"

COLORS = {
    "bg":       (13, 17, 23),
    "card":     (22, 27, 34),
    "cell":     (22, 27, 34),
    "cage_hl":  (30, 40, 54),
    "selected": (24, 56, 52),
    "wrong_bg": (74, 30, 36),
    "grid":     (48, 54, 61),
    "cage":     (139, 148, 158),
    "keycap":   (110, 118, 129),
    "accent":   (163, 230, 53),     
    "player":   (163, 230, 53),
    "hinted":   (192, 132, 252),    
    "label":    (245, 165, 36),     
    "label_ok": (63, 185, 80),
    "error":    (255, 92, 92),
    "text":     (230, 237, 243),
    "muted":    (125, 133, 144),
    "win":      (63, 185, 80),
}
OP_SYMBOL = {"": "", "+": "+", "-": "\u2212", "*": "\u00d7", "/": "\u00f7"}


class Game:
    def __init__(self, n=4):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("KenKen")
        self.clock = pygame.time.Clock()

        def font(size, bold=False):
            return pygame.font.SysFont(FONT_STACK, size, bold=bold)

        self.f_title, self.f_timer = font(26, True), font(26, True)
        self.f_value, self.f_tag = font(22, True), font(16, True)
        self.f_label, self.f_key, self.f_desc = font(12, True), font(13, True), font(14)
        self.font = font
        self.new_game(n)

    def new_game(self, n):
        self.n = n
        self.cell = BOARD_PX // n
        self.solution, self.cage_id, self.cages = generate_puzzle(n)
        self.board = [[0] * n for _ in range(n)]
        self.hinted = [[False] * n for _ in range(n)]
        self.sel = (0, 0)
        self.hints_used = 0
        self.show_wrong = False
        self.start = time.time()
        self.finish = None
        self.num_font = self.font(int(self.cell * 0.5), True)
        self.cage_font = self.font(max(13, int(self.cell * 0.17)), True)



    def find_conflicts(self):
        n, b = self.n, self.board
        bad = set()
        for r in range(n):
            for c in range(n):
                v = b[r][c]
                if v and (b[r].count(v) > 1 or [b[i][c] for i in range(n)].count(v) > 1):
                    bad.add((r, c))
        return bad

    def cage_status(self, i):
        op, target, cells = self.cages[i]
        vals = [self.board[r][c] for r, c in cells]
        if 0 in vals:
            return None
        return cage_ok(op, target, vals)

    @property
    def won(self):
        return self.finish is not None

    def check_win(self):
        full = all(all(row) for row in self.board)
        if (full and not self.find_conflicts()
                and all(self.cage_status(i) for i in range(len(self.cages)))):
            self.finish = time.time()


    def set_cell(self, value):
        r, c = self.sel
        if self.won or self.hinted[r][c]:
            return
        self.board[r][c] = value
        self.check_win()

    def hint(self):
        r, c = self.sel
        if self.won or self.board[r][c] == self.solution[r][c]:
            return
        self.board[r][c] = self.solution[r][c]
        self.hinted[r][c] = True
        self.hints_used += 1
        self.check_win()

    def on_key(self, event):
        r, c = self.sel
        k = event.key
        if k == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
        elif k == pygame.K_n:
            self.new_game(self.n)
        elif k == pygame.K_TAB:
            self.new_game(SIZES[(SIZES.index(self.n) + 1) % len(SIZES)])
        elif k == pygame.K_h:
            self.hint()
        elif k == pygame.K_c:
            self.show_wrong = not self.show_wrong
        elif k == pygame.K_UP:
            self.sel = (max(r - 1, 0), c)
        elif k == pygame.K_DOWN:
            self.sel = (min(r + 1, self.n - 1), c)
        elif k == pygame.K_LEFT:
            self.sel = (r, max(c - 1, 0))
        elif k == pygame.K_RIGHT:
            self.sel = (r, min(c + 1, self.n - 1))
        elif k in (pygame.K_BACKSPACE, pygame.K_DELETE):
            self.set_cell(0)
        elif event.unicode.isdigit():
            v = int(event.unicode)
            if 0 <= v <= self.n:
                self.set_cell(v)

    def on_click(self, pos):
        x, y = pos[0] - BOARD_X, pos[1] - BOARD_Y
        if x < 0 or y < 0:
            return
        r, c = y // self.cell, x // self.cell
        if r < self.n and c < self.n:
            self.sel = (r, c)


    def text(self, font, string, color, x, y, anchor="topleft"):
        surf = font.render(string, True, COLORS[color])
        self.screen.blit(surf, surf.get_rect(**{anchor: (x, y)}))
        return surf.get_width()

    def card(self, x, y, w, label, value, value_color="text", h=62):
        pygame.draw.rect(self.screen, COLORS["card"], (x, y, w, h), border_radius=6)
        pygame.draw.rect(self.screen, COLORS["grid"], (x, y, w, h), 1, border_radius=6)
        self.text(self.f_label, label, "muted", x + 10, y + 8)
        self.text(self.f_value, value, value_color, x + 10, y + 28)

    def keycap(self, x, y, key, desc):
        w, h = 54, 24
        pygame.draw.rect(self.screen, COLORS["card"], (x, y, w, h), border_radius=5)
        pygame.draw.rect(self.screen, COLORS["keycap"], (x, y, w, h), 1, border_radius=5)
        self.text(self.f_key, key, "text", x + w // 2, y + h // 2, "center")
        self.text(self.f_desc, desc, "muted", x + w + 14, y + h // 2, "midleft")


    def draw_header(self):
        mid = HEADER // 2
        w = self.text(self.f_title, "KENKEN", "accent", MARGIN, mid, "midleft")
        self.text(self.f_tag, f"// {self.n}\u00d7{self.n}", "muted", MARGIN + w + 12, mid + 2, "midleft")

        secs = int((self.finish or time.time()) - self.start)
        w = self.text(self.f_timer, f"{secs // 60:02}:{secs % 60:02}",
                      "win" if self.won else "text", WIN_W - MARGIN, mid, "midright")
        self.text(self.f_tag, "T+", "muted", WIN_W - MARGIN - w - 10, mid + 2, "midright")
        pygame.draw.line(self.screen, COLORS["grid"], (0, HEADER), (WIN_W, HEADER), 1)

    def draw_board(self):
        n, s = self.n, self.cell
        sel_cage = self.cage_id[self.sel[0]][self.sel[1]]
        conflicts = self.find_conflicts()

        def origin(r, c):
            return BOARD_X + c * s, BOARD_Y + r * s

        for r in range(n):
            for c in range(n):
                x, y = origin(r, c)
                wrong = (self.show_wrong and self.board[r][c]
                         and self.board[r][c] != self.solution[r][c])
                if wrong:
                    bg = "wrong_bg"
                elif (r, c) == self.sel:
                    bg = "selected"
                elif self.cage_id[r][c] == sel_cage:
                    bg = "cage_hl"
                else:
                    bg = "cell"
                pygame.draw.rect(self.screen, COLORS[bg], (x, y, s, s))
                pygame.draw.rect(self.screen, COLORS["grid"], (x, y, s, s), 1)

        for r in range(n):
            for c in range(n):
                x, y = origin(r, c)
                cid = self.cage_id[r][c]
                if r == 0 or self.cage_id[r - 1][c] != cid:
                    pygame.draw.line(self.screen, COLORS["cage"], (x, y), (x + s, y), 3)
                if r == n - 1 or self.cage_id[r + 1][c] != cid:
                    pygame.draw.line(self.screen, COLORS["cage"], (x, y + s), (x + s, y + s), 3)
                if c == 0 or self.cage_id[r][c - 1] != cid:
                    pygame.draw.line(self.screen, COLORS["cage"], (x, y), (x, y + s), 3)
                if c == n - 1 or self.cage_id[r][c + 1] != cid:
                    pygame.draw.line(self.screen, COLORS["cage"], (x + s, y), (x + s, y + s), 3)

        for i, (op, target, cells) in enumerate(self.cages):
            x, y = origin(*cells[0])
            status = self.cage_status(i)
            color = "error" if status is False else "label_ok" if status else "label"
            self.text(self.cage_font, f"{target}{OP_SYMBOL[op]}", color, x + 7, y + 5)

        
        for r in range(n):
            for c in range(n):
                v = self.board[r][c]
                if v:
                    color = ("error" if (r, c) in conflicts
                             else "hinted" if self.hinted[r][c] else "player")
                    x, y = origin(r, c)
                    self.text(self.num_font, str(v), color, x + s // 2, y + s // 2 + s // 14, "center")

        x, y = origin(*self.sel)
        pygame.draw.rect(self.screen, COLORS["accent"], (x, y, s, s), 3)

        # corner brackets
        o, ln = 9, 16
        x0, y0, x1, y1 = BOARD_X - o, BOARD_Y - o, BOARD_X + BOARD_PX + o, BOARD_Y + BOARD_PX + o
        for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            pygame.draw.line(self.screen, COLORS["accent"], (cx, cy), (cx + sx * ln, cy), 2)
            pygame.draw.line(self.screen, COLORS["accent"], (cx, cy), (cx, cy + sy * ln), 2)

    def draw_panel(self):
        x, y = PANEL_X, BOARD_Y
        half = (PANEL_W - 10) // 2
        filled = sum(1 for row in self.board for v in row if v)

        self.card(x, y, half, "SIZE", f"{self.n}\u00d7{self.n}")
        self.card(x + half + 10, y, half, "FILLED", f"{filled}/{self.n * self.n}")
        self.card(x, y + 72, half, "HINTS", str(self.hints_used),
                  "hinted" if self.hints_used else "text")
        self.card(x + half + 10, y + 72, half, "CHECK",
                  "ON" if self.show_wrong else "OFF", "error" if self.show_wrong else "muted")
        self.card(x, y + 144, PANEL_W, "STATUS",
                  "SOLVED" if self.won else "SOLVING...", "win" if self.won else "label")

        y += 232
        self.text(self.f_label, "CONTROLS", "muted", x, y)
        pygame.draw.line(self.screen, COLORS["grid"], (x, y + 20), (x + PANEL_W, y + 20), 1)
        keys = ((f"1-{self.n}", "enter number"), ("DEL", "clear cell"), ("H", "hint"),
                ("C", "check mistakes"), ("N", "new puzzle"), ("TAB", "change size"),
                ("ESC", "quit"))
        for i, (key, desc) in enumerate(keys):
            self.keycap(x, y + 32 + i * 34, key, desc)

    def draw(self):
        self.screen.fill(COLORS["bg"])
        self.draw_header()
        self.draw_board()
        self.draw_panel()
        pygame.display.flip()

    def run(self):
        while True:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    self.on_key(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.on_click(event.pos)
            self.draw()


if __name__ == "__main__":
    Game().run()