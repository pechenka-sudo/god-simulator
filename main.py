from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from random import random, randint, choice
from math import sin, cos, radians
import time

app = Ursina()
window.title = 'Симулятор Бога — Веб-версия'
window.fps_counter.enabled = True
window.exit_button.visible = False

# Настройки (упрощённые для веб)
CHUNK_SIZE = 8  # Меньше чанков для скорости
RENDER_DISTANCE = 3

# Цвета вместо текстур (для веб, без файлов)
block_colors = {
    'grass': color.lime,
    'dirt': color.brown,
    'stone': color.gray,
    'sand': color.yellow,
    'water': color.azure.tint(-0.5),
    'wood': color.orange,
    'leaves': color.green,
    'lava': color.red
}
blocks = list(block_colors.keys())
current_block = 0

player = FirstPersonController(collider='box', jump_height=2)
player.speed = 8
player.cursor.visible = False
player.ghost_mode = False

# Небо и свет
sky = Sky()
sun = DirectionalLight(shadows=False)  # Тени off для скорости
sun.look_at(Vec3(1, -1, -1))

# Животные (упрощённо)
animals = []
class Animal(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=choice([color.white, color.magenta, color.pink]),
            scale=1.5,
            position=position + Vec3(0, 1, 0),
            collider='box'
        )
        self.speed = 0.02 + random() * 0.02
        animals.append(self)

    def update(self):
        self.x += (random() - 0.5) * 0.1
        self.z += (random() - 0.5) * 0.1

# Воксели
class Voxel(Button):
    def __init__(self, position, btype='grass'):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            color=block_colors.get(btype, color.gray),
            highlight_color=color.lime
        )
        self.block_type = btype
        self.age = 0

    def update(self):
        # Падение песка/лавы (упрощённо)
        if self.block_type in ('sand', 'lava') and self.y > -20:
            below = [e for e in scene.entities if e.position == self.position + Vec3(0, -1, 0)]
            if not below:
                self.position += Vec3(0, -1, 0)

        # Рост листьев
        if self.block_type == 'wood':
            self.age += 1
            if self.age > 100 and random() < 0.01:
                Voxel(self.position + Vec3(0, 1, 0), 'leaves')

# Генерация чанков (процедурная)
def generate_chunk(cx, cz):
    for x in range(CHUNK_SIZE):
        for z in range(CHUNK_SIZE):
            wx = cx * CHUNK_SIZE + x
            wz = cz * CHUNK_SIZE + z
            # Простой шум для высоты
            h = int((sin(wx * 0.1) + cos(wz * 0.1)) * 5 + 5)

            for y in range(-3, h):
                if y < h - 3: block = 'stone'
                elif y < h - 1: block = 'dirt'
                elif y == h - 1:
                    block = 'sand' if h < 3 else 'grass'
                else: continue
                Voxel((wx, y, wz), block)

            # Деревья
            if block == 'grass' and random() < 0.05:
                for th in range(3, 5):
                    Voxel((wx, h + th, wz), 'wood')
                Voxel((wx, h + 5, wz), 'leaves')

            # Животные
            if random() < 0.02:
                Animal(Vec3(wx, h + 2, wz))

chunks = {}
def generate_chunks_around_player():
    cx = int(player.x // CHUNK_SIZE)
    cz = int(player.z // CHUNK_SIZE)
    for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
        for dz in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            key = (cx + dx, cz + dz)
            if key not in chunks:
                generate_chunk(cx + dx, cz + dz)
                chunks[key] = True

# Божественные силы (упрощённые)
def lightning_strike():
    pos = player.position + player.forward * 20 + Vec3(0, 20, 0)
    bolt = Entity(model='cube', color=color.yellow, scale=(0.2, 30, 0.2), position=pos)
    invoke(destroy, bolt, delay=0.5)

def meteor():
    m_pos = player.position + Vec3(randint(-20, 20), 40, randint(-20, 20))
    meteor = Entity(model='sphere', color=color.orange, scale=2, position=m_pos)
    meteor.animate_position(m_pos + Vec3(0, -50, 0), duration=2)
    invoke(destroy, meteor, delay=2)

def tornado():
    for _ in range(10):
        Entity(model='cube', color=color.gray, scale=0.5,
               position=player.position + Vec3(randint(-5,5), randint(0,10), randint(-5,5)),
               rotation=Vec3(randint(0,360), 0, 0))

# Управление
def input(key):
    global current_block
    if key == 'escape': quit()
    if key == 'scroll up': current_block = (current_block + 1) % len(blocks)
    if key == 'scroll down': current_block = (current_block - 1) % len(blocks)
    if key == 'g':  # Полёт
        player.ghost_mode = not player.ghost_mode
        player.collider = None if player.ghost_mode else 'box'
        player.speed = 15 if player.ghost_mode else 8

    # Силы
    if key == 'l': lightning_strike()
    if key == 'm': meteor()
    if key == 't': tornado()
    if key == 'f':  # Наводнение (добавить воду)
        for _ in range(20): Voxel(player.position + Vec3(randint(-5,5), 0, randint(-5,5)), 'water')

    # Блоки
    if held_keys['left mouse'] and mouse.hovered_entity:
        Voxel(mouse.hovered_entity.position + mouse.normal, blocks[current_block])
    if held_keys['right mouse'] and mouse.hovered_entity:
        destroy(mouse.hovered_entity)

# UI
Text("Симулятор Бога\nЛКМ: создать | ПКМ: удалить\nG: полёт | L: молния | M: метеор | T: торнадо | F: наводнение", 
     origin=(0,0), y=0.45, scale=2, color=color.yellow)

current_text = Text('', x=-0.8, y=0.4, scale=1.5)

def update():
    generate_chunks_around_player()
    current_text.text = f"Блок: {blocks[current_block].upper()}\nРежим: {'ПОЛЁТ' if player.ghost_mode else 'ЗЕМЛЯ'}"
    sun.rotation_y += 0.2
    # Анимация животных
    for a in animals[:]:
        if distance(a, player) > 50:  # Удаляем дальних
            destroy(a)
            animals.remove(a)

# Начальная генерация
generate_chunks_around_player()

app.run()
