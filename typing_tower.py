import array
import copy
import json
import math
import random
import sys
import time
from collections import Counter, deque
from pathlib import Path

import pygame

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()


WIDTH, HEIGHT, FPS = 1280, 720, 60

try:
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
except pygame.error:
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Typing Tower")


BG = (45, 38, 32)
GRASS = (82, 91, 65)
GRASS_DARK = (65, 72, 52)
GRASS_LIGHT = (101, 105, 72)
DIRT = (118, 98, 68)
DIRT_DARK = (96, 79, 55)
STONE = (120, 116, 108)
STONE_DARK = (84, 80, 74)

WOOD_DARK = (72, 45, 31)
WOOD = (111, 70, 45)
WOOD_LIGHT = (145, 94, 57)

CREAM = (226, 210, 174)
CREAM_DARK = (184, 163, 126)
WHITE = (240, 232, 211)
BLACK = (25, 23, 20)

RED = (145, 65, 50)
RED_DARK = (105, 45, 38)
RED_BRIGHT = (208, 84, 62)
GOLD = (184, 143, 67)
GOLD_LIGHT = (222, 182, 96)
ICE = (140, 205, 235)
FIRE = (214, 125, 62)
LEAF = (125, 175, 95)

KEY_NORMAL = (61, 56, 49)
KEY_BORDER = (110, 99, 83)
KEY_ACTIVE = (184, 143, 67)
KEY_NEXT = (130, 92, 60)
KEY_BAD = (160, 52, 42)

ENEMY_COLORS = [(133, 70, 53), (115, 76, 56), (137, 86, 54), (104, 73, 58)]


MAP_SIZE = 600
MAP_X = 45
MAP_Y = 45
MAP_RECT = pygame.Rect(MAP_X, MAP_Y, MAP_SIZE, MAP_SIZE)
TOWER_X = MAP_X + MAP_SIZE // 2
TOWER_Y = MAP_Y + MAP_SIZE // 2
TOWER_RADIUS = 48
PANEL_RECT = pygame.Rect(720, 45, 510, 625)

MENU_TX, MENU_TY = 960, 410

KEYBOARD_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
ROW_STAGGER = [0.0, 0.25, 0.75]
KEY_W, KEY_H, KEY_GAP = 42, 42, 5

DIFFICULTIES = [
    {"name": "EASY", "hp": 15, "speed": 0.80, "spawn": 0.85, "score": 0.75},
    {"name": "NORMAL", "hp": 10, "speed": 1.00, "spawn": 1.00, "score": 1.00},
    {"name": "HARD", "hp": 7, "speed": 1.25, "spawn": 1.25, "score": 1.50},
]

ABILITIES = [
    ("freeze", "FREEZE", ICE),
    ("bomb", "BOMB", FIRE),
    ("heal", "HEAL", LEAF),
]
MAX_CHARGES = 3
FREEZE_TIME = 4.5


TIERS = [

    ["cat", "dog", "sun", "tree", "moon", "door", "bird", "food", "fish", "book",
     "star", "rain", "wind", "fire", "leaf", "rock", "sand", "lake", "road", "ship",
     "wolf", "bear", "duck", "frog", "lamp", "bell", "cake", "gold", "iron", "coin"],

    ["apple", "river", "chair", "green", "cloud", "stone", "light", "mouse", "grass",
     "plant", "bread", "night", "horse", "tiger", "sword", "magic", "flame", "storm",
     "ocean", "eagle", "dream", "music", "happy", "smile", "heart", "queen", "crown",
     "candy", "field", "beach"],

    ["forest", "window", "yellow", "orange", "purple", "garden", "castle", "rabbit",
     "school", "friend", "summer", "winter", "dragon", "bridge", "island", "silver",
     "wizard", "knight", "shadow", "planet", "rocket", "flower", "coffee", "market",
     "pirate", "hunter", "anchor", "candle"],

    ["monster", "thunder", "morning", "country", "picture", "kitchen", "teacher",
     "journey", "weather", "library", "freedom", "village", "captain", "machine",
     "kingdom", "diamond", "mystery", "lantern", "blanket", "warrior", "harvest",
     "fortune", "dolphin", "penguin", "volcano", "rainbow"],

    ["adventure", "beautiful", "dangerous", "something", "important", "different",
     "computer", "mountain", "building", "together", "remember", "knowledge",
     "wonderful", "chocolate", "butterfly", "landscape", "strawberry", "telescope",
     "fireworks", "nightmare", "passenger", "afternoon"],

    ["experience", "impossible", "information", "environment", "interesting",
     "everything", "understanding", "responsibility", "conversation", "imagination",
     "extraordinary", "civilization", "determination", "celebration", "independence",
     "architecture", "opportunity", "temperature", "organization", "communication"],
]

BOSS_PHRASES = [
    "the dark lord", "iron giant", "storm king", "ancient dragon", "silent night",
    "fallen knight", "crimson moon", "winter is here", "shadow of doom",
    "the last stand", "broken crown", "king of ashes", "cursed castle", "wild hunt",
    "the black tower", "lord of thunder", "bone collector", "frozen throne",
    "endless night", "the red baron", "sea of fire", "queen of thorns",
]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1[:3], c2[:3]))


def lighten(c, t=0.3):
    return mix(c, (255, 255, 255), t)


def darken(c, t=0.3):
    return mix(c, (0, 0, 0), t)


