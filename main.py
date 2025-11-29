# main.py — Симулятор Бога Ultimate 2025 (веб-версия для GitHub Pages)
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from random import random, randint, choice
from math import sin, cos, radians
import time

app = Ursina()
window.title = 'СИМУЛЯТОР БОГА'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# === Настройки для веба ===
CHUNK_SIZE = 10
RENDER_DISTANCE = 4

# Цвета вместо текстур (чтобы не грузить файлы)
colors = {
    'grass': color.lime.tint(-0.2),
    'dirt': color.brown,
    'stone': color.gray,
    'sand': color.yellow,
    'water': color.azure.tint(-0.4),
    'wood': color.orange,
    'leaves': color.green,
    'lava': color.red,
    'gold': color.gold,
    'snow': color.white
}
block_list = list(colors.keys())
current_idx = 0

player = FirstPersonController()
player.speed = 8
player.jump_height = 3
player.cursor.visible = False
ghost_mode = False

sky = Sky()
sun = DirectionalLight(shadows=False)
sun.look_at(Vec3(1,-1,1))

zombies = []

# === ВОКСЕЛЬ ===
class Block(Button):
    def __init__(self, pos, type='grass'):
        super().__init__(
            parent=scene,
            position=pos,
            model='cube',
            origin_y=0.5,
            color=colors.get(type, color.white),
            highlight_color=color.lime
        )
        self.type = type

# === Простая генерация мира ===
def generate_chunk(cx, cz):
    for x in range(CHUNK_SIZE):
        for z in range(CHUNK_SIZE):
            wx = cx * CHUNK_SIZE + x
            wz = cz * CHUNK_SIZE + z
            height = int((sin(wx*0.07) + cos(wz*0.07)) * 4 + 6)

            for y in range(height-4, height):
                if y < height-4: t = 'stone'
                elif y < height-1: t = 'dirt'
                else: t = 'grass' if height > 3 else 'sand'
                Block(Vec3(wx, y, wz), t)

chunks = {}
def load_chunks():
    cx = int(player.x // CHUNK_SIZE)
    cz = int(player.z // CHUNK_SIZE)
    for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE+1):
        for dz in range(-RENDER_DISTANCE, RENDER_DISTANCE+1):
            key = (cx+dx, cz+dz)
            if key not in chunks:
                generate_chunk(cx+dx, cz+dz)
                chunks[key] = True

# === БОЖЕСТВЕННЫЕ СИЛЫ ===
def lightning():    Entity(model='cube', color=color.yellow, scale=(0.3,40,0.3), position=player.position+player.forward*30+Vec3(0,20,0), lifetime=0.3)
def meteor():       Entity(model='sphere', color=color.orange, scale=5, position=(player.x+randint(-40,40),60,player.z+randint(-40,40))).animate_position_y(-10, duration=3)
def tornado():      [Entity(model='cube', color=color.gray, scale=0.6, position=player.position+Vec3(randint(-10,10),randint(0,20),randint(-10,10))) for _ in range(20)]
def flood():        [Block(player.position+Vec3(randint(-15,15),0,randint(-15,15)), 'water') for _ in range(80)]
def volcano():      [Block((player.x+cos(radians(a))*r, randint(15,30), player.z+sin(radians(a))*r), 'lava') for r in range(5,20) for a in range(0,360,30)]
def nuclear_winter(): [Entity(model='sphere', color=color.white, scale=0.15, position=(player.x+randint(-60,60),50,player.z+randint(-60,60)), velocity=Vec3(0,-10,0)) for _ in range(600)]
def zombies():      [zombies.append(Entity(model='cube', color=color.dark_gray, scale=1.8, position=player.position+Vec3(randint(-30,30),5,randint(-30,30)), collider='box')) for _ in range(15)]
def gold_rain():    [Entity(model='cube', color=colors['gold'], scale=1, position=(player.x+randint(-40,40),45,player.z+randint(-40,40)), velocity=Vec3(0,-12,0)) for _ in range(100)]
def levitate():     [setattr(e, 'y', e.y+3) for e in scene.entities if isinstance(e, Block) and distance(e, player) < 25]
def fire_rain():    [Entity(model='sphere', color=color.orange, scale=1.2, position=(player.x+randint(-35,35),50,player.z+randint(-35,35)), velocity=Vec3(0,-15,0)) for _ in range(60)]
def apocalypse():   [f() for f in [meteor, volcano, nuclear_winter, zombies, fire_rain]]

# === УПРАВЛЕНИЕ ===
def input(key):
    global current_idx, ghost_mode
    if key == 'escape': quit()
    if key == 'scroll up':   current_idx = (current_idx + 1) % len(block_list)
    if key == 'scroll down': current_idx = (current_idx - 1) % len(block_list)
    if key == 'g':
        ghost_mode = not ghost_mode
        player.collider = None if ghost_mode else 'box'
        player.speed = 25 if ghost_mode else 8

    # СИЛЫ
    {'l': lightning, 'm': meteor, 't': tornado, 'f': flood, 'v': volcano,
     'n': nuclear_winter, 'z': zombies, 'h': gold_rain, 'i': levitate,
     'j': fire_rain, 'x': apocalypse}.get(key, lambda:None)()

    # Строительство
    if held_keys['left mouse'] and mouse.hovered_entity:
        Block(mouse.hovered_entity.position + mouse.normal, block_list[current_idx])
    if held_keys['right mouse'] and mouse.hovered_entity:
        destroy(mouse.hovered_entity)

# UI
Text('L-молния │ M-метеорит │ T-торнадо │ F-наводнение │ V-вулкан │ N-зима │ Z-зомби │ H-огонь │ J-золото │ I-левитация │ X-АПОКАЛИПСИС │ G-полёт', 
     origin=(0,0), y=.45, scale=1.6, color=color.cyan)

Text(lambda: f'Блок: {block_list[current_idx].upper()}  │  Режим: {"ПОЛЁТ" if ghost_mode else "ХОДЬБА"}', x=-0.87, y=0.4, scale=1.8)

def update():
    load_chunks()
    # зомби преследуют
    for z in zombies[:]:
        dir = (player.position - z.position).normalized()
        z.position += dir * 0.07
        if distance(z, player) > 100: destroy(z); zombies.remove(z)

load_chunks()
app.run()
