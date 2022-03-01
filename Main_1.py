import random

import pygame
from pygame import mixer
import os
import csv

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.6)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Стрелялка')

clock = pygame.time.Clock()
FPS = 60

M_left = False
M_right = False
GRAVITY = 0.75
rows = 16
cols = 150
s_tile = SCREEN_HEIGHT // rows
tile_types = 21
level = 1
screen_scroll = 0
background_scroll = 0
scroll_pos = 400
amount_lvl = 1
font = pygame.font.SysFont('comicsans', 26)
background = (144, 201, 120)
RED = (255, 0, 0)
start_game = False


health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
item_boxes = {
	'Health'	: health_box_img,
	'Ammo'		: ammo_box_img,
}

pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()
win_bg = pygame.image.load('img/win_screen.jpg').convert_alpha()
death_bg = pygame.image.load('img/death_screen.jpg').convert_alpha()
"""
jump_sound = pygame.mixer.Sound('audio/jump.wav')
jump_sound.set_volume(0.08)
shot_sound = pygame.mixer.Sound('audio/shot.wav')
shot_sound.set_volume(0.08)
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)
"""

img_list = []
for x in range(tile_types):
	img = pygame.image.load(f'img/Tile/{x}.png')
	img = pygame.transform.scale(img, (s_tile, s_tile))
	img_list.append(img)