def load_font(names, size, bold=False):
    try:
        return pygame.font.SysFont(names, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


F_HUGE = pygame.font.Font(None, 120)
F_TITLE = pygame.font.Font(None, 64)
F_BIG = pygame.font.Font(None, 48)
F_MED = pygame.font.Font(None, 32)
F_SMALL = pygame.font.Font(None, 24)
F_TINY = pygame.font.Font(None, 20)
F_WORD = load_font("dejavusansmono,liberationmono,couriernew,monospace", 24, True)

_EMPTY = pygame.Surface((0, 0))
_text_cache = {}


def render(text, font, color):

    if not text:
        return _EMPTY
    key = (text, id(font), color)
    surf = _text_cache.get(key)
    if surf is None:
        if len(_text_cache) > 900:
            _text_cache.clear()
        surf = font.render(text, True, color)
        _text_cache[key] = surf
    return surf


def draw_text(s, text, font, color, x, y, anchor="topleft", shadow=None, alpha=None):
    surf = render(text, font, color)
    rect = surf.get_rect()
    setattr(rect, anchor, (int(x), int(y)))
    if shadow:
        s.blit(render(text, font, shadow), rect.move(2, 2))
    if alpha is not None and alpha < 255:
        surf = surf.copy()
        surf.set_alpha(int(clamp(alpha, 0, 255)))
    s.blit(surf, rect)
    return rect


def draw_panel(s, rect, fill, border=None, width=2, radius=8, alpha=None):
    rect = pygame.Rect(rect)
    if rect.w <= 0 or rect.h <= 0:
        return
    if alpha is None:
        pygame.draw.rect(s, fill, rect, border_radius=radius)
    else:
        tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(tmp, (*fill[:3], alpha), tmp.get_rect(), border_radius=radius)
        s.blit(tmp, rect.topleft)
    if border:
        pygame.draw.rect(s, border, rect, width, border_radius=radius)


def make_glow(radius, color, strength=200):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        a = int(strength * (1 - r / radius) ** 2)
        pygame.draw.circle(surf, (*color[:3], a), (radius, radius), r)
    return surf


def shape_points(shape, x, y, r):
    if shape == "triangle":
        return [(x, y - r), (x - r, y + r * 0.85), (x + r, y + r * 0.85)]
    if shape == "diamond":
        return [(x, y - r * 1.1), (x + r, y), (x, y + r * 1.1), (x - r, y)]
    if shape == "octagon":
        return [(x + r * math.cos(math.pi / 8 + k * math.pi / 4),
                 y + r * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]

    return [(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r)]


def draw_shape(s, shape, color, x, y, r, width=0):
    if shape == "circle":
        pygame.draw.circle(s, color, (int(x), int(y)), max(1, int(r)), width)
    else:
        pygame.draw.polygon(s, color, shape_points(shape, x, y, r), width)


SAVE_PATH = Path.home() / ".typing_tower.json"
DEFAULT_SAVE = {
    "highscores": [],
    "settings": {"sound": True, "music": True, "difficulty": 1},
    "totals": {"games": 0, "words": 0, "keys": 0, "seconds": 0.0},
    "key_errors": {},
    "best_wpm": 0,
}


class SaveData:
    def __init__(self):
        self.data = copy.deepcopy(DEFAULT_SAVE)
        self.load()

    def load(self):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for k, v in raw.items():
                if k in self.data:
                    if isinstance(self.data[k], dict) and isinstance(v, dict):
                        self.data[k].update(v)
                    else:
                        self.data[k] = v
        except (OSError, ValueError, AttributeError):
            pass
        d = self.data["settings"]
        d["difficulty"] = int(clamp(d.get("difficulty", 1), 0, len(DIFFICULTIES) - 1))

    def save(self):
        try:
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass


RATE = 22050


def synth(freq, dur, vol=0.4, wave="sine", slide=0.0, noise=0.0,
          attack=0.004, decay=4.0, vibrato=0.0):

    n = max(1, int(RATE * dur))
    buf = array.array("h")
    phase = 0.0
    tau = math.tau
    for i in range(n):
        t = i / RATE
        frac = i / n
        f = freq * (1.0 + slide * frac)
        if vibrato:
            f *= 1.0 + vibrato * math.sin(tau * 6.0 * t)
        phase += tau * f / RATE
        if wave == "sine":
            v = math.sin(phase)
        elif wave == "square":
            v = 0.6 if math.sin(phase) >= 0 else -0.6
        elif wave == "saw":
            v = ((phase / tau) % 1.0) * 2.0 - 1.0
        else:
            v = 2.0 * abs(((phase / tau) % 1.0) * 2.0 - 1.0) - 1.0
        if noise:
            v = v * (1.0 - noise) + random.uniform(-1.0, 1.0) * noise
        env = min(1.0, t / attack) * math.exp(-decay * frac)
        buf.append(int(clamp(32767 * vol * v * env, -32767, 32767)))
    return buf


def layer(parts, total=None):

    length = int(total * RATE) if total else max(int(o * RATE) + len(b) for o, b in parts)
    acc = [0] * length
    for off, buf in parts:
        o = int(off * RATE)
        for i, v in enumerate(buf):
            idx = o + i
            if total:
                idx %= length
            elif idx >= length:
                break
            acc[idx] += v
    return array.array("h", (int(clamp(v, -32767, 32767)) for v in acc))


class Audio:
    def __init__(self, settings):
        self.settings = settings
        self.ok = False
        self.sounds = {}
        self.key_sounds = []
        self.music = None
        self.music_channel = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 1, 512)
            self.ok = True
            self._build()
        except Exception:
            self.ok = False


    def _snd(self, buf):
        channels = pygame.mixer.get_init()[2]
        if channels == 2:
            st = array.array("h")
            for v in buf:
                st.append(v)
                st.append(v)
            buf = st
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _build(self):
        S = synth
        self.key_sounds = [self._snd(S(480 + i * 45, 0.07, 0.22, "square", decay=6))
                           for i in range(8)]
        snd = self.sounds
        snd["error"] = self._snd(S(150, 0.22, 0.35, "saw", slide=-0.45, noise=0.25, decay=3))
        snd["kill"] = self._snd(layer([
            (0.00, S(330, 0.18, 0.30, "square", slide=1.2, decay=4)),
            (0.00, S(120, 0.25, 0.35, "sine", noise=0.6, decay=6)),
            (0.07, S(660, 0.15, 0.20, "triangle", decay=5)),
        ]))
        snd["hit"] = self._snd(S(90, 0.38, 0.65, "saw", slide=-0.5, noise=0.5, decay=3))
        snd["wave"] = self._snd(layer([
            (i * 0.11, S(f, 0.30, 0.25, "triangle", decay=3))
            for i, f in enumerate((523.25, 659.25, 783.99, 1046.5))
        ]))
        snd["clear"] = self._snd(layer([
            (i * 0.09, S(f, 0.35, 0.22, "sine", decay=3))
            for i, f in enumerate((392.0, 523.25, 659.25, 783.99, 1046.5))
        ]))
        snd["boss"] = self._snd(layer([
            (0.0, S(110, 0.5, 0.45, "saw", vibrato=0.03, decay=2)),
            (0.55, S(98, 0.7, 0.45, "saw", vibrato=0.03, decay=2)),
        ]))
        snd["power"] = self._snd(layer([
            (i * 0.07, S(f, 0.25, 0.2, "sine", decay=3))
            for i, f in enumerate((880.0, 1174.7, 1568.0))
        ]))
        snd["combo"] = self._snd(layer([
            (0.0, S(784.0, 0.12, 0.2, "square", decay=5)),
            (0.08, S(1046.5, 0.18, 0.2, "square", decay=5)),
        ]))
        snd["freeze"] = self._snd(S(1400, 0.7, 0.28, "sine", slide=-0.75, vibrato=0.04, decay=2.5))
        snd["bomb"] = self._snd(layer([
            (0.0, S(70, 0.7, 0.7, "saw", slide=-0.5, noise=0.85, decay=4)),
            (0.0, S(200, 0.3, 0.3, "square", slide=-0.8, decay=5)),
        ]))
        snd["heal"] = self._snd(layer([
            (0.0, S(523.25, 0.3, 0.22, "sine", decay=3)),
            (0.12, S(783.99, 0.4, 0.22, "sine", decay=3)),
        ]))
        snd["move"] = self._snd(S(520, 0.05, 0.18, "square", decay=6))
        snd["select"] = self._snd(layer([
            (0.0, S(660, 0.08, 0.2, "square", decay=5)),
            (0.07, S(990, 0.12, 0.2, "square", decay=5)),
        ]))
        snd["over"] = self._snd(layer([
            (i * 0.22, S(f, 0.45, 0.3, "triangle", decay=2.5))
            for i, f in enumerate((392.0, 349.23, 311.13, 261.63, 196.0))
        ]))
        self._build_music()

    def _build_music(self):
        chords = [(220.00, 261.63, 329.63), (174.61, 220.00, 261.63),
                  (261.63, 329.63, 392.00), (196.00, 246.94, 293.66)]
        bass = [110.0, 87.31, 130.81, 98.0]
        pattern = [0, 1, 2, 1, 0, 1, 2, 1]
        parts = []
        for ci, ch in enumerate(chords):
            base = ci * 2.0
            parts.append((base, synth(bass[ci], 1.0, 0.30, "sine", decay=2.2)))
            for k, idx in enumerate(pattern):
                parts.append((base + k * 0.25, synth(ch[idx] * 2, 0.3, 0.13, "sine", decay=5)))
        self.music = self._snd(layer(parts, total=8.0))
        self.music.set_volume(0.55)


    @property
    def sound_on(self):
        return self.ok and self.settings.get("sound", True)

    def play(self, name, volume=1.0):
        if self.sound_on and name in self.sounds:
            snd = self.sounds[name]
            snd.set_volume(volume)
            snd.play()

    def play_key(self, combo):
        if self.sound_on and self.key_sounds:
            self.key_sounds[min(len(self.key_sounds) - 1, combo // 4)].play()

    def start_music(self):
        if self.ok and self.settings.get("music", True) and self.music is not None:
            if self.music_channel is None or not self.music_channel.get_busy():
                self.music_channel = self.music.play(loops=-1)

    def stop_music(self):
        if self.ok and self.music is not None:
            self.music.stop()
            self.music_channel = None


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "gravity")

    def __init__(self, x, y, vx, vy, life, color, size, gravity=0.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color, self.size, self.gravity = color, size, gravity

    def update(self, dt):
        self.life -= dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 1.0 - min(1.0, 1.5 * dt)

    def draw(self, s):
        r = int(self.size * clamp(self.life / self.max_life, 0.0, 1.0))
        if r >= 1:
            pygame.draw.circle(s, self.color, (int(self.x), int(self.y)), r)


class Ring:
    __slots__ = ("x", "y", "r", "max_r", "life", "max_life", "color")

    def __init__(self, x, y, max_r, life, color):
        self.x, self.y, self.r, self.max_r = x, y, 4.0, max_r
        self.life = self.max_life = life
        self.color = color

    def update(self, dt):
        self.life -= dt
        t = 1.0 - clamp(self.life / self.max_life, 0.0, 1.0)
        self.r = lerp(4.0, self.max_r, 1 - (1 - t) ** 3)

    def draw(self, s):
        t = clamp(self.life / self.max_life, 0.0, 1.0)
        pygame.draw.circle(s, mix(GRASS, self.color, t), (int(self.x), int(self.y)),
                           int(self.r), max(1, int(5 * t)))


class FloatingText:
    def __init__(self, text, x, y, color, font, life=1.0, vy=-45.0):
        self.text, self.x, self.y = text, x, y
        self.color, self.font = color, font
        self.life = self.max_life = life
        self.vy = vy

    def update(self, dt):
        self.life -= dt
        self.y += self.vy * dt
        self.vy *= 1.0 - min(1.0, 2.0 * dt)

    def draw(self, s):
        a = int(255 * clamp(self.life / (self.max_life * 0.5), 0.0, 1.0))
        draw_text(s, self.text, self.font, self.color, self.x, self.y, "center",
                  shadow=BLACK, alpha=a)


class Bullet:


    def __init__(self, x, y, target):
        self.x, self.y = x, y
        self.target = target
        self.tx, self.ty = target.x, target.y
        self.speed = 950.0
        self.alive = True
        self.trail = deque(maxlen=7)

    def update(self, dt):
        if self.target.alive:
            self.tx, self.ty = self.target.x, self.target.y
        dx, dy = self.tx - self.x, self.ty - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt
        self.trail.append((self.x, self.y))
        if dist <= step or dist < 4:
            self.alive = False
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        return False

    def draw(self, s):
        n = len(self.trail)
        for i, (px, py) in enumerate(self.trail):
            pygame.draw.circle(s, mix(GRASS, GOLD_LIGHT, (i + 1) / (n + 1)),
                               (int(px), int(py)), max(1, int(1 + 3 * i / max(1, n))))
        pygame.draw.circle(s, GOLD_LIGHT, (int(self.x), int(self.y)), 4)
        pygame.draw.circle(s, WHITE, (int(self.x), int(self.y)), 2)


KINDS = {
    "normal": dict(speed=1.00, radius=24, damage=1, score=1.0, shift=0, color=None, shape=None),
    "runner": dict(speed=1.90, radius=17, damage=1, score=1.4, shift=-2, color=(196, 132, 60), shape="triangle"),
    "tank":   dict(speed=0.60, radius=32, damage=2, score=1.8, shift=1, color=(96, 100, 110), shape="square"),
    "ghost":  dict(speed=1.00, radius=24, damage=1, score=1.6, shift=0, color=(150, 170, 190), shape="circle"),
    "boss":   dict(speed=0.40, radius=46, damage=4, score=4.0, shift=0, color=(120, 40, 60), shape="octagon"),
}
SHADOW = (44, 50, 35)


def edge_spawn_point():
    side = random.randint(0, 3)
    inset = 20
    if side == 0:
        return random.randint(MAP_X + inset, MAP_X + MAP_SIZE - inset), MAP_Y + inset
    if side == 1:
        return MAP_X + MAP_SIZE - inset, random.randint(MAP_Y + inset, MAP_Y + MAP_SIZE - inset)
    if side == 2:
        return random.randint(MAP_X + inset, MAP_X + MAP_SIZE - inset), MAP_Y + MAP_SIZE - inset
    return MAP_X + inset, random.randint(MAP_Y + inset, MAP_Y + MAP_SIZE - inset)


class Enemy:
    def __init__(self, kind, word, pos=None, target=None):
        spec = KINDS[kind]
        self.kind = kind
        self.word = word
        self.typed = ""
        self.base_radius = spec["radius"]
        self.speed_mult = spec["speed"] * random.uniform(0.9, 1.1)
        self.damage = spec["damage"]
        self.color = spec["color"] or random.choice(ENEMY_COLORS)
        self.shape = spec["shape"] or random.choice(["circle", "square", "triangle", "diamond"])
        self.target = target or (TOWER_X, TOWER_Y)
        self.alive = True
        self.age = 0.0
        self.shake = 0.0
        self.flash = 0.0
        self.phase = random.uniform(0, math.tau)
        self.dir = (0.0, 1.0)
        self.x, self.y = pos if pos is not None else edge_spawn_point()


    @property
    def radius(self):
        t = min(1.0, self.age / 0.45)
        return self.base_radius * (0.35 + 0.65 * (1 - (1 - t) ** 2))

    def distance(self):
        return math.hypot(self.target[0] - self.x, self.target[1] - self.y)

    def revealed(self, selected=False):
        if self.kind != "ghost":
            return True
        return selected or bool(self.typed) or self.distance() < 300


    def update(self, dt, speed):
        self.age += dt
        self.shake = max(0.0, self.shake - dt)
        self.flash = max(0.0, self.flash - dt)
        dx, dy = self.target[0] - self.x, self.target[1] - self.y
        dist = math.hypot(dx, dy)
        if dist > 0.001:
            self.dir = (dx / dist, dy / dist)
            step = speed * self.speed_mult * dt
            self.x += self.dir[0] * step
            self.y += self.dir[1] * step
            if self.kind == "runner":
                w = math.sin(self.age * 7 + self.phase) * 45 * dt
                self.x += -self.dir[1] * w
                self.y += self.dir[0] * w
        return dist < TOWER_RADIUS + self.base_radius * 0.6


    def _paint(self, s, cx, cy, r, selected):
        col = self.color
        body = lighten(col, 0.55) if self.flash > 0 else col
        border = GOLD if selected else darken(col, 0.55)
        draw_shape(s, self.shape, darken(col, 0.35), cx, cy + 3, r)
        draw_shape(s, self.shape, body, cx, cy, r * 0.96)
        if self.shape in ("circle", "square", "octagon"):
            pygame.draw.ellipse(s, lighten(body, 0.16),
                                (int(cx - r * 0.55), int(cy - r * 0.78), int(r * 0.7), int(r * 0.32)))
        draw_shape(s, self.shape, border, cx, cy, r, 3)

        if self.kind == "tank":
            for sx in (-1, 1):
                for sy in (-1, 1):
                    pygame.draw.circle(s, lighten(col, 0.35),
                                       (int(cx + sx * r * 0.68), int(cy + sy * r * 0.68)), 3)
        if self.kind == "boss":
            crown = [(cx - r * .5, cy - r * .9), (cx - r * .5, cy - r * 1.35),
                     (cx - r * .25, cy - r * 1.1), (cx, cy - r * 1.45),
                     (cx + r * .25, cy - r * 1.1), (cx + r * .5, cy - r * 1.35),
                     (cx + r * .5, cy - r * .9)]
            pygame.draw.polygon(s, GOLD, crown)
            pygame.draw.polygon(s, darken(GOLD, 0.5), crown, 2)


        er = max(2.0, r * 0.2)
        ey = cy - r * 0.12
        for sgn in (-1, 1):
            ex = cx + sgn * r * 0.36
            pygame.draw.circle(s, WHITE, (int(ex), int(ey)), int(er))
            pygame.draw.circle(s, BLACK, (int(ex + self.dir[0] * er * 0.45),
                                          int(ey + self.dir[1] * er * 0.45)), max(1, int(er * 0.55)))
            pygame.draw.line(s, BLACK, (ex + sgn * er * 1.2, ey - er * 1.9),
                             (ex - sgn * er * 1.1, ey - er * 1.0), 2)
        pygame.draw.line(s, BLACK, (cx - r * 0.25, cy + r * 0.4), (cx + r * 0.25, cy + r * 0.4), 2)

    def draw_body(self, s, selected, frozen, now):
        r = self.radius
        x = self.x + (random.uniform(-3, 3) if self.shake > 0 else 0)
        y = self.y + math.sin(self.age * 6 + self.phase) * 2.5
        pygame.draw.ellipse(s, SHADOW, (int(x - r), int(self.y + r * 0.7), int(r * 2), max(2, int(r * 0.6))))

        if self.kind == "runner":
            for i in range(3):
                off = r + 8 + i * 6
                px = -self.dir[1] * (i - 1) * 7
                py = self.dir[0] * (i - 1) * 7
                pygame.draw.line(s, darken(GRASS, 0.3),
                                 (x - self.dir[0] * off + px, y - self.dir[1] * off + py),
                                 (x - self.dir[0] * (off + 9) + px, y - self.dir[1] * (off + 9) + py), 2)

        if self.kind == "ghost":
            size = int(r * 2 + 40)
            tmp = pygame.Surface((size, size), pygame.SRCALPHA)
            self._paint(tmp, size / 2, size / 2, r, selected)
            tmp.set_alpha(int(150 + 60 * math.sin(now * 3 + self.phase)))
            s.blit(tmp, (int(x - size / 2), int(y - size / 2)))
        else:
            self._paint(s, x, y, r, selected)

        if frozen:
            pygame.draw.circle(s, (190, 235, 255), (int(x), int(y)), int(r + 5), 3)
            pygame.draw.circle(s, ICE, (int(x), int(y)), int(r + 9), 1)

    def draw_label(self, s, selected):
        font = F_WORD
        if self.revealed(selected):
            typed = self.typed
            rest = self.word[len(typed):]
        else:
            typed, rest = "", "?" * len(self.word)
        tw = font.size(typed)[0] if typed else 0
        rw = font.size(rest)[0] if rest else 0
        rect = pygame.Rect(0, 0, tw + rw + 18, font.get_height() + 8)
        rect.midbottom = (int(self.x), int(self.y - self.radius - 8))
        rect.clamp_ip(MAP_RECT.inflate(-10, -10))
        draw_panel(s, rect, (18, 16, 14), GOLD if selected else (110, 99, 83),
                   2 if selected else 1, 6, alpha=215 if selected else 170)
        x, y = rect.x + 9, rect.y + 4
        if typed:
            s.blit(render(typed, font, GOLD_LIGHT), (x, y))
            x += tw
        if rest:
            s.blit(render(rest, font, WHITE if selected else CREAM), (x, y))


def build_scenery(surf, area, rng, centers):

    pygame.draw.rect(surf, GRASS, area)
    surf.set_clip(area)

    def far(x, y, d):
        return all(math.hypot(x - cx, y - cy) > d for cx, cy in centers)

    for _ in range(int(area.w * area.h / 3500)):
        x = rng.randint(area.left, area.right)
        y = rng.randint(area.top, area.bottom)
        base = GRASS_DARK if rng.random() < 0.5 else GRASS_LIGHT
        pygame.draw.circle(surf, mix(GRASS, base, rng.uniform(0.0, 0.4)), (x, y), rng.randint(18, 55))

    for cx, cy in centers:
        for _ in range(16):
            a = rng.uniform(0, math.tau)
            d = rng.uniform(20, 70)
            pygame.draw.circle(surf, mix(DIRT, DIRT_DARK, rng.uniform(0, 0.4)),
                               (int(cx + math.cos(a) * d), int(cy + math.sin(a) * d)), rng.randint(30, 52))
        pygame.draw.circle(surf, DIRT_DARK, (cx, cy), 92, 3)

    for _ in range(int(area.w * area.h / 1400)):
        x = rng.randint(area.left, area.right)
        y = rng.randint(area.top, area.bottom)
        if not far(x, y, 95):
            continue
        c = rng.choice([GRASS_LIGHT, GRASS_DARK])
        for k in (-3, 0, 3):
            pygame.draw.line(surf, c, (x + k, y), (x + k * 2, y - rng.randint(4, 8)), 1)

    for _ in range(int(area.w * area.h / 9000)):
        x = rng.randint(area.left + 20, area.right - 20)
        y = rng.randint(area.top + 20, area.bottom - 20)
        if not far(x, y, 105):
            continue
        petal = rng.choice([CREAM, GOLD_LIGHT, (196, 98, 82)])
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            pygame.draw.circle(surf, petal, (x + dx, y + dy), 2)
        pygame.draw.circle(surf, GOLD, (x, y), 2)

    for _ in range(int(area.w * area.h / 12000)):
        x = rng.randint(area.left + 20, area.right - 20)
        y = rng.randint(area.top + 20, area.bottom - 20)
        if not far(x, y, 105):
            continue
        w = rng.randint(8, 16)
        pygame.draw.ellipse(surf, STONE_DARK, (x, y + 2, w, w // 2 + 3))
        pygame.draw.ellipse(surf, STONE, (x, y, w, w // 2 + 3))

    for _ in range(int(area.w * area.h / 30000) + 3):
        x = rng.randint(area.left + 30, area.right - 30)
        y = rng.randint(area.top + 40, area.bottom - 30)
        if not far(x, y, 150):
            continue
        pygame.draw.ellipse(surf, SHADOW, (x - 20, y + 8, 44, 16))
        pygame.draw.rect(surf, WOOD_DARK, (x - 4, y - 6, 8, 18))
        for dx, dy, r in ((0, -22, 20), (-12, -12, 15), (12, -12, 15)):
            pygame.draw.circle(surf, darken(GRASS_DARK, 0.15), (x + dx, y + dy), r)
        pygame.draw.circle(surf, GRASS, (x - 4, y - 24), 10)
    surf.set_clip(None)


def build_game_bg():
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill(BG)
    pygame.draw.rect(surf, GRASS_DARK, MAP_RECT)
    build_scenery(surf, MAP_RECT.inflate(-16, -16), random.Random(25), [(TOWER_X, TOWER_Y)])
    pygame.draw.rect(surf, WOOD_DARK, MAP_RECT, 6)
    pygame.draw.rect(surf, WOOD, MAP_RECT.inflate(-6, -6), 1)
    for cx in (MAP_RECT.left, MAP_RECT.right - 1):
        for cy in (MAP_RECT.top, MAP_RECT.bottom - 1):
            pygame.draw.circle(surf, GOLD, (cx, cy), 6)
            pygame.draw.circle(surf, darken(GOLD, 0.5), (cx, cy), 6, 2)
    draw_panel(surf, PANEL_RECT, (39, 35, 31), WOOD_DARK, 4, 6)
    return surf


def build_menu_bg():
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill(BG)
    build_scenery(surf, pygame.Rect(0, 0, WIDTH, HEIGHT), random.Random(7), [(MENU_TX, MENU_TY)])
    dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim.fill((20, 16, 12, 105))
    surf.blit(dim, (0, 0))
    return surf


def build_vignette():
    v = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(55):
        a = int(130 * (1 - i / 55) ** 2)
        pygame.draw.rect(v, (190, 25, 20, a), pygame.Rect(i, i, WIDTH - 2 * i, HEIGHT - 2 * i), 1)
    return v


class Game:
    def __init__(self):
        self.screen = SCREEN
        self.clock = pygame.time.Clock()
        self.running = True
        self.now = 0.0

        self.screen.fill(BG)
        draw_text(self.screen, "Loading...", F_BIG, CREAM, WIDTH // 2, HEIGHT // 2, "center")
        pygame.display.flip()

        self.save = SaveData()
        self.settings = self.save.data["settings"]
        self.audio = Audio(self.settings)

        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.game_bg = build_game_bg()
        self.menu_bg = build_menu_bg()
        self.vignette = build_vignette()
        self.night_surf = pygame.Surface(MAP_RECT.size)
        self.night_surf.fill((8, 12, 42))
        self.glow_torch = make_glow(70, (255, 170, 70), 190)
        self.glow_tower = make_glow(210, (255, 190, 100), 120)
        self.glow_fly = make_glow(10, (230, 255, 140), 230)

        rng = random.Random(3)
        self.clouds = []
        for _ in range(4):
            w, h = rng.randint(180, 280), rng.randint(70, 110)
            img = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(img, (0, 0, 0, 34), img.get_rect())
            self.clouds.append({"img": img, "x": rng.uniform(MAP_X, MAP_X + MAP_SIZE),
                                "y": rng.uniform(MAP_Y, MAP_Y + MAP_SIZE), "v": rng.uniform(8, 18)})
        self.fireflies = [{"x": rng.uniform(MAP_X, MAP_X + MAP_SIZE),
                           "y": rng.uniform(MAP_Y, MAP_Y + MAP_SIZE),
                           "p": rng.uniform(0, 6.28), "s": rng.uniform(10, 22)} for _ in range(16)]

        self.state = "menu"
        self.state_time = 0.0
        self.menu_index = 0
        self.demo_enemies = []
        self.demo_timer = 0.5

        self.particles = []
        self.rings = []
        self.floaters = []
        self.shake = 0.0
        self.reset_run()


    def reset_run(self):
        diff = DIFFICULTIES[self.settings["difficulty"]]
        self.diff = diff
        self.enemies = []
        self.bullets = []
        self.particles = []
        self.rings = []
        self.floaters = []
        self.selected = None

        self.score = 0
        self.kills = 0
        self.keys_total = 0
        self.keys_correct = 0
        self.combo = 0
        self.best_combo = 0
        self.max_hp = diff["hp"]
        self.hp = self.max_hp

        self.wave = 0
        self.wave_queue = []
        self.wave_total = 1
        self.wave_killed = 0
        self.wave_state = "intermission"
        self.intermission = 1.2
        self.spawn_timer = 0.0
        self.spawn_interval = 2.0
        self.max_on_screen = 3

        self.time = 0.0
        self.active_time = 0.0
        self.charges = {"freeze": 1, "bomb": 0, "heal": 0}
        self.freeze_timer = 0.0
        self.key_flash = {}
        self.key_errors = Counter()
        self.stroke_times = deque()
        self.wpm_samples = []
        self.next_sample = 2.0
        self.banner = None
        self.tower_kick = 0.0
        self.damage_flash = 0.0
        self.white_flash = 0.0
        self.night = 0.0
        self.night_target = 0.0
        self.new_record = False
        self.result = None

    def set_state(self, name):
        self.state = name
        self.state_time = self.now
        self.menu_index = 0
        if name == "menu":
            self.audio.stop_music()

    def start_game(self):
        self.reset_run()
        self.set_state("playing")
        self.audio.start_music()


    def base_speed(self):
        return (24 + 2.4 * min(self.wave, 25)) * self.diff["speed"]

    def multiplier(self):
        return 1.0 + min(self.combo // 10, 8) * 0.5

    def accuracy(self):
        return self.keys_correct / self.keys_total if self.keys_total else 1.0

    def live_wpm(self):
        while self.stroke_times and self.stroke_times[0] < self.time - 10:
            self.stroke_times.popleft()
        span = min(10.0, max(self.active_time, 1.0))
        return len(self.stroke_times) * 12.0 / span

    def avg_wpm(self):
        return (self.keys_correct / 5.0) / (max(self.active_time, 1.0) / 60.0)


    def start_wave(self):
        self.wave += 1
        w = self.wave
        boss = (w % 5 == 0)
        count = 5 + int(w * 1.8)
        if boss:
            count = max(4, count // 2)
        queue = []
        for _ in range(count):
            pool = ["normal"] * 6
            if w >= 2:
                pool += ["runner"] * min(4, w)
            if w >= 3:
                pool += ["tank"] * min(3, w - 1)
            if w >= 4:
                pool += ["ghost"] * min(3, w - 2)
            queue.append(random.choice(pool))
        if boss:
            queue.insert(min(2, len(queue)), "boss")
        self.wave_queue = queue
        self.wave_total = len(queue)
        self.wave_killed = 0
        self.wave_state = "active"
        self.spawn_interval = max(0.55, 2.3 - 0.12 * w) / self.diff["spawn"]
        self.spawn_timer = 0.3
        self.max_on_screen = min(7, 3 + w // 2)
        self.night_target = [0.0, 0.0, 0.25, 0.55, 0.75, 0.35][(w - 1) % 6]
        if boss:
            self.banner = dict(text="BOSS WAVE", sub=f"Wave {w}", t=0.0, dur=2.6, color=RED_BRIGHT)
            self.audio.play("boss")
            self.shake = max(self.shake, 8)
        else:
            self.banner = dict(text=f"WAVE {w}", sub="Get ready", t=0.0, dur=2.0, color=GOLD_LIGHT)
            self.audio.play("wave")

    def wave_clear(self):
        bonus = int(self.wave * 100 * self.diff["score"] + self.accuracy() * 100)
        self.score += bonus
        text = "WAVE CLEARED"
        sub = f"+{bonus} bonus"
        if self.hp < self.max_hp:
            self.hp += 1
            sub += "   +1 HP"
        self.banner = dict(text=text, sub=sub, t=0.0, dur=2.4, color=LEAF)
        self.audio.play("clear")
        self.wave_state = "intermission"
        self.intermission = 3.2

    def pick_word(self, kind):
        used = {e.word for e in self.enemies}
        if kind == "boss":
            pool = [p for p in BOSS_PHRASES if p not in used] or BOSS_PHRASES
            return random.choice(pool)
        tier = clamp((self.wave - 1) // 2 + KINDS[kind]["shift"], 0, len(TIERS) - 1)
        pool = list(TIERS[tier])
        if tier > 0 and random.random() < 0.25:
            pool += TIERS[tier - 1]
        firsts = {e.word[0] for e in self.enemies}
        cands = [w for w in pool if w not in used and w[0] not in firsts]
        if not cands:
            cands = [w for w in pool if w not in used]
        return random.choice(cands or pool)

    def spawn_enemy(self, kind):
        self.enemies.append(Enemy(kind, self.pick_word(kind)))


    def find_target(self, ch):
        best = None
        for e in self.enemies:
            if not e.alive or len(e.typed) >= len(e.word) or not e.revealed():
                continue
            if e.word[len(e.typed)] != ch:
                continue
            key = (0 if e.typed else 1, e.distance())
            if best is None or key < best[0]:
                best = (key, e)
        return best[1] if best else None

    def select_by_click(self, pos):
        best, best_d = None, 1e9
        for e in self.enemies:
            d = math.hypot(pos[0] - e.x, pos[1] - e.y)
            if e.alive and d <= e.radius + 15 and d < best_d:
                best, best_d = e, d
        self.selected = best
        if best:
            self.audio.play("move", 0.6)

    def handle_letter(self, ch):
        alive = [e for e in self.enemies if e.alive]
        if not alive:
            return
        target = self.selected if (self.selected and self.selected.alive) else None
        if target is None:
            if ch == " ":
                return
            target = self.find_target(ch)
            self.keys_total += 1
            if target is None:
                self.register_error(None, ch)
                return
            self.selected = target
        else:
            self.keys_total += 1

        expected = target.word[len(target.typed)]
        label = "SPACE" if ch == " " else ch.upper()
        if ch != expected:
            self.register_error(target, ch, expected)
            return


        self.key_flash[label] = (self.now, "ok")
        target.typed += ch
        target.flash = 0.12
        self.keys_correct += 1
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        self.stroke_times.append(self.time)
        self.score += int(5 * self.multiplier())
        self.tower_kick = 1.0
        self.bullets.append(Bullet(TOWER_X, TOWER_Y - 70, target))
        self.audio.play_key(self.combo)

        if self.combo % 10 == 0:
            self.floater(f"COMBO {self.combo}!", TOWER_X, TOWER_Y - 120, GOLD_LIGHT, F_MED, 1.3)
            self.audio.play("combo")
        if self.combo % 30 == 0:
            self.grant_charge()
        if target.typed == target.word:
            self.kill_enemy(target)

    def register_error(self, target, ch, expected=None):
        self.combo = 0
        self.damage_flash = max(self.damage_flash, 0.0)
        label = "SPACE" if ch == " " else ch.upper()
        self.key_flash[label] = (self.now, "bad")
        if expected:
            self.key_errors["SPACE" if expected == " " else expected.upper()] += 1
        if target:
            target.shake = 0.25
        self.audio.play("error", 0.8)

    def use_ability(self, name):
        if self.charges[name] <= 0:
            self.audio.play("error", 0.4)
            return
        alive = [e for e in self.enemies if e.alive]
        if name == "freeze":
            self.freeze_timer = FREEZE_TIME
            self.ring(TOWER_X, TOWER_Y, 520, 0.8, ICE)
            self.audio.play("freeze")
            self.floater("FROZEN", TOWER_X, TOWER_Y - 130, ICE, F_BIG, 1.4)
        elif name == "bomb":
            if not alive:
                self.audio.play("error", 0.4)
                return
            for e in list(alive):
                if e.kind == "boss":
                    self.floater("IMMUNE", e.x, e.y - 60, RED_BRIGHT, F_MED, 1.0)
                else:
                    self.kill_enemy(e, bomb=True)
            self.ring(TOWER_X, TOWER_Y, 560, 0.6, FIRE)
            self.white_flash = 0.5
            self.shake = max(self.shake, 18)
            self.audio.play("bomb")
        elif name == "heal":
            if self.hp >= self.max_hp:
                self.audio.play("error", 0.4)
                return
            self.hp = min(self.max_hp, self.hp + 3)
            self.burst(TOWER_X, TOWER_Y, LEAF, 22, 120, 1.0, 4, gravity=-60)
            self.floater("+HP", TOWER_X, TOWER_Y - 90, LEAF, F_BIG, 1.2)
            self.audio.play("heal")
        self.charges[name] -= 1

    def grant_charge(self, name=None):
        options = [n for n, _, _ in ABILITIES if self.charges[n] < MAX_CHARGES]
        if not options:
            self.score += 200
            self.floater("+200", TOWER_X, TOWER_Y - 150, GOLD_LIGHT, F_MED)
            return
        name = name or random.choice(options)
        self.charges[name] += 1
        label = next(l for n, l, _ in ABILITIES if n == name)
        color = next(c for n, _, c in ABILITIES if n == name)
        self.floater(f"+{label}", TOWER_X, TOWER_Y - 150, color, F_MED, 1.5)
        self.audio.play("power")


    def kill_enemy(self, e, bomb=False):
        e.alive = False
        self.kills += 1
        self.wave_killed += 1
        pts = int(len(e.word) * 10 * KINDS[e.kind]["score"] * self.multiplier() * self.diff["score"])
        if bomb:
            pts //= 2
        self.score += pts
        if self.selected is e:
            self.selected = None
        self.burst(e.x, e.y, e.color, 20 if e.kind != "boss" else 60, 220, 0.8, 5)
        self.burst(e.x, e.y, lighten(e.color, 0.5), 8, 120, 0.5, 3)
        self.floater(f"+{pts}", e.x, e.y - 20, GOLD_LIGHT, F_MED)
        self.audio.play("kill")
        if e.kind == "boss":
            self.shake = max(self.shake, 14)
            self.ring(e.x, e.y, 200, 0.7, GOLD)
            self.grant_charge()
            self.grant_charge()

    def enemy_reaches_tower(self, e):
        e.alive = False
        if self.selected is e:
            self.selected = None
        self.hp -= e.damage
        self.combo = 0
        self.wave_killed += 1
        self.shake = 14 + e.damage * 4
        self.damage_flash = 0.7
        self.burst(e.x, e.y, e.color, 26, 240, 0.9, 5)
        self.ring(TOWER_X, TOWER_Y, 120, 0.4, RED_BRIGHT)
        self.floater(f"-{e.damage}", TOWER_X, TOWER_Y - 100, RED_BRIGHT, F_BIG, 1.2)
        self.audio.play("hit")
        if self.hp <= 0:
            self.hp = 0
            self.end_game()

    def end_game(self):
        self.state = "gameover"
        self.state_time = self.now
        self.menu_index = 0
        self.audio.stop_music()
        self.audio.play("over")
        self.shake = max(self.shake, 24)

        acc = self.accuracy()
        wpm = self.avg_wpm()
        entry = {"score": self.score, "wave": self.wave, "wpm": round(wpm), "acc": round(acc * 100),
                 "diff": self.diff["name"], "date": time.strftime("%d/%m/%y")}
        hs = self.save.data["highscores"]
        hs.append(entry)
        hs.sort(key=lambda e: e["score"], reverse=True)
        del hs[10:]
        self.new_record = self.score > 0 and hs[0] is entry

        tot = self.save.data["totals"]
        tot["games"] += 1
        tot["words"] += self.kills
        tot["keys"] += self.keys_total
        tot["seconds"] += self.time
        ke = self.save.data["key_errors"]
        for k, v in self.key_errors.items():
            ke[k] = ke.get(k, 0) + v
        self.save.data["best_wpm"] = max(self.save.data.get("best_wpm", 0), round(wpm))
        self.save.save()

        self.result = {"score": self.score, "wave": self.wave, "kills": self.kills, "acc": acc,
                       "wpm": wpm, "combo": self.best_combo, "time": self.time,
                       "diff": self.diff["name"], "samples": list(self.wpm_samples),
                       "worst": self.key_errors.most_common(5)}


    def burst(self, x, y, color, n=18, speed=180, life=0.7, size=4, gravity=140):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(0.25, 1.0) * speed
            self.particles.append(Particle(x, y, math.cos(a) * sp, math.sin(a) * sp,
                                           random.uniform(0.5, 1.0) * life, color,
                                           random.uniform(0.6, 1.0) * size, gravity))

    def ring(self, x, y, max_r, life, color):
        self.rings.append(Ring(x, y, max_r, life, color))

    def floater(self, text, x, y, color, font, life=1.0):
        self.floaters.append(FloatingText(text, x, y, color, font, life))


    def menu_items(self):
        if self.state == "menu":
            return [("PLAY", "play"),
                    (f"DIFFICULTY   <  {DIFFICULTIES[self.settings['difficulty']]['name']}  >", "diff"),
                    (f"SOUND   {'ON' if self.settings['sound'] else 'OFF'}", "sound"),
                    (f"MUSIC   {'ON' if self.settings['music'] else 'OFF'}", "music"),
                    ("HIGH SCORES", "scores"), ("HOW TO PLAY", "howto"), ("QUIT", "quit")]
        if self.state == "paused":
            return [("RESUME", "resume"), ("RESTART", "restart"), ("MAIN MENU", "menu")]
        if self.state == "gameover":
            return [("PLAY AGAIN", "restart"), ("MAIN MENU", "menu")]
        return []

    def menu_layout(self):
        items = self.menu_items()
        rects = []
        if self.state == "menu":
            for i in range(len(items)):
                rects.append(pygame.Rect(60, 310 + i * 52, 400, 44))
        elif self.state == "paused":
            for i in range(len(items)):
                rects.append(pygame.Rect(WIDTH // 2 - 160, 330 + i * 56, 320, 46))
        elif self.state == "gameover":
            for i in range(len(items)):
                rects.append(pygame.Rect(WIDTH // 2 - 230 + i * 240, HEIGHT // 2 + 200, 220, 46))
        return rects

    def activate(self, action, direction=1):
        a = self.audio
        if action == "play" or action == "restart":
            a.play("select")
            self.start_game()
        elif action == "diff":
            self.settings["difficulty"] = (self.settings["difficulty"] + direction) % len(DIFFICULTIES)
            a.play("move")
        elif action == "sound":
            self.settings["sound"] = not self.settings["sound"]
            a.play("select")
        elif action == "music":
            self.settings["music"] = not self.settings["music"]
            if not self.settings["music"]:
                a.stop_music()
        elif action == "scores":
            a.play("select")
            self.set_state("scores")
        elif action == "howto":
            a.play("select")
            self.set_state("howto")
        elif action == "resume":
            self.state = "playing"
        elif action == "menu":
            a.play("select")
            self.set_state("menu")
        elif action == "quit":
            self.running = False

    def toggle_pause(self):
        if self.state == "playing":
            self.state = "paused"
            self.menu_index = 0
        elif self.state == "paused":
            self.state = "playing"


    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            self.running = False
            return
        if ev.type == getattr(pygame, "WINDOWFOCUSLOST", -1) and self.state == "playing":
            self.toggle_pause()
            return
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
                return
            if ev.key == pygame.K_F2:
                self.settings["sound"] = not self.settings["sound"]
                return
            self.handle_key(ev)
        elif ev.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.menu_layout()):
                if r.collidepoint(ev.pos) and self.menu_index != i:
                    self.menu_index = i
                    self.audio.play("move", 0.4)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.state == "playing":
                self.select_by_click(ev.pos)
            elif self.state in ("menu", "paused", "gameover"):
                items = self.menu_items()
                for i, r in enumerate(self.menu_layout()):
                    if r.collidepoint(ev.pos):
                        self.activate(items[i][1])
                        break
            elif self.state in ("scores", "howto"):
                self.set_state("menu")

    def handle_key(self, ev):
        st = self.state
        if st in ("scores", "howto"):
            if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
                self.set_state("menu")
            return
        if st in ("menu", "paused", "gameover"):
            items = self.menu_items()
            if st == "paused" and ev.key == pygame.K_ESCAPE:
                self.toggle_pause()
            elif ev.key in (pygame.K_UP, pygame.K_w):
                self.menu_index = (self.menu_index - 1) % len(items)
                self.audio.play("move", 0.5)
            elif ev.key in (pygame.K_DOWN, pygame.K_s):
                self.menu_index = (self.menu_index + 1) % len(items)
                self.audio.play("move", 0.5)
            elif ev.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                if items[self.menu_index][1] == "diff":
                    self.activate("diff", -1 if ev.key in (pygame.K_LEFT, pygame.K_a) else 1)
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if st == "gameover" and self.now - self.state_time < 0.6:
                    return
                self.activate(items[self.menu_index][1])
            elif ev.key == pygame.K_ESCAPE and st == "gameover":
                self.set_state("menu")
            elif ev.key == pygame.K_F1 and st != "menu":
                self.start_game()
            return


        if ev.key == pygame.K_ESCAPE:
            self.toggle_pause()
        elif ev.key == pygame.K_F1:
            self.start_game()
        elif ev.key == pygame.K_TAB:
            self.selected = None
        elif ev.key == pygame.K_1:
            self.use_ability("freeze")
        elif ev.key == pygame.K_2:
            self.use_ability("bomb")
        elif ev.key == pygame.K_3:
            self.use_ability("heal")
        elif ev.unicode and ev.unicode.isascii() and (ev.unicode.isalpha() or ev.unicode == " "):
            self.handle_letter(ev.unicode.lower())


    def update(self, dt):
        self.shake = max(0.0, self.shake - 40 * dt)
        self.damage_flash = max(0.0, self.damage_flash - dt)
        self.white_flash = max(0.0, self.white_flash - dt * 2)

        for coll in (self.particles, self.rings, self.floaters):
            for o in coll:
                o.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        self.rings = [r for r in self.rings if r.life > 0]
        self.floaters = [f for f in self.floaters if f.life > 0]

        if self.state == "menu":
            self.update_demo(dt)
        elif self.state == "playing":
            self.update_play(dt)
            self.update_ambient(dt)
        elif self.state in ("paused", "gameover"):
            self.update_ambient(dt * (0.0 if self.state == "paused" else 1.0))

        if self.banner:
            if self.state == "playing":
                self.banner["t"] += dt
            if self.banner["t"] >= self.banner["dur"]:
                self.banner = None

    def update_ambient(self, dt):
        for c in self.clouds:
            c["x"] += c["v"] * dt
            if c["x"] > MAP_X + MAP_SIZE + 20:
                c["x"] = MAP_X - c["img"].get_width()
        for f in self.fireflies:
            f["p"] += dt
            f["x"] += math.cos(f["p"] * 0.7) * f["s"] * dt
            f["y"] += math.sin(f["p"] * 0.9) * f["s"] * dt
            f["x"] = clamp(f["x"], MAP_X + 10, MAP_X + MAP_SIZE - 10)
            f["y"] = clamp(f["y"], MAP_Y + 10, MAP_Y + MAP_SIZE - 10)
        self.night += (self.night_target - self.night) * min(1.0, dt * 0.6)

    def update_demo(self, dt):
        self.demo_timer -= dt
        if self.demo_timer <= 0 and len(self.demo_enemies) < 6:
            a = random.uniform(-1.3, 1.3)
            pos = (MENU_TX + math.cos(a) * 560, MENU_TY + math.sin(a) * 440)
            kind = random.choice(["normal", "normal", "runner", "tank", "ghost"])
            e = Enemy(kind, "", pos=pos, target=(MENU_TX, MENU_TY))
            e.age = 1.0
            self.demo_enemies.append(e)
            self.demo_timer = random.uniform(0.9, 1.8)
        for e in self.demo_enemies:
            if e.update(dt, 70):
                e.alive = False
                self.burst(e.x, e.y, e.color, 18, 200, 0.8, 5)
                self.shake = max(self.shake, 3)
                self.audio.play("hit", 0.15)
        self.demo_enemies = [e for e in self.demo_enemies if e.alive]
        self.tower_kick = max(0.0, self.tower_kick - dt * 6)

    def update_play(self, dt):
        self.time += dt
        self.enemies = [e for e in self.enemies if e.alive]
        if self.selected is not None and not self.selected.alive:
            self.selected = None
        self.freeze_timer = max(0.0, self.freeze_timer - dt)
        frozen = self.freeze_timer > 0
        self.tower_kick = max(0.0, self.tower_kick - dt * 6)

        if self.wave_state == "intermission":
            self.intermission -= dt
            if self.intermission <= 0:
                self.start_wave()
        else:
            self.active_time += dt
            if not frozen:
                self.spawn_timer -= dt
                if not self.enemies and self.wave_queue:
                    self.spawn_timer = min(self.spawn_timer, 0.35)
                if (self.wave_queue and self.spawn_timer <= 0
                        and len(self.enemies) < self.max_on_screen):
                    self.spawn_enemy(self.wave_queue.pop(0))
                    self.spawn_timer = self.spawn_interval * random.uniform(0.75, 1.25)
            if not self.wave_queue and not self.enemies:
                self.wave_clear()

        speed = 0.0 if frozen else self.base_speed()
        for e in list(self.enemies):
            if e.alive and e.update(dt, speed):
                self.enemy_reaches_tower(e)
                if self.state != "playing":
                    return

        for b in self.bullets:
            if b.update(dt):
                self.burst(b.tx, b.ty, GOLD_LIGHT, 5, 110, 0.3, 3, 0)
        self.bullets = [b for b in self.bullets if b.alive]

        if self.active_time >= self.next_sample:
            self.wpm_samples.append(self.live_wpm())
            self.next_sample += 2.0


    def draw(self):
        c = self.canvas
        st = self.state
        if st == "menu":
            self.draw_menu(c)
        elif st == "howto":
            self.draw_howto(c)
        elif st == "scores":
            self.draw_scores(c)
        else:
            self.draw_game(c)
            if st == "paused":
                self.draw_pause(c)
            elif st == "gameover":
                self.draw_gameover(c)

        ox = oy = 0
        if self.shake > 0.5:
            s = int(self.shake)
            ox, oy = random.randint(-s, s), random.randint(-s, s)
        self.screen.fill((20, 17, 14))
        self.screen.blit(c, (ox, oy))
        pygame.display.flip()


    def draw_tower(self, c, cx, cy, aim=None, hp_bar=True):
        now = self.now
        pygame.draw.ellipse(c, SHADOW, (cx - 62, cy + 28, 124, 34))
        pygame.draw.rect(c, STONE_DARK, (cx - 54, cy + 26, 108, 22), border_radius=4)
        pygame.draw.rect(c, STONE, (cx - 54, cy + 26, 108, 8), border_radius=4)

        body = pygame.Rect(cx - 44, cy - 44, 88, 78)
        pygame.draw.rect(c, WOOD_DARK, body.inflate(8, 8), border_radius=6)
        pygame.draw.rect(c, WOOD, body, border_radius=4)
        for i in range(1, 5):
            x = body.x + i * body.w // 5
            pygame.draw.line(c, WOOD_DARK, (x, body.y + 3), (x, body.bottom - 3), 1)
        pygame.draw.rect(c, WOOD_LIGHT, (body.x, body.y, body.w, 5), border_radius=3)


        for i in range(5):
            pygame.draw.rect(c, WOOD_DARK, (cx - 52 + i * 22, cy - 58, 14, 18), border_radius=2)
            pygame.draw.rect(c, WOOD, (cx - 50 + i * 22, cy - 56, 10, 14), border_radius=2)


        pygame.draw.polygon(c, RED_DARK, [(cx - 62, cy - 40), (cx, cy - 92), (cx + 62, cy - 40)])
        pygame.draw.polygon(c, RED, [(cx - 53, cy - 42), (cx, cy - 83), (cx + 53, cy - 42)])
        pygame.draw.line(c, RED_DARK, (cx, cy - 83), (cx, cy - 42), 2)


        ang = -math.pi / 2
        if aim is not None:
            ang = math.atan2(aim[1] - (cy - 70), aim[0] - cx)
        k = self.tower_kick * 4
        bx, by = cx, cy - 70
        tip = (bx + math.cos(ang) * (26 - k), by + math.sin(ang) * (26 - k))
        pygame.draw.line(c, WOOD_DARK, (bx, by), tip, 7)
        pygame.draw.line(c, WOOD_LIGHT, (bx, by), tip, 3)
        pygame.draw.circle(c, GOLD, (int(tip[0]), int(tip[1])), 4)
        pygame.draw.circle(c, GOLD_LIGHT, (bx, by), 6)


        pygame.draw.rect(c, BLACK, (cx - 15, cy + 2, 30, 32), border_top_left_radius=15, border_top_right_radius=15)
        pygame.draw.rect(c, WOOD_DARK, (cx - 13, cy + 4, 26, 30), border_top_left_radius=13, border_top_right_radius=13)
        pygame.draw.circle(c, GOLD, (cx + 8, cy + 20), 2)
        flick = 0.75 + 0.25 * math.sin(now * 9 + 1.3)
        for dx in (-27, 27):
            w = pygame.Rect(cx + dx - 8, cy - 22, 16, 18)
            pygame.draw.rect(c, mix(CREAM_DARK, GOLD_LIGHT, flick), w, border_radius=3)
            pygame.draw.rect(c, WOOD_DARK, w, 2, border_radius=3)
            pygame.draw.line(c, WOOD_DARK, (w.centerx, w.top), (w.centerx, w.bottom), 1)


        for dx in (-66, 66):
            tx, ty = cx + dx, cy + 14
            pygame.draw.rect(c, WOOD_DARK, (tx - 3, ty, 6, 26))
            fl = 8 + 3 * math.sin(now * 12 + dx)
            pygame.draw.ellipse(c, FIRE, (tx - 6, ty - fl - 2, 12, fl + 8))
            pygame.draw.ellipse(c, GOLD_LIGHT, (tx - 3, ty - fl * 0.6, 6, fl * 0.7 + 4))


        pygame.draw.line(c, WOOD_DARK, (cx, cy - 92), (cx, cy - 122), 3)
        pts = [(cx + 2, cy - 121)]
        for i in range(1, 7):
            pts.append((cx + 2 + i * 5, cy - 121 + math.sin(now * 5 + i * 0.8) * 2.5))
        flag = pts + [(p[0], p[1] + 12) for p in reversed(pts)]
        pygame.draw.polygon(c, RED_BRIGHT, flag)
        pygame.draw.polygon(c, RED_DARK, flag, 1)

        if hp_bar:
            bw, bh = 124, 12
            bar = pygame.Rect(cx - bw // 2, cy + 66, bw, bh)
            ratio = clamp(self.hp / max(1, self.max_hp), 0.0, 1.0)
            pygame.draw.rect(c, BLACK, bar.inflate(4, 4), border_radius=5)
            if ratio > 0:
                col = mix(RED_BRIGHT, LEAF, ratio)
                pygame.draw.rect(c, col, (bar.x, bar.y, int(bw * ratio), bh), border_radius=4)
            draw_text(c, f"TOWER  {self.hp}/{self.max_hp}", F_TINY, CREAM, cx, cy + 90, "center", shadow=BLACK)


    def draw_game(self, c):
        c.blit(self.game_bg, (0, 0))
        c.set_clip(MAP_RECT.inflate(-6, -6))
        now = self.now

        for cl in self.clouds:
            c.blit(cl["img"], (int(cl["x"]), int(cl["y"])))

        sel = self.selected if (self.selected and self.selected.alive) else None
        if sel:
            pygame.draw.line(c, mix(GRASS, GOLD, 0.5), (sel.x, sel.y), (TOWER_X, TOWER_Y - 40), 2)

        frozen = self.freeze_timer > 0
        ordered = sorted(self.enemies, key=lambda e: e.y)
        for e in ordered:
            e.draw_body(c, e is sel, frozen, now)
        if sel:
            rr = int(sel.radius + 12 + math.sin(now * 6) * 2)
            rect = pygame.Rect(int(sel.x - rr), int(sel.y - rr), rr * 2, rr * 2)
            for k in range(4):
                a = now * 2 + k * math.pi / 2
                pygame.draw.arc(c, GOLD_LIGHT, rect, a, a + 0.8, 3)

        self.draw_tower(c, TOWER_X, TOWER_Y, aim=(sel.x, sel.y) if sel else None)

        if self.night > 0.02:
            self.night_surf.set_alpha(int(self.night * 150))
            c.blit(self.night_surf, MAP_RECT.topleft)
            self.glow_tower.set_alpha(int(255 * self.night))
            c.blit(self.glow_tower, (TOWER_X - 210, TOWER_Y - 210))
        flick = 0.8 + 0.2 * math.sin(now * 11)
        self.glow_torch.set_alpha(int(255 * (0.25 + 0.75 * self.night) * flick))
        for dx in (-66, 66):
            c.blit(self.glow_torch, (TOWER_X + dx - 70, TOWER_Y + 10 - 70))
        if self.night > 0.15:
            for f in self.fireflies:
                self.glow_fly.set_alpha(int(255 * self.night * (0.5 + 0.5 * math.sin(f["p"] * 3))))
                c.blit(self.glow_fly, (int(f["x"]) - 10, int(f["y"]) - 10))

        for e in ordered:
            e.draw_label(c, e is sel)
        for b in self.bullets:
            b.draw(c)
        for r in self.rings:
            r.draw(c)
        for p in self.particles:
            p.draw(c)
        for f in self.floaters:
            f.draw(c)
        c.set_clip(None)

        if self.white_flash > 0:
            fl = pygame.Surface(MAP_RECT.size)
            fl.fill(WHITE)
            fl.set_alpha(int(200 * self.white_flash))
            c.blit(fl, MAP_RECT.topleft)
        if self.damage_flash > 0:
            self.vignette.set_alpha(int(255 * clamp(self.damage_flash / 0.7, 0, 1)))
            c.blit(self.vignette, (0, 0))
        if self.hp <= max(2, self.max_hp // 4) and self.state == "playing":
            self.vignette.set_alpha(int(60 + 40 * math.sin(now * 5)))
            c.blit(self.vignette, (0, 0))

        self.draw_banner(c)
        self.draw_header(c)
        self.draw_side_panel(c)

    def draw_banner(self, c):
        b = self.banner
        if not b:
            return
        t, dur = b["t"], b["dur"]
        a = int(255 * clamp(min(t / 0.3, (dur - t) / 0.6), 0.0, 1.0))
        cx, cy = MAP_X + MAP_SIZE // 2, MAP_Y + 150
        draw_text(c, b["text"], F_TITLE, b["color"], cx, cy, "center", shadow=BLACK, alpha=a)
        draw_text(c, b["sub"], F_MED, CREAM, cx, cy + 42, "center", shadow=BLACK, alpha=a)

    def draw_header(self, c):
        draw_text(c, "TYPING TOWER", F_BIG, CREAM, 45, 8)
        draw_text(c, f"WAVE {max(1, self.wave)}", F_MED, GOLD, 300, 14)
        draw_text(c, self.diff["name"], F_SMALL, CREAM_DARK, 400, 18)
        draw_text(c, f"SCORE  {self.score}", F_MED, CREAM, MAP_X + MAP_SIZE, 14, "topright")

        bar = pygame.Rect(MAP_X, 654, MAP_SIZE, 12)
        pygame.draw.rect(c, BLACK, bar.inflate(4, 4), border_radius=6)
        if self.wave_state == "active" and self.wave_total:
            ratio = clamp(self.wave_killed / self.wave_total, 0.0, 1.0)
            if ratio > 0:
                pygame.draw.rect(c, GOLD, (bar.x, bar.y, int(bar.w * ratio), bar.h), border_radius=5)
        elif self.wave_state == "intermission" and self.wave > 0:
            pygame.draw.rect(c, LEAF, bar, border_radius=5)
        draw_text(c, "TAB release target    1 Freeze    2 Bomb    3 Heal    F2 sound    F11 fullscreen",
                  F_TINY, CREAM_DARK, MAP_X, 678)


    def draw_key(self, c, rect, label, color, pressed, font=F_MED):
        off = 2 if pressed else 0
        pygame.draw.rect(c, darken(color, 0.5), (rect.x, rect.y + 4, rect.w, rect.h), border_radius=6)
        top = pygame.Rect(rect.x, rect.y + off, rect.w, rect.h)
        pygame.draw.rect(c, color, top, border_radius=6)
        pygame.draw.rect(c, KEY_BORDER, top, 2, border_radius=6)
        draw_text(c, label, font, CREAM, top.centerx, top.centery, "center")

    def key_color(self, label, nxt):
        fl = self.key_flash.get(label)
        if fl and self.now - fl[0] < 0.18:
            return (KEY_ACTIVE if fl[1] == "ok" else KEY_BAD), True
        if nxt == label:
            return mix(KEY_NORMAL, KEY_NEXT, 0.6 + 0.4 * math.sin(self.now * 6)), False
        return KEY_NORMAL, False

    def draw_side_panel(self, c):
        px = PANEL_RECT.centerx
        draw_text(c, "KEYBOARD", F_MED, CREAM, px, 70, "center")

        sel = self.selected if (self.selected and self.selected.alive) else None
        nxt = None
        if sel and len(sel.typed) < len(sel.word):
            ch = sel.word[len(sel.typed)]
            nxt = "SPACE" if ch == " " else ch.upper()

        row0_w = 10 * KEY_W + 9 * KEY_GAP
        left = px - row0_w // 2
        y = 100
        for ri, row in enumerate(KEYBOARD_ROWS):
            x = left + ROW_STAGGER[ri] * (KEY_W + KEY_GAP)
            for letter in row:
                col, pressed = self.key_color(letter, nxt)
                self.draw_key(c, pygame.Rect(int(x), y, KEY_W, KEY_H), letter, col, pressed)
                x += KEY_W + KEY_GAP
            y += KEY_H + 10
        col, pressed = self.key_color("SPACE", nxt)
        self.draw_key(c, pygame.Rect(px - 130, y, 260, 34), "SPACE", col, pressed, F_SMALL)


        ay = 316
        for i, (name, label, color) in enumerate(ABILITIES):
            r = pygame.Rect(742 + i * 160, ay, 150, 66)
            n = self.charges[name]
            draw_panel(c, r, (50, 45, 40), color if n > 0 else KEY_BORDER, 2, 8)
            pygame.draw.rect(c, color if n > 0 else KEY_NORMAL, (r.x + 8, r.y + 8, 22, 22), border_radius=5)
            draw_text(c, str(i + 1), F_SMALL, BLACK if n > 0 else CREAM_DARK, r.x + 19, r.y + 19, "center")
            draw_text(c, label, F_SMALL, CREAM if n > 0 else CREAM_DARK, r.x + 40, r.y + 12)
            for k in range(MAX_CHARGES):
                pos = (r.x + 16 + k * 18, r.bottom - 15)
                if k < n:
                    pygame.draw.circle(c, color, pos, 6)
                pygame.draw.circle(c, KEY_BORDER, pos, 6, 1)
            if name == "freeze" and self.freeze_timer > 0:
                w = int((r.w - 8) * self.freeze_timer / FREEZE_TIME)
                pygame.draw.rect(c, ICE, (r.x + 4, r.bottom - 6, w, 3))

        pygame.draw.line(c, KEY_BORDER, (750, 402), (1200, 402), 2)


        mult = self.multiplier()
        acc = int(self.accuracy() * 100)
        stats = [
            ("SCORE", str(self.score), CREAM), ("WAVE", str(max(1, self.wave)), GOLD),
            ("WORDS", str(self.kills), CREAM), ("COMBO", f"{self.combo}   x{mult:.1f}", GOLD_LIGHT if self.combo >= 10 else CREAM),
            ("WPM", f"{self.live_wpm():.0f}", CREAM), ("ACCURACY", f"{acc}%", LEAF if acc >= 95 else CREAM),
        ]
        for i, (label, value, color) in enumerate(stats):
            x = 750 + (i % 2) * 230
            yy = 412 + (i // 2) * 42
            draw_text(c, label, F_TINY, CREAM_DARK, x, yy)
            draw_text(c, value, F_MED, color, x, yy + 15)


        gr = pygame.Rect(750, 540, 450, 44)
        draw_panel(c, gr, (30, 27, 24), KEY_BORDER, 1, 4)
        samples = self.wpm_samples[-40:] + [self.live_wpm()]
        if len(samples) >= 2:
            top = max(40.0, max(samples))
            pts = [(gr.x + 4 + i * (gr.w - 8) / (len(samples) - 1),
                    gr.bottom - 4 - (v / top) * (gr.h - 8)) for i, v in enumerate(samples)]
            pygame.draw.lines(c, GOLD, False, pts, 2)
        draw_text(c, "WPM", F_TINY, CREAM_DARK, gr.x + 6, gr.y + 3)


        ty = 604
        if sel:
            draw_text(c, "TARGET", F_TINY, CREAM_DARK, px, ty, "center")
            font = F_WORD
            tw = font.size(sel.typed)[0] if sel.typed else 0
            rest = sel.word[len(sel.typed):]
            rw = font.size(rest)[0] if rest else 0
            x = px - (tw + rw) // 2
            if sel.typed:
                c.blit(render(sel.typed, font, GOLD_LIGHT), (x, ty + 16))
            if rest:
                c.blit(render(rest, font, CREAM), (x + tw, ty + 16))
        elif self.wave_state == "intermission" and self.wave_total and self.wave > 0:
            draw_text(c, f"NEXT WAVE IN {max(0, math.ceil(self.intermission))}", F_SMALL, CREAM_DARK, px, ty + 24, "center")
        else:
            draw_text(c, "TYPE A LETTER TO LOCK ON", F_SMALL, CREAM_DARK, px, ty + 24, "center")


    def draw_pause(self, c):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((20, 18, 16, 195))
        c.blit(ov, (0, 0))
        draw_text(c, "PAUSED", F_TITLE, CREAM, WIDTH // 2, 250, "center", shadow=BLACK)
        draw_text(c, "ESC to resume", F_SMALL, CREAM_DARK, WIDTH // 2, 295, "center")
        self.draw_buttons(c)

    def draw_buttons(self, c):
        items = self.menu_items()
        for i, (r, (label, _)) in enumerate(zip(self.menu_layout(), items)):
            sel = (i == self.menu_index)
            fill = (70, 52, 38) if sel else (40, 34, 29)
            draw_panel(c, r, fill, GOLD if sel else KEY_BORDER, 2 if sel else 1, 8, alpha=235)
            draw_text(c, label, F_MED, GOLD_LIGHT if sel else CREAM, r.centerx if self.state != "menu" else r.x + 20,
                      r.centery, "center" if self.state != "menu" else "midleft")

    def draw_menu(self, c):
        c.blit(self.menu_bg, (0, 0))
        for e in sorted(self.demo_enemies, key=lambda e: e.y):
            e.draw_body(c, False, False, self.now)
        self.draw_tower(c, MENU_TX, MENU_TY, aim=None, hp_bar=False)
        for r in self.rings:
            r.draw(c)
        for p in self.particles:
            p.draw(c)

        draw_panel(c, (30, 30, 470, 660), (20, 17, 14), WOOD_DARK, 4, 12, alpha=185)
        draw_text(c, "TYPING", F_HUGE, CREAM, 60, 45, shadow=WOOD_DARK)
        draw_text(c, "TOWER", F_HUGE, GOLD_LIGHT, 60, 135, shadow=WOOD_DARK)
        draw_text(c, "Type fast. Defend the tower.", F_SMALL, CREAM_DARK, 62, 255)
        self.draw_buttons(c)

        d = self.save.data
        hs = d["highscores"][0]["score"] if d["highscores"] else 0
        draw_text(c, f"BEST SCORE  {hs}      BEST WPM  {d.get('best_wpm', 0)}", F_SMALL, CREAM_DARK, 62, 660)
        draw_text(c, "UP/DOWN + ENTER, or use the mouse", F_TINY, CREAM_DARK, 62, 640)

    def draw_howto(self, c):
        c.blit(self.menu_bg, (0, 0))
        draw_panel(c, (140, 50, 1000, 620), (20, 17, 14), WOOD_DARK, 4, 12, alpha=225)
        draw_text(c, "HOW TO PLAY", F_TITLE, GOLD_LIGHT, WIDTH // 2, 95, "center", shadow=BLACK)
        lines = [
            ("Type the word shown above a monster to destroy it. The first letter locks the target.", CREAM),
            ("A wrong letter breaks your combo. TAB (or a click) releases the current target.", CREAM),
            ("", CREAM),
            ("MONSTERS", GOLD),
            ("Normal ........ plain old monsters", CREAM),
            ("Runner ........ fast and wobbly, short words", CREAM),
            ("Tank .......... slow, long words, hits for 2", CREAM),
            ("Ghost ......... its word stays hidden until it gets close", CREAM),
            ("Boss .......... every 5th wave, types a phrase (use SPACE), hits for 4", CREAM),
            ("", CREAM),
            ("ABILITIES  (earn one every 30-letter streak or by defeating a boss)", GOLD),
            ("[1] FREEZE stops all monsters for a few seconds", ICE),
            ("[2] BOMB destroys every monster on screen (bosses are immune)", FIRE),
            ("[3] HEAL restores 3 tower HP", LEAF),
            ("", CREAM),
            ("ESC pause   F1 restart   F2 sound   F11 fullscreen", CREAM_DARK),
        ]
        y = 150
        for text, color in lines:
            if text:
                draw_text(c, text, F_SMALL if color != GOLD else F_MED, color, 190, y)
            y += 30 if text else 14
        draw_text(c, "Press any key to go back", F_SMALL, CREAM_DARK, WIDTH // 2, 640, "center")

    def draw_scores(self, c):
        c.blit(self.menu_bg, (0, 0))
        draw_panel(c, (190, 50, 900, 620), (20, 17, 14), WOOD_DARK, 4, 12, alpha=225)
        draw_text(c, "HIGH SCORES", F_TITLE, GOLD_LIGHT, WIDTH // 2, 95, "center", shadow=BLACK)
        cols = [("#", 225), ("SCORE", 275), ("WAVE", 420), ("WPM", 510), ("ACC", 600), ("MODE", 690), ("DATE", 820)]
        for name, x in cols:
            draw_text(c, name, F_SMALL, CREAM_DARK, x, 150)
        pygame.draw.line(c, KEY_BORDER, (220, 176), (1050, 176), 2)
        hs = self.save.data["highscores"]
        if not hs:
            draw_text(c, "No games played yet.", F_MED, CREAM_DARK, WIDTH // 2, 300, "center")
        for i, e in enumerate(hs[:10]):
            y = 190 + i * 32
            color = GOLD_LIGHT if i == 0 else CREAM
            vals = [str(i + 1), str(e["score"]), str(e["wave"]), str(e["wpm"]), f"{e['acc']}%", e["diff"], e["date"]]
            for (name, x), v in zip(cols, vals):
                draw_text(c, v, F_SMALL, color, x, y)
        t = self.save.data["totals"]
        mins = int(t["seconds"] // 60)
        draw_text(c, f"Games {t['games']}    Words {t['words']}    Keys {t['keys']}    Time {mins} min    "
                     f"Best WPM {self.save.data.get('best_wpm', 0)}", F_SMALL, CREAM_DARK, WIDTH // 2, 600, "center")
        draw_text(c, "Press any key to go back", F_SMALL, CREAM_DARK, WIDTH // 2, 635, "center")

    def draw_gameover(self, c):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((20, 15, 13, 215))
        c.blit(ov, (0, 0))
        panel = pygame.Rect(0, 0, 900, 560)
        panel.center = (WIDTH // 2, HEIGHT // 2 - 10)
        draw_panel(c, panel, (30, 26, 22), WOOD_DARK, 4, 12, alpha=245)
        r = self.result
        if not r:
            return
        title = "NEW HIGH SCORE!" if self.new_record else "THE TOWER FELL"
        draw_text(c, title, F_TITLE, GOLD_LIGHT if self.new_record else CREAM, panel.centerx, panel.y + 50,
                  "center", shadow=BLACK)

        rows = [("Score", str(r["score"])), ("Wave reached", str(r["wave"])), ("Words destroyed", str(r["kills"])),
                ("Accuracy", f"{r['acc'] * 100:.0f}%"), ("Average WPM", f"{r['wpm']:.0f}"),
                ("Best combo", str(r["combo"])), ("Time", f"{int(r['time'] // 60)}:{int(r['time'] % 60):02d}"),
                ("Difficulty", r["diff"])]
        for i, (k, v) in enumerate(rows):
            y = panel.y + 100 + i * 34
            draw_text(c, k, F_SMALL, CREAM_DARK, panel.x + 50, y)
            draw_text(c, v, F_MED, GOLD_LIGHT if i == 0 else CREAM, panel.x + 300, y - 4, "topright")

        gx, gy = panel.x + 440, panel.y + 120
        draw_text(c, "WPM OVER TIME", F_SMALL, CREAM_DARK, gx, gy - 24)
        gr = pygame.Rect(gx, gy, 410, 150)
        draw_panel(c, gr, (22, 20, 17), KEY_BORDER, 1, 4)
        s = r["samples"]
        if len(s) >= 2:
            top = max(40.0, max(s))
            pts = [(gr.x + 8 + i * (gr.w - 16) / (len(s) - 1), gr.bottom - 8 - (v / top) * (gr.h - 16))
                   for i, v in enumerate(s)]
            pygame.draw.lines(c, GOLD, False, pts, 3)
            draw_text(c, f"{top:.0f}", F_TINY, CREAM_DARK, gr.x + 6, gr.y + 4)
        else:
            draw_text(c, "Not enough data", F_SMALL, CREAM_DARK, gr.centerx, gr.centery, "center")

        draw_text(c, "MOST MISSED KEYS", F_SMALL, CREAM_DARK, gx, gy + 180)
        if r["worst"]:
            for i, (k, n) in enumerate(r["worst"]):
                kr = pygame.Rect(gx + i * 80, gy + 210, 66, 46)
                self.draw_key(c, kr, k if len(k) == 1 else "SP", KEY_NORMAL, False)
                draw_text(c, f"x{n}", F_SMALL, RED_BRIGHT, kr.centerx, kr.bottom + 16, "center")
        else:
            draw_text(c, "Perfect typing!", F_SMALL, LEAF, gx, gy + 215)

        self.draw_buttons(c)


    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.now = pygame.time.get_ticks() / 1000.0
            for ev in pygame.event.get():
                self.handle_event(ev)
            self.update(dt)
            self.draw()
        self.save.save()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
    sys.exit()