def draw_BG():
    screen.fill(background)
    width = sky_img.get_width()
    for x in range(5):
        screen.blit(sky_img, ((x * width) - background_scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - background_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - background_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - background_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

def reset_level():
	enemy_group.empty()
	bullet_group.empty()
	box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	data = []
	for row in range(rows):
		r = [-1] * cols
		data.append(r)

	return data

def dead_draw():
    screen.blit(death_bg, (0, 0))
    text1 = font.render('Нажмите "Z" для рестарта', True,
                      (255, 255, 255))
    screen.blit(text1, (300, SCREEN_HEIGHT // 2))
    text2 = font.render('Нажмите "Esc" для выхода', True,
                        (255, 255, 255))
    screen.blit(text2, (300, SCREEN_HEIGHT // 2.5))

class Entity(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, health):
        pygame.sprite.Sprite.__init__(self)
        self.char_type = char_type
        self.direction = 1
        self.flip = False
        self.speed = speed
        self.jump = False
        self.jump_count = 0
        self.in_air = False
        self.shoot_cooldown = 0
        self.health = health
        self.max_health = health
        self.ammo = 25
        self.shoot_flag = False
        self.animation_list = []
        self.anim_count = 0
        self.alive = True
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
                # reset temporary list of images
            temp_list = []
                # count number of files in the folder
            num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = x
        self.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.idling = False #Бездействует
        self.vision = pygame.Rect(0, 0, 200, 25)
        self.move_counter = 0
        self.idling_counter = 0

    def AI(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)
                self.idling = True
                self.idling_counter = 50
            if self.vision.colliderect(player.rect):
                self.update_action(0)
                self.shoot()
            else:
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)
                    self.move_counter += 1
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > 40:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
        self.rect.x += screen_scroll

    def move(self, M_left, M_right):
        screen_scroll = 0
        coord_x = 0
        coord_y = 0
        if M_left:
            coord_x -= self.speed
            self.direction = -1
            self.flip = True
        if M_right:
            coord_x = self.speed
            self.direction = 1
            self.flip = False
        if self.jump == True and self.in_air == False:
            self.jump_count = -15
            self.jump = False
            self.in_air = True

        self.jump_count += GRAVITY
        if self.jump_count > 10:
            self.jump_count = self.jump_count
        coord_y += self.jump_count
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect.x + coord_x, self.rect.y, self.width, self.height):
                coord_x = 0
            if tile[1].colliderect(self.rect.x, self.rect.y + coord_y, self.width, self.height):
                if self.jump_count < 0:
                    self.jump_count = 0
                    coord_y = tile[1].bottom - self.rect.top
                elif self.jump_count >= 0:
                    self.jump_count = 0
                    self.in_air = False
                    coord_y = tile[1].top - self.rect.bottom

        if self.char_type == 'player':
            if self.rect.left + coord_x < 0 or self.rect.right + coord_x > SCREEN_WIDTH:
                coord_x = 0

        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        self.rect.x += coord_x
        self.rect.y += coord_y

        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - scroll_pos and background_scroll < (
                    world.level_length * s_tile) - SCREEN_WIDTH) \
                    or (self.rect.left < scroll_pos and background_scroll > abs(coord_x)):
                self.rect.x -= coord_x
                screen_scroll = -coord_x

        return screen_scroll, level_complete

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.6 * self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            bullet_group.add(bullet)
            self.ammo -= 1
            #shot_sound.play()

    def update(self):
        self.check_alive()
        self.update_animation()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def check_alive(self):
        if self.health <= 0:
            self.alive = False
            self.health = 0
            self.speed = 0
            self.update_action(3)

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

class Health_Ammo_Bar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health
        self.img = pygame.image.load('img/icons/bullet.png').convert_alpha()
        scale = 3
        self.img_ammo = pygame.transform.scale(self.img, (int(self.img.get_width() * scale), int(self.img.get_height() * scale)))

    def draw(self):
        ratio = player.health / player.max_health
        pygame.draw.rect(screen, (0, 0, 0), (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, (255,0,0), (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, (0,255,0), (self.x, self.y, 150 * ratio, 20))


    def counter(self):
        screen.blit(self.img_ammo, (170, 6))
        ammo_counter = font.render(f'X {player.ammo}', False, (0, 0, 0))
        pos_counter = ammo_counter.get_rect(center=(240, 20))
        screen.blit(ammo_counter, pos_counter)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.bullet_speed = 10
        self.direction = direction
        self.radius = 15
        img = pygame.image.load('img/icons/bullet.png').convert_alpha()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.rect.x += (self.direction * self.bullet_speed)  + screen_scroll
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemy in enemy_group:
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()

class Box(pygame.sprite.Sprite):
    def __init__(self, x, y, box_type):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.box_type = box_type
        self.image = item_boxes[self.box_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + 40 // 2, y + (40 - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll
        if pygame.sprite.collide_rect(self, player):
            if self.box_type == 'Ammo':
                if player.alive:
                    player.ammo += 10
            elif self.box_type == 'Health':
                if player.alive:
                    player.health += 25
                    if player.health > player.max_health:
                        player.health = player.max_health
            self.kill()

class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * s_tile
                    img_rect.y = y * s_tile
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        Water = water(img, x * s_tile, y * s_tile)
                        water_group.add(Water)
                    elif tile >= 11 and tile <= 14:
                        decoration = bg_Fill(img, x * s_tile, y * s_tile)
                        decoration_group.add(decoration)
                    elif tile == 15:  # create player
                        player = Entity('player', 300, 300, 2, 5, 100)
                        health_bar = Health_Ammo_Bar(10, 10, 100, 100)
                    elif tile == 16:  # create enemies
                        enemy = Entity('enemy', x * s_tile, y * s_tile, 2, 2, 100)
                        enemy_group.add(enemy)
                    elif tile == 17:  # create ammo box
                        item_box = Box(x * s_tile, y * s_tile, 'Ammo')
                        box_group.add(item_box)
                    elif tile == 19:  # create health box
                        item_box = Box(x * s_tile, y * s_tile, 'Health')
                        box_group.add(item_box)
                    elif tile == 20:  # create exit
                        Exit = exit(img, x * s_tile, y * s_tile)
                        exit_group.add(Exit)

        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])

class water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + s_tile // 2, y + (s_tile - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class bg_Fill(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + s_tile // 2, y + (s_tile - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + s_tile // 2, y + (s_tile - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


bullet_group = pygame.sprite.Group()
box_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

world_data = []
for row in range(rows):
    r = [-1] * cols
    world_data.append(r)

with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)


world = World()
player, health_bar = world.process_data(world_data)

run = True
while run:
    clock.tick(FPS)
    draw_BG()
    world.draw()
    player.update()
    player.draw()
    for enemy in enemy_group:
        enemy.AI()
        enemy.update()
        enemy.draw()
    bullet_group.update()
    bullet_group.draw(screen)
    box_group.update()
    box_group.draw(screen)
    decoration_group.update()
    decoration_group.draw(screen)
    water_group.update()
    water_group.draw(screen)
    exit_group.update()
    exit_group.draw(screen)
    if player.alive:
        health_bar.draw()
        health_bar.counter()
        if player.shoot_flag:
            player.shoot()
        if player.in_air:
            player.update_action(2)
        elif M_left or M_right:
            player.update_action(1)
        else:
            player.update_action(0)
        screen_scroll, level_complete = player.move(M_left, M_right)
        background_scroll -= screen_scroll
        if level_complete:
            level += 1
            background_scroll = 0

            if level <= amount_lvl:
                world_data = reset_level()
                with open(f'level{level}_data.csv', newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=',')
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)
                world = World()
                player, health_bar = world.process_data(world_data)
            else:
                screen_scroll = 0
                screen.blit(win_bg, (0, 0))
                text1 = font.render('Вы победили!!, чтобы перезапустить игру, рестартните окно', True,
                                    (255, 255, 255))
                screen.blit(text1, (300, SCREEN_HEIGHT // 2))
                text2 = font.render('Нажмите "Esc" для выхода', True,
                                    (255, 255, 255))
                screen.blit(text2, (300, SCREEN_HEIGHT // 2.5))
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            run = False
    else:
        screen_scroll = 0
        dead_draw()
        if player.health == 0:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        run = False
                    elif event.key == pygame.K_z:
                        bg_scroll = 0
                        world_data = reset_level()
                        # load in level data and create world
                        with open(f'level{level}_data.csv', newline='') as csvfile:
                            reader = csv.reader(csvfile, delimiter=',')
                            for x, row in enumerate(reader):
                                for y, tile in enumerate(row):
                                    world_data[x][y] = int(tile)
                        world = World()
                        player, health_bar = world.process_data(world_data)
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            Stand = False
            if event.key == pygame.K_a:
                M_left = True
                M_right = False
            elif event.key == pygame.K_d:
                M_right = True
                M_left = False
            elif event.key == pygame.K_w:
                player.jump = True
                #jump_sound.play()
            elif event.key == pygame.K_RSHIFT:
                player.shoot_flag = True
            elif event.key == pygame.K_ESCAPE:
                run = False
            elif event.key == pygame.K_l:
                player.health = 0
            elif event.key == pygame.K_n:
                player.ammo += 10
            elif event.key == pygame.K_m:
                player.health += 15
        if event.type == pygame.KEYUP:
            Stand = True
            if event.key == pygame.K_a:
                M_left = False
            elif event.key == pygame.K_d:
                M_right = False
            elif event.key == pygame.K_RSHIFT:
                player.shoot_flag = False
    pygame.display.update()

pygame.quit()
