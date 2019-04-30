# shmup game!
# Frozen Jam by tgfcoder <https://twitter.com/tgfcoder> licensed under CC-BY-3 <http://creativecommons.org/licenses/by/3.0/>
# Art from keenney.nl

import os
import time
import pygame
import random
import math
# from pygame.math import Vector2
import pytweening as tween

import bulletml
import bulletml.bulletyaml
from bulletml.collision import collides_all

from os import path

try:
	import yaml
except ImportError:
	yaml = None

try:
	import psyco
except ImportError:
	pass
else:
	psyco.full()

import glob

# Set up paths to assets/resources
img_dir = path.join(path.dirname(__file__), 'img')
snd_dir = path.join(path.dirname(__file__), 'audio')
# font_dir = path.join(path.dirname(__file__), 'fonts')

font_dir = glob.glob('fonts/*.ttf')
print("=====> lOADED FONTS", font_dir)

print("FONT DIR", font_dir)
bullet_pattern_dir = glob.glob('bullet-patterns/*.xml')
print("=====> lOADED PATTERNS", bullet_pattern_dir)

WIDTH  = 180 * 2 #320 * 2 #180
HEIGHT = 320 * 2 #180 * 2 #320
FPS = 60
POWERUP_TIME = 5000

# define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
P_BLACK = (34, 32, 52)
RED = (255, 0, 0)
P_RED = (172, 50, 50)
GREEN = (0, 255, 0)
P_GREEN = (55, 148, 110)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CLEAR = (0, 0, 0, 0)
SFX_VOL = 0.05
MUSIC_VOL = 0.15
PLAYER_SHOOT_VOL = MUSIC_VOL - 0.115

HS_FILE = "highscore.txt"

# pre init for audio buffer specification. Helps play sfx responcively, lagless
pygame.mixer.pre_init(44100,-16, 1, 512)

# initialize pygame and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode([WIDTH, HEIGHT], pygame.DOUBLEBUF)
# pygame.display.set_caption("Gumdrop Gunner! %d" % FPS)
pygame.display.set_caption("Gumdrop Gunner!")
clock = pygame.time.Clock()

print("=> PYGAME INITIALIZED")

# pygame.mouse.set_visible(False)
# FOR BACKGROUND SCROLLING <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
x = 0
y = 0

font_name = pygame.font.match_font('arial', bold=True)

def fancy_text(surf,text, size, x, y, color=WHITE):
	font = pygame.font.Font(font_dir[0], size)
	char_group = []
	char_width = 0
	char_num = 0

	# if text == "Gumdrop": print("TEXT METRICS", font.size(text))

	for char in text:
		if text == "Gumdrop": print("CHAR WIDTH", font.size(char)[0])
		char_blit = ()
		text_surface = font.render(char, True, color)
		text_rect = text_surface.get_rect()

		text_rect.midtop = (x, y) # why midtop?
		
		text_rect.x += int(char_width)
		# print("X MAX LETTER WIDTH", font.metrics(text)[0][1])
		# char_width += font.metrics(text)[char_num][1] # 35 + 4
		char_width += font.size(char)[0] # 35 + 4
		char_blit = (text_surface, text_rect)
		char_group.append(char_blit)
		char_num += 1

		# surf.blits(text_surface,text_rect)
	# print(char_group)
	surf.blits(char_group)

def draw_text(surf,text, size, x, y, color=WHITE, centered=True):
	font = pygame.font.Font(font_dir[0], size)
	text_surface = font.render(text, True, color)
	text_rect = text_surface.get_rect()
	if centered: text_rect.midtop = (x, y)
	else: text_rect.topleft = (x, y)
	surf.blit(text_surface,text_rect)


	# char_group = []
	# char_width = 0
	# char_num = 0

	# # if text == "Gumdrop": print("TEXT METRICS", font.size(text))

	# for char in text:
	# 	if text == "Gumdrop": print("CHAR WIDTH", font.size(char)[0])
	# 	char_blit = ()
	# 	text_surface = font.render(char, True, color)
	# 	text_rect = text_surface.get_rect()
	# 	text_rect.midtop = (x, y)
	# 	text_rect.x += int(char_width)
	# 	char_width += font.size(char)[0] # 35 + 4
	# 	char_blit = (text_surface, text_rect)
	# 	char_group.append(char_blit)
	# 	char_num += 1
	# surf.blits(char_group)

def newmob(mob, layer_manager, group):
	m = mob
	group.add(m)
	layer_manager.add(m)

def draw_shield_bar(surf, x, y, pct, color, bar_length):
	if pct < 0:
		pct = 0
	BAR_LENGTH = bar_length
	BAR_HEIGHT = 10
	fill = (pct / bar_length) * BAR_LENGTH
	outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
	fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
	pygame.draw.rect(surf, color, fill_rect)
	pygame.draw.rect(surf, WHITE, outline_rect, 2)

def draw_invuln_circle(surf, x, y, color, radius):
	pygame.draw.circle(surf, color, (x, y), radius * 10, 2)

def draw_radial_meter(surf, color_arc, rect, arc_start, arc_end, width_arc=6):
	pygame.draw.arc(surf, color_arc, rect, arc_start, arc_end, width_arc)

def draw_lives(surf, x, y, lives, img):
	for i in range(lives):
		img_rect = img.get_rect()
		img_rect.x = x + 30 * i
		img_rect.y = y
		surf.blit(img, img_rect)

def get_angle(origin, destination):
    """Returns angle in radians from origin to destination.
    This is the angle that you would get if the points were
    on a cartesian grid. Arguments of (0,0), (1, -1)
    return .25pi(45 deg) rather than 1.75pi(315 deg).
    """
    x_dist = destination[0] - origin[0]
    y_dist = destination[1] - origin[1]
    return math.atan2(-y_dist, x_dist) % (2 * math.pi)

def project(pos, angle, distance):
    """Returns tuple of pos projected distance at angle
    adjusted for pygame's y-axis.
    """
    return (pos[0] + (math.cos(angle) * distance),
            pos[1] - (math.sin(angle) * distance))

# t = current time/time elapsed, b = starting point/value(beginning), c = change, d = duration

class Player(pygame.sprite.Sprite):
	def __init__(self):
		self.groups = all_sprites
		self._layer = 1
		pygame.sprite.Sprite.__init__(self)
		# print(pygame.math.Vector2())
		#what we see
		self.image =  pygame.transform.scale(player_img, (64, 64))
		self.image.set_colorkey(BLACK)
		# the bounding box of the player
		self.rect = self.image.get_rect()
		self.radius = int(self.rect.width * 0.07)
		self.radius_mod = 2
		pygame.draw.circle(self.image, P_GREEN, self.rect.center, self.radius)
		# pygame.draw.circle(self.image, YELLOW, self.rect.center, self.radius * self.radius_mod, 2)
		# pygame.draw.rect(self.image, RED, self.rect, 2)
		
		self.deg_shield_start = math.radians(-90)
		self.deg_shield_end = math.radians(-90)
		self.shield_start = self.deg_shield_start
		self.shield_end = self.deg_shield_end
		# pygame.draw.ellipse(self.image, P_GREEN, self.rect, 2)
		# pygame.draw.arc(self.image, P_RED, self.rect, self.shield_start, self.shield_end, 6)


		self.rect.centerx = WIDTH / 2
		self.rect.bottom = HEIGHT - 10
		self.speedx = 2
		self.speedy = 2
		self.max_shield = 1
		self.shield = self.max_shield
		self.shoot_delay = 200
		self.last_shot = pygame.time.get_ticks()
		self.lives = 3
		self.hidden = False
		self.hide_timer = pygame.time.get_ticks()
		self.power = 1
		self.power_time = pygame.time.get_ticks()
		self.shot_angle = 180
		# self.spawn_point = pygame.mouse.set_pos(int(WIDTH / 2), int(HEIGHT + self.rect.height))
		self.can_shoot = False
		 
		self.start_speed = 10
		self.speed = self.start_speed
		self.pos = self.rect.center
		self.angle = get_angle(self.pos, pygame.mouse.get_pos())
		# self.pos = project(self.pos, self.angle, self.speed)

		self.ivn_timer = 0.001
		self.inv_curr_time = self.ivn_timer
		self.respawn_inv_timer = pygame.time.get_ticks()
		self.is_invuln = True
		self.inv_color = (55, 148, 110)

		self.orig_speed_k_control = 5
		self.speed_k_control = self.orig_speed_k_control

		self.shot_timer = pygame.time.get_ticks()

		self.ease_time = pygame.time.get_ticks()
		self.ease_started = False

		self.paused = False

	def color_cycle(self):
		self.inv_color = (random.randrange(0.0,255.0), random.randrange(0.0,255.0), random.randrange(0.0,255.0))

	def invulnerability(self, timer):
		self.inv_curr_time = timer * 1000
		now = pygame.time.get_ticks()

		if self.is_invuln and now - self.respawn_inv_timer > self.inv_curr_time:
			self.color_cycle()
			self.respawn_inv_timer = now
			self.deg_shield_end -= math.radians(1.2)
			self.deg_shield_start += math.radians(1.2)
			
			if math.degrees(self.deg_shield_end) <= math.degrees(self.shield_end) - 179:
				self.is_invuln = False 


	def update(self):
		if not self.lives: self.hide()
		if self.hidden or self.paused:
			# self.rect.center = (int(WIDTH / 2), int(HEIGHT + self.rect.height))
			pass
			# self.spawn_point = pygame.mouse.set_pos(int(WIDTH / 2), int(HEIGHT + self.rect.height))
		else:

			# self.rect.x += self.speedx
			# self.rect.y += self.speedy
			if self.rect.right > WIDTH:
				self.rect.right = WIDTH
			if self.rect.left < 0:
				self.rect.left = 0
			if self.rect.bottom > HEIGHT:
				self.rect.bottom = HEIGHT
			if self.rect.top < 0:
				self.rect.top = 0

			if self.is_invuln:
				# self.draw_invuln(self.rect.center, 20, YELLOW)

				self.invulnerability(self.ivn_timer)

			# print("It is indeed", self.is_invuln, "that I am invulnerable!")

			

			# for mouse controls
			# mouse_x, mouse_y = pygame.mouse.get_pos()
			# if mouse_x == self.rect.centerx:
			# 	# print("MOUSE X")
			# 	self.speedx = 0
			# else:
			# 	self.speedx = (mouse_x - self.rect.centerx) / self.speed
			# if mouse_y == self.rect.centery:
			# 	self.speedy = 0
			# else:
			# 	self.speedy = (mouse_y - self.rect.centery) / self.speed

			# if mouse_x != pygame.mouse.get_pos()[0] or mouse_y != pygame.mouse.get_pos()[1]:
			# 	print("mouse x and mouse y", mouse_x, mouse_y)
			# 	print("get mouse pos", pygame.mouse.get_pos())
				
			# if self.is_invuln and pygame.time.get_ticks() - self.respawn_inv_timer > timer:
			# 	self.is_invuln = False 
			if self.can_shoot and pygame.time.get_ticks() - self.shot_timer > (self.shoot_delay * 2) :
				
				self.shoot()


			# keyboard movement

			# use for simulated decelleration
			# self.rect.y += self.speedy

			self.vx, self.vy = 0, 0

			keystate = pygame.key.get_pressed()
			if  keystate[pygame.K_LEFT]:
				if self.can_shoot and pygame.time.get_ticks() - self.shot_timer > (self.shoot_delay * 1) :
					self.shot_timer = pygame.time.get_ticks()
					self.can_shoot = False
				
				self.vx = -self.speed_k_control

			if  keystate[pygame.K_RIGHT]:
				if self.can_shoot and pygame.time.get_ticks() - self.shot_timer > (self.shoot_delay * 1) :
					self.shot_timer = pygame.time.get_ticks()
					self.can_shoot = False

				self.vx = self.speed_k_control

			if keystate[pygame.K_UP]:
				if self.can_shoot and pygame.time.get_ticks() - self.shot_timer > (self.shoot_delay * 1) :
					self.shot_timer = pygame.time.get_ticks()
					self.can_shoot = False

				self.vy = -self.speed_k_control

			if  keystate[pygame.K_DOWN]:
				if self.can_shoot and pygame.time.get_ticks() - self.shot_timer > (self.shoot_delay * 1) :
					self.shot_timer = pygame.time.get_ticks()
					self.can_shoot = False
					
				self.vy = self.speed_k_control

			if self.vx != 0 and self.vy != 0:
				self.vx /= 1.414
				self.vy /= 1.414

			self.rect.centerx += self.vx
			self.rect.centery += self.vy
			

			# shooting

			if not keystate[pygame.K_DOWN] and not keystate[pygame.K_UP] and not keystate[pygame.K_RIGHT] and not keystate[pygame.K_LEFT]:
				self.can_shoot = True

			# if keystate[pygame.K_c]:
			# 	self.speed_k_control = int(self.orig_speed_k_control / 2)
			# 	self.can_shoot = True
			# else:
			# 	self.speed_k_control = self.orig_speed_k_control
			# 	self.can_shoot = False

			# powerup timeout
			if self.power >= 2 and pygame.time.get_ticks() - self.power_time > POWERUP_TIME:
				self.power -= 1
				self.power_time = pygame.time.get_ticks()
		

		# restart setup
		if self.lives and self.hidden and pygame.time.get_ticks() - self.hide_timer > 1000:
			self.shield = self.max_shield
			self.hidden = False
			self.rect.centerx = WIDTH / 2
			self.rect.bottom = HEIGHT - 10

			self.is_invuln = True
			self.inv_curr_time = 0
			self.shot_timer = pygame.time.get_ticks()

	def powerup(self):
		self.power += 1
		self.power_time = pygame.time.get_ticks()

	def shoot(self):
		now = pygame.time.get_ticks()
		if now - self.last_shot > self.shoot_delay:
			self.last_shot = now
			if self.power == 1:
				self.shot_angle = 180
				# print(self.shot_angle)
				# self.shot_angle = 0 - self.rect.x
				bullet = Bullet(self.rect.centerx, self.rect.top, -self.shot_angle)
				all_sprites.add(bullet)
				bullets.add(bullet)
				shoot_sfx.play()
			if self.power >= 2:
				# self.shot_angle = random.randrange(179, 181)
				self.shot_angle = 180
				bullet1 = Bullet(self.rect.left, self.rect.centery, self.shot_angle)
				bullet2 = Bullet(self.rect.right, self.rect.centery, self.shot_angle)
				all_sprites.add(bullet1)
				all_sprites.add(bullet2)
				bullets.add(bullet1)
				bullets.add(bullet2)
				shoot_sfx.play()

	def hide(self):
		# temporarily hide player
		self.hidden = True
		self.respawn_inv_timer = pygame.time.get_ticks()

		self.deg_shield_start = self.shield_start
		self.deg_shield_end = self.shield_end

		# self.shield = 0

		self.hide_timer = pygame.time.get_ticks()
		self.rect.center = (WIDTH / 2, HEIGHT + 200)

		# self.shot_timer = pygame.time.get_ticks()

class Mob(pygame.sprite.Sprite):
	def __init__(self):
		# initialize the sprite
		pygame.sprite.Sprite.__init__(self)
		self.image_orig = random.choice(meteor_images)
		self.image_orig.set_colorkey(BLACK)
		self.image = self.image_orig.copy()
		# bounding box
		self.rect = self.image.get_rect()
		self.radius = int((self.rect.width / 2))
		# pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
		self.rect.x = random.randrange(WIDTH - self.rect.width)
		self.rect.y = random.randrange(-100, -40)
		self.speedy = random.randrange(1, 8)
		self.speedx = random.randrange(-3, 3)
		self.rot = 0
		self.rot_speed = random.randrange(-8, 8)
		self.last_update = pygame.time.get_ticks()

	def rotate(self):
		now = pygame.time.get_ticks()
		if now - self.last_update > 50:
			self.last_update = now
			self.rot = (self.rot + self.rot_speed) % 360
			new_image = pygame.transform.rotate(self.image_orig, self.rot)
			old_center = self.rect.center
			self.image = new_image
			self.rect = self.image.get_rect()
			self.rect.center = old_center	

	# def follow(self, target):
	# 	distx = target.rect.centerx - self.rect.centerx
	# 	disty = target.rect.centery - self.rect.centery
		
	# 	dist = math.sqrt(distx * distx + disty * disty)
	# 	if dist == 0:
	# 		pass
	# 	else:
	# 		distx /= dist
	# 		disty /= dist
	# 		distx *= 10
	# 		disty *= 10
	# 	print("distance ", dist)


	# 	self.rect.centerx += distx
	# 	self.rect.centery += disty

	def update(self):
		self.rotate()
		self.rect.y += self.speedy
		self.rect.x += self.speedx
		if self.rect.top > HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WIDTH + 20:
			self.rect.x = random.randrange(WIDTH - self.rect.width)
			self.rect.y = random.randrange(-100, -40)
			self.speedy = random.randrange(1, 8)

class Mob_Ufo(pygame.sprite.Sprite):
	def __init__(self):
		# initialize the sprite
		pygame.sprite.Sprite.__init__(self)
		self.image_orig = pygame.transform.scale(mob_ufo_img, (50, 50))
		self.image_orig.set_colorkey(BLACK)
		self.image = self.image_orig.copy()
		# bounding box
		self.rect = self.image.get_rect()
		self.radius = int((self.rect.width / 2))
		# pygame.draw.circle(self.image, RED, self.rect.center, self.radius)
		# spawn position 
		self.rect.x = random.randrange(WIDTH - self.rect.width)
		# How far back up to spawn from
		self.rect.y = random.randrange(-100, -40)
		self.speedy = random.randrange(1, 2)
		self.speedy_orig = self.speedy
		self.rot = 0
		self.rot_speed = random.randrange(-8, 8)
		self.last_update = pygame.time.get_ticks()
		self.shoot_delay = random.randrange(500, 1000, 50)
		self.last_shot = pygame.time.get_ticks()
		self.shot_angle = 0
		self.can_shoot = True
		self.fixed_shot_angle = True

	def rotate(self):
		now = pygame.time.get_ticks()
		if now - self.last_update > 50:
			self.last_update = now
			self.rot = (self.rot + self.rot_speed) % 360
			new_image = pygame.transform.rotate(self.image_orig, self.rot)
			old_center = self.rect.center
			self.image = new_image
			self.rect = self.image.get_rect()
			self.rect.center = old_center

	def shoot(self):
		now = pygame.time.get_ticks()
		if now - self.last_shot > self.shoot_delay and self.can_shoot:
			self.last_shot = now
			if self.fixed_shot_angle == True:
				self.shot_angle = (180 - 35)
			for i in range(5):
				bullet1 = Mob_Bullet(self.rect.centerx, self.rect.centery, self.shot_angle)
				# bullet2 = Mob_Bullet(self.rect.centerx, self.rect.top, self.shot_angle - 180)
				all_sprites.add(bullet1)
				mob_bullets.add(bullet1)
				# all_sprites.add(bullet2)
				# mob_bullets.add(bullet2)
				# shoot_sfx.play()
				self.shot_angle += 18
			# self.can_shoot = False

	def update(self):
		# self.rotate()
		self.shoot()
		if self.can_shoot:
			self.rect.y += self.speedy
		if self.rect.top > HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WIDTH + 20:
			self.rect.x = random.randrange(WIDTH - self.rect.width)
			self.rect.y = random.randrange(-100, -40)
			self.speedy = random.randrange(1, 2)

class Mob_Boss(pygame.sprite.Sprite):
	def __init__(self, target_pos):
		self.groups = bosses, all_sprites
		self._layer = 2
		pygame.sprite.Sprite .__init__(self)
		self.image_orig = pygame.transform.scale(mob_boss_img, (78 * 2, 73 * 2))
		self.image_orig.set_colorkey(BLACK)
		self.image = self.image_orig.copy()
		self.rect = self.image_orig.get_rect()
		self.radius = int(self.rect.width * 0.7 / 2)
		self.rect.centerx = WIDTH / 2
		self.rect.centery = -self.rect.height

		self.last_update = pygame.time.get_ticks()
		self.shoot_delay = random.randrange(500, 1000, 50)
		self.last_shot = pygame.time.get_ticks()
		
		self.pos = self.rect.center
		self.target_pos = target_pos
		# self.angle = get_angle(self.pos, pygame.mouse.get_pos())
		self.angle = get_angle(self.pos, self.target_pos.center)

		self.shot_angle = self.angle
		self.can_shoot = False
		self.resting = False
		self.fixed_shot_angle = False
		# zero indexed wave count
		self.wave_count = 0
		self.round_count = 0

		self.max_shield = 30
		self.shield = self.max_shield
		self.hidden = False
		self.speedx = 1
		self.speedy = 1

		self.right_angle = 0
		self.mirror_angle = 0

		self.can_phase_switch = True
		self.phase = 0

		self.pattern_delay = 1.5
		self.pattern_repeat = False

		self.rep_count = 0
		self.intro_playing = True

		self.tween = tween.easeInOutCubic
		self.stepy_start = 0.5
		self.stepx_start = 0.5
		self.stepy = 0
		self.stepx = 0
		self.diry = 1
		self.dirx = 1
		self.bob_rangey = 30
		self.bob_speedy = 0.75
		self.bob_rangex = 120
		self.bob_speedx = 1

		self.target = bulletml.Bullet()
		self.bml_mob = pygame.image.load(path.join(img_dir, "sprite_que_bullet_1.png")).convert()
		self.bml_mob_2 = pygame.image.load(path.join(img_dir,"sprite_que_bullet-2-1.png")).convert()

		self.norm = self.bml_mob
		self.homer = self.bml_mob_2


		self.ammo_sprite = dict(norm=self.norm, homer=self.homer)
		self.file_idx = 0

		self.bullet_radius = 12.5
		self.bullet_posx = 15
		self.bullet_posy = 15

		self.filename = bullet_pattern_dir[self.file_idx % len(bullet_pattern_dir)]
		self.doc = bulletml.BulletML.FromDocument(open(self.filename, "rU"))
		# self.source = bulletml.Bullet.FromDocument(
		# 	self.doc, x=self.rect.centerx, y=HEIGHT-self.rect.centery, target=target_pos, rank=0.5)
		self.active = set()
		# print('===========> MORGANA BULLETS', self.active)

		# print("FILENAME",self.filename)


	def Fx_Hit(self):
		# TINT OVEER SPRITE
		# pixels = pygame.PixelArray(self.image)
		# pixels.replace(P_RED, WHITE)
		# pixels.close()
		sprite_flash = pygame.Surface(self.rect.size, pygame.SRCALPHA)
		pygame.transform.threshold(
			sprite_flash, 
			sprite_flash, 
			search_color=None, 
			threshold=(0, 0, 0, 0), 
			set_color=WHITE,
			search_surf=sprite_flash,
			inverse_set=True)

		# sprite_flash.fill((255, 255, 255, 255))
		# self.image.fill((255, 255, 255, 255))

		sprite_flash.blit(self.image, (0, 0)) # (0, 0) is the top right of the image

		screen.blit(sprite_flash, self.rect, special_flags=pygame.BLEND_RGBA_MULT)

	def path(self):
		# print("boss is at:", self.rect.centerx)

		# offset = self.bob_rangey * (self.tween(self.stepy / self.bob_rangey) - self.stepy_start)
		# self.rect.centery = self.pos[1] + offset * self.diry
		# self.stepy += self.bob_speedy
		# if self.stepy > self.bob_rangey:
		# 	self.stepy = 0
		# 	self.diry *= -1

		if self.rect.centery > HEIGHT:
			self.rect.centery = -self.rect.height
		else:
			if self.shield < self.max_shield * 0.50:
				self.rect.centery += 1

		offset = self.bob_rangex * (self.tween(self.stepx / self.bob_rangex) - self.stepx_start)
		self.rect.centerx = self.pos[0] + offset * self.dirx
		self.stepx += self.bob_speedx
		if self.stepx > self.bob_rangex:
			self.stepx = 0
			self.dirx *= -1

	def pattern_target_tracker(self):

		self.target.x, self.target.y = self.target_pos.center

		# invert the 'y' value because bulletml co-ords origin is at screen bottom left
		self.target.y = HEIGHT - self.target.y
		# what are px and py
		self.target.px = self.target.x
		self.target.py = self.target.y

		# print("MORGANA TARGET POS =====>", self.target.x, self.target.y)

	def pattern_renderer(self):
		# draw bulletml objects
		for obj in self.active:
			try:
				x, y = obj.x, obj.y
			except AttributeError:
				pass
			else:
				if not obj.vanished:
					x -= 1
					y -= 1
					if os.path.basename(self.filename) == '01_SwirlingSun.xml':
						obj.radius = bullet_radius

						bullet = self.ammo_sprite.get(obj.appearance, norm)
						# print("O//////>", obj.x,"," , obj.y)
						
						# bullet = Mob_Bullet(obj.x, (HEIGHT - obj.y))
						# # bullet2 = Mob_Bullet(self.rect.centerx, self.rect.top, self.shot_angle - 180)
						# all_sprites.add(bullet)
						# mob_bullets.add(bullet)

					else:
						bullet = self.ammo_sprite.get(obj.appearance, homer)
					# more of that sweet 
					# sweet inversion on the 'y' axis!
					# so the bullet may be rendered correctly
					screen.blit(bullet, [x - self.bullet_posx, (HEIGHT - self.bullet_posy) - y])

	def pattern_bullet_handler(self):
		collides = []
		# if not game_over:
		lactive = list(self.active)
		# print("LACTIVE",len(lactive),"in LACTIVE")

		# for obj in lactive:
		# 	print('>>>>>>>MOB BOSS NEW OBJ HP', obj.hp)
		# 	new = obj.step()

		# 	self.active.update(new)
		# 	# remove bullets once out of specified bounds
		# 	# these are using good o'l pygame co-ords
		# 	# account for bullet size as well, as an update
		# 	if (obj.finished
		# 		or not (0 < obj.x < WIDTH)
		# 		or not (0 < obj.y < HEIGHT)):
		# 		self.active.remove(obj)
	
	def pattern_spawner(self):
		bullet = bulletml.Bullet()
		# wave_hp = 0
		if self.shield < self.max_shield * 0.90:
			# PHASE 3
			wave_hp = 3
			self.filename = bullet_pattern_dir[self.file_idx % int(len(bullet_pattern_dir) / 2)]
			print("Phase 3", self.filename)
			self.doc = bulletml.BulletML.FromDocument(open(self.filename, "rU"))
		elif self.shield < self.max_shield * 0.99:
			# PHASE 2
			print("Phase 2")
			wave_hp = 1
			self.filename = bullet_pattern_dir[self.file_idx % int(len(bullet_pattern_dir) / 4)]
			self.doc = bulletml.BulletML.FromDocument(open(self.filename, "rU"))
		else:
			# PHASE 1
			print("Phase 1")
			wave_hp = 0
			self.filename = bullet_pattern_dir[self.file_idx % int(len(bullet_pattern_dir) / 8)]
			self.doc = bulletml.BulletML.FromDocument(open(self.filename, "rU"))

		source = bullet.FromDocument(
			self.doc, x=self.rect.centerx, y=HEIGHT-self.rect.centery, 
			target=self.target, rank=0.5, max_hp=wave_hp)
		# source.max_hp = 200
		# print(">>>>bulletml.Bullet<<<<", bullet.max_hp)
		# source.max_hp = 1
		# print("AFTER HP", source.hp)
		source.vanished = True


		self.active.add(source)
		# print("self.active", self.active)
		# for i in self.active:
		# 	i.target.max_hp = 10
		# 	print(">>>OBJs in ACTIVE<<<", i)

		self.pattern_bullet_handler()
		self.can_shoot = False

	def pattern_interrupt(self, seconds=2.5, repeat=False):
		self.shoot_delay = 1000 * seconds
		now = pygame.time.get_ticks()
		curr_round = self.round_count
		repeat = self.pattern_repeat

		if now - self.last_shot > self.shoot_delay and not self.can_shoot:
			self.last_shot = now
			self.wave_count = 0
			self.can_shoot = True
			if repeat and not self.intro_playing:
				self.round_count = curr_round
				self.pattern_repeat = False
				# times pattern repeated

				self.rep_count += 1
				# print(">>>>>>>>Repeating", self.rep_count, "reps streak")
				return 
			elif self.intro_playing:
				self.intro_playing = False
			else:
				self.file_idx += 1
				# self.round_count += 1
				# print("file_idx:", self.file_idx)
				self.pattern_repeat = False
				# print("OUT PATTERN REP BOOL:", self.pattern_repeat)
				# times pattern repeated
				self.rep_count = 0
				# print("wave cleared<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
				return

	def shoot(self):
		self.pattern_spawner()

	def hide(self):
		# temporarily hide mob boss
		self.hidden = True
		self.shield = 0
		self.hide_timer = pygame.time.get_ticks()
		self.rect.center = (WIDTH / 2, HEIGHT + 200)

	def update(self):
		# self.pattern_target_tracker()
		# self.pattern_renderer()
		# self.image.set_at((0, i), RED)

		# self.Fx_Hit()
		if self.shield:
			if self.rect.centery <= self.rect.height:
				self.rect.centery += 2

			if self.shield < self.max_shield * 0.90:
				self.path()
			if self.can_shoot == True:
				# print("//////>shooting<////")
				self.shoot()
			if not self.active and not self.can_shoot:
				# print("///>picking next action<///")
				self.pattern_interrupt(self.pattern_delay, self.pattern_repeat)

class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, angle):
		self.groups = bullets, all_sprites
		self._layer = 3
		pygame.sprite.Sprite.__init__(self)
		self.image_orig = pygame.transform.scale(bullet_img, (32, 32))
		self.image_orig.set_colorkey(BLACK)
		# image copy for ratations
		self.image = self.image_orig.copy()
		# new_image = pygame.transform.rotate(self.image_orig, 45)
		# self.image = new_image
		self.rect = self.image_orig.get_rect()
		self.radius = int((self.rect.width))
		# For testing
		# pygame.draw.rect(self.image_orig, RED, self.rect, 2)
		
		# self.rect.centerx = x
		# self.rect.bottom = y
		self.rect.center = (x, y)
		self.bullet_speed = 1.5

		# Set initial Bullet Rotation
		self.rot = angle % 360
		new_image = pygame.transform.rotate(self.image_orig, self.rot)
		# old_center = (self.rect.centerx, self.rect.bottom)
		old_center = self.rect.center
		self.image = new_image
		# updating the old rect to match the new rotation so collisions match up
		self.rect = self.image.get_rect()
		self.rect.center = old_center
		# Bullet movement where '10' is the speed
		self.frame = 0
		self.speedx = 10 * math.sin(math.radians(self.rot))
		self.speedy = 10 * math.cos(math.radians(self.rot))
		self.posx = self.rect.centerx
		self.posy = self.rect.centery
		self.target = bulletml.Bullet()



	def update(self):
		now = pygame.time.get_ticks()
		# print("BULLET TARGET STATS", self.target)

		self.frame += 1
		self.posx +=  self.speedx
		self.posy += self.speedy
		self.rect.center = (self.posx, self.posy)

		self.target.x, self.target.y = self.rect.center
		# invert the 'y' value because bulletml co-ords origin is at screen bottom left
		self.target.y = HEIGHT - self.target.y
		# what are px and py
		self.target.px = self.target.x
		self.target.py = self.target.y

		# kill bullet when offscreen
		if self.rect.bottom < 0:
			self.kill()

class Mob_Homing_Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, angle, speed):
		self.groups = mob_bullets, all_sprites
		self._layer = 5
		pygame.sprite.Sprite.__init__(self)
		self.image_orig = pygame.transform.scale(mob_bullet_images[0], (32, 32))
		self.image_orig.set_colorkey(BLACK)
		# image copy for ratations
		self.image = self.image_orig.copy()
		self.rect = self.image.get_rect()
		self.radius = int(self.rect.width * 0.5 / 2)

		self.rect.center = (x, y)
		self.bullet_speed = 1

		self.pos = self.rect.center

		self.speed = speed
		
		# Set initial Bullet Rotation
		self.rot = angle % 360
		new_image = pygame.transform.rotate(self.image_orig, self.rot)
		# old_center = (self.rect.centerx, self.rect.bottom)
		old_center = self.rect.center
		self.image = new_image
		# updating the old rect to match the new rotation so collisions match up
		self.rect = self.image.get_rect()
		self.rect.center = old_center

		self.frame_rate = 60 
		self.last_update = pygame.time.get_ticks()
		self.frame = 0

	def update(self):
		now = pygame.time.get_ticks()
		if now - self.last_update > self.frame_rate:
			self.last_update = now
			self.frame += 1
			if self.frame == 2:
				self.frame = 0

			self.image_orig = pygame.transform.scale(mob_bullet_images[self.frame], (32, 32))
			self.image_orig.set_colorkey(BLACK)
			self.radius = int(self.rect.width * 0.5 / 2)

			new_image = pygame.transform.rotate(self.image_orig, self.rot)
			# old_center = (self.rect.centerx, self.rect.bottom)
			old_center = self.rect.center
			self.image = new_image



		self.pos = project(self.pos, self.rot, self.speed)
		self.rect.center = self.pos
		# print(self.rect.center)
		if self.rect.top > HEIGHT:
			self.kill()

class Mob_Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, angle, speed=5):
		self.groups = mob_bullets, all_sprites
		self._layer = 5
		pygame.sprite.Sprite.__init__(self)
		self.image_orig = pygame.transform.scale(mob_bullet_images[3], (32, 32))
		self.image_orig.set_colorkey(BLACK)
		# image copy for ratations
		self.image = self.image_orig.copy()
		# new_image = pygame.transform.rotate(self.image_orig, 45)
		# self.image = new_image
		self.rect = self.image.get_rect()
		self.radius = int(self.rect.width * 0.5 / 2)
		# For testing
		# pygame.draw.rect(self.image_orig, RED, self.rect, 2)
		# pygame.draw.circle(self.image_orig, GREEN, self.rect.center, self.radius)

		# self.rect.centerx = x
		# self.rect.bottom = y
		self.rect.center = (x, y)
		self.bullet_speed = speed

		# Set initial Bullet Rotation
		self.rot = angle % 360
		new_image = pygame.transform.rotate(self.image_orig, self.rot)
		# old_center = (self.rect.centerx, self.rect.bottom)
		old_center = self.rect.center
		self.image = new_image
		# updating the old rect to match the new rotation so collisions match up
		self.rect = self.image.get_rect()
		self.rect.center = old_center
		# Bullet movement where '-10' is the speed
		self.speedx = -self.bullet_speed * math.sin(math.radians(self.rot))
		self.speedy = -self.bullet_speed * math.cos(math.radians(self.rot))
		self.posx = self.rect.centerx
		self.posy = self.rect.centery

		self.frame_rate = 140 
		self.last_update = pygame.time.get_ticks()
		self.frame = 3

	def update(self):
		now = pygame.time.get_ticks()
		if now - self.last_update > self.frame_rate:
			self.last_update = now
			self.frame += 1
			if self.frame == len(mob_bullet_images):
				self.frame = 3

			self.image_orig = pygame.transform.scale(mob_bullet_images[self.frame], (32, 32))
			self.image_orig.set_colorkey(BLACK)
			self.radius = int(self.rect.width * 0.5 / 2)

			new_image = pygame.transform.rotate(self.image_orig, self.rot)
			old_center = self.rect.center
			self.image = new_image

		self.posx += self.speedx
		self.posy += self.speedy
		self.rect.center = (self.posx, self.posy)
		if self.rect.top > HEIGHT:
			self.kill()

class Pow(pygame.sprite.Sprite):
	def __init__(self, center):
		pygame.sprite.Sprite.__init__(self)
		self.type = random.choice(['shield', 'gun'])
		self.image = powerup_images[self.type]
		self.image.set_colorkey(BLACK)
		self.rect = self.image.get_rect()
		self.rect.center = center
		self.speedy = 5

	def update(self):
		self.rect.y += self.speedy
		# kill bullet when offscreen
		if self.rect.top > HEIGHT:
			self.kill()

class Explosion(pygame.sprite.Sprite):
	def __init__(self, center, size):
		self.groups = all_sprites
		self._layer = 4
		# init sprite! get used to seeing this!
		pygame.sprite.Sprite.__init__(self)
		self.size = size
		self.image = explosion_anim[self.size][0]
		self.rect = self.image.get_rect()
		self.rect.center = center
		self.frame = 0
		self.last_update = pygame.time.get_ticks()
		self.frame_rate = 80

	def update(self):
		now = pygame.time.get_ticks()
		if now - self.last_update > self.frame_rate:
			self.last_update = now
			self.frame += 1
			if self.frame == len(explosion_anim[self.size]):
				self.kill()
			else:
				center = self.rect.center
				self.image = explosion_anim[self.size][self.frame]
				self.rect = self.image.get_rect()
				self.rect.center = center

class BG_Art(pygame.sprite.Sprite):
	def __init__(self, typeof, pos=HEIGHT, scroll=True):

		self.groups =  all_sprites, title_bg, bg_art, title_art

		self.typeof = typeof
		if self.typeof == 0:
			self._layer = -1 # front most clouds
		elif self.typeof == 1:
			self._layer = -2 # second layer clouds
		else:
			self._layer = -3 # Wall texture
			
		pygame.sprite.Sprite.__init__(self)
		if self.typeof == 0:
			self.image = pygame.transform.scale(background_images[0], (180 * 2, 320 * 2))
			self.dy = 5
		elif self.typeof == 1:
			self.image = pygame.transform.scale(background_images[1], (180 * 2, 320 * 2))
			self.dy = 3
		else:
			self.image = pygame.transform.scale(background_images[2], (180 * 2, 320 * 2))
			self.dy = 1
		self.image.set_colorkey(BLACK)
		self.image.convert_alpha()
		self.rect = self.image.get_rect()
		self.start_pos = pos
		self.rect.bottom = self.start_pos

		self.parent = False
		self.can_scroll = scroll

	def update(self):
		if self.can_scroll:
			self.rect.y += self.dy
		# print("STARTED SCROLLING", self.py)

			if self.rect.y > HEIGHT:
				# print("Just passed bottom")
				# self.rect.y = self.start_pos
				self.kill()

			if not self.parent:
				if self.rect.y > 0:
					self.parent = True

					if game_over:
						# print("====>TITLE ART", len(title_art))
						# def newmob(mob, layer_manager, group):
						newmob(BG_Art(self.typeof, self.rect.y), title_bg, title_art)
					else:
						# print("==>BG ART", len(bg_art))
						# print("New BG Elem")
						newmob(BG_Art(self.typeof, self.rect.y), all_sprites, bg_art)

def transition_blinds_in(width_blinds=0):
	if width_blinds:
		for x in range(0, HEIGHT + 200, 20):
			b1 = pygame.draw.line(screen, BLACK, (0, x - 200), (WIDTH, x - 1), width_blinds)
			b2 = pygame.draw.line(screen, BLACK, (0, x - 1), (WIDTH, x - 200), width_blinds)

def transition_blinds_out(new_width=0):
	if new_width:
		for x in range(0, HEIGHT + 200, 20):
			pygame.draw.line(screen, BLACK, (0, x - 200), (WIDTH, x - 1), new_width)
			pygame.draw.line(screen, BLACK, (0, x - 1), (WIDTH, x - 200), new_width)

def fade_in(alpha=255):
	if alpha < 0: alpha = 0
	if alpha > 255: alpha = 255

	overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
	overlay.fill((0, 0, 0, alpha)) # You can change the 100 depending on what transparency it is.
	screen.blit(overlay, (0, 0))

def fade_out(alpha=0):
	if alpha < 0: alpha = 0
	if alpha > 255: alpha = 255

	overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
	overlay.fill((0, 0, 0, alpha)) # You can change the 100 depending on what transparency it is.
	screen.blit(overlay, (0, 0))

def trans_overlay(size=(WIDTH, HEIGHT), alpha=128, pos=(0, 0)):
	overlay = pygame.Surface(size, pygame.SRCALPHA)
	overlay.fill((34, 32, 52, alpha)) # You can change the 100 depending on what transparency it is.
	screen.blit(overlay, pos)

def scan_lines():
	# set width and height of scanlines now both at 1px drawn every 2 lines
	for x in range(0, HEIGHT + 2, 2):
		horizontal_line = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
		horizontal_line.fill((0, 0, 0, 60)) # You can change the 100 depending on what transparency it is.
		screen.blit(horizontal_line, (0, x - 1))
	for y in range(0, WIDTH + 2, 2):
		vertical_line = pygame.Surface((1, HEIGHT), pygame.SRCALPHA)
		vertical_line.fill((0, 0, 0, 40)) # You can change the 100 depending on what transparency it is.
		screen.blit(vertical_line, (y - 1, 0))

def show_go_screen():

	# all_sprites = pygame.sprite.LayeredUpdates()
	title_sprites = pygame.sprite.LayeredUpdates()
	title_art = pygame.sprite.Group()
	# title_bg_art = pygame.sprite.Group()

	wall_texture = BG_Art(2, scroll=True)
	cloud_texture_1 = BG_Art(0, scroll=True)
	cloud_texture_2 = BG_Art(1, scroll=True)
	
	title_art.add(wall_texture)
	title_art.add(cloud_texture_1)
	title_art.add(cloud_texture_2)

	title_bg.add(wall_texture)
	title_bg.add(cloud_texture_1)
	title_bg.add(cloud_texture_2)

	if len(title_art) < 0:
		print("ADD BG LAYERS", len(title_art))

	waiting = True
	transitioning = False
	# menu_items = {  'Start': "Play", 
	# 				'About': "About",
	# 				'High Score': 'High Score', 
	# 				'Quit': "Quit"}

	orig_menu_items = [  
					"Play", 
					"About",
					"High Score", 
					"Quit"]

	menu_items = [  "Play", 
					"About",
					"High Score", 
					"Quit"]
	hs_items = [111, 3242314, 423423, 12321, 122134]
	
	curr_blinds_width = blinds_width
	blinds_width_out = 0
	fade_in_val = 255
	fade_out_val = 0

	curr_menu_item = 1
	curr_menu_screen = 0
	
	while waiting:
		clock.tick(FPS)
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					pygame.quit()
				
				if event.key == pygame.K_UP:
					curr_menu_item -= 1
					if curr_menu_item <= 0: curr_menu_item = len(menu_items)
					# print("CURMENUITEM", menu_items[curr_menu_item % len(menu_items)])
				if event.key == pygame.K_DOWN:
					curr_menu_item += 1
					if curr_menu_item > len(menu_items): curr_menu_item = 1
					# print("CURMENUITEM", menu_items[curr_menu_item % len(menu_items)])
					
					# transitioning = True
				if event.key == pygame.K_z:
					if curr_menu_item == 1:
						transitioning = True
					elif curr_menu_item == len(menu_items):
						pygame.quit()


			if event.type == pygame.QUIT:
				pygame.quit()
			if event.type == pygame.MOUSEBUTTONUP:
				waiting = False


		title_bg.update()

		screen.fill(P_BLACK)

		title_bg.draw(screen)


		# print(">>>title_art SPRITE GROUP", len(title_art))
	

		# screen.fill(P_BLACK)
		# screen.blit(background_resize, background_rect)



		# MENU ARROW
		if curr_menu_screen == 1:
			trans_overlay(alpha=200, size=(WIDTH, (18 + 26) * 2), pos=(((0, HEIGHT / 2 - HEIGHT / 2 + (HEIGHT * 0.2)))))

			trans_overlay(alpha=200, size=(WIDTH * 0.6, (18 + 30) * 3), pos=(((WIDTH * 0.2, HEIGHT / 2 + 18 ))))
			# TITLE
			draw_text(screen, "Gumdrop", 64, WIDTH / 2, HEIGHT * 0.2)
			draw_text(screen, "-Gunner-", 30, (WIDTH / 2), HEIGHT * 0.28)
			draw_text(screen, ">", 22, WIDTH / 2 - 60, HEIGHT / 2 + 18 * curr_menu_item, centered=False)

			draw_text(screen, menu_items[0], 22, WIDTH / 2 - 40, HEIGHT / 2 + 18, centered=False )
			draw_text(screen, menu_items[1], 22, WIDTH / 2 - 40, HEIGHT / 2 + 18 * 2, centered=False)
			draw_text(screen, menu_items[2], 22, WIDTH / 2 - 40, HEIGHT / 2 + 18 * 3, centered=False)
			draw_text(screen, menu_items[3], 22, WIDTH / 2 - 40, HEIGHT / 2 + 18 * 4, centered=False)
		elif curr_menu_screen == 0:
			trans_overlay(alpha=200, size=(WIDTH, (18 + 26) * 2), pos=(0, 0) )

			trans_overlay(alpha=200, size=(WIDTH, HEIGHT * 0.8), pos=(0,  HEIGHT - HEIGHT * 0.8) )

			draw_text(screen, "Highscores", 58, WIDTH / 2, 0)
			# draw_text(screen, ">", 44, 60, HEIGHT / 2 + 32 * curr_menu_item, centered=False)

			for score in range(len(hs_items)):
				draw_text(screen, "%d" % hs_items[score], 44, 40, HEIGHT / 2 + 32 * score, centered=False)




		# in transition

		if fade_in_val >= 0 and fade_in_val <= 255 and not transitioning:
			fade_in(fade_in_val)
			fade_in_val -= 7
			# print("FADE IN VAL", fade_in_val)
		if transitioning and fade_out_val >= 0 and fade_out_val <= 255:
			fade_out(fade_out_val)
			fade_out_val += 10
			# print("FADE OUT VAL", fade_out_val)

		if curr_blinds_width >= 0 and curr_blinds_width <= blinds_width and not transitioning:
			# print("CURRENT BLINDS WIDTH", curr_blinds_width)

			curr_blinds_width -= 1

		elif blinds_width_out >= 0 and blinds_width_out <= blinds_width and transitioning:
			blinds_width_out += 1
			if blinds_width_out > blinds_width:
				# print("TRANSITIONING", transitioning)
				waiting = False
				
			transition_blinds_out(blinds_width_out)
		else:
		# if blinds_width_out == blinds_width:
			pass
			# print("TRANSITIONING", transitioning)
			# time.sleep(0.5)
		transition_blinds_in(curr_blinds_width)
		# pygame.display.update()
		# clock.tick(FPS)
		scan_lines()

		pygame.display.flip()

# load all game graphics
background = pygame.image.load(path.join(img_dir,"BG_tate_wall_1.png")).convert()
background_resize = pygame.transform.scale(background, (background.get_rect().width * 2, background.get_rect().height * 2))
background_rect = background_resize.get_rect()

background_images = []
background_image_list = [ 'BG_tate_clouds_1.png', 'BG_tate_clouds_2.png', 'BG_tate_wall_1.png']

for img in background_image_list:
	background_images.append(pygame.image.load(path.join(img_dir,img)).convert())

player_img = pygame.image.load(path.join(img_dir, "sprite_momoko.png")).convert()
player_mini_img = pygame.transform.scale(player_img, (25, 19))
player_mini_img.set_colorkey(BLACK)
bullet_img = pygame.image.load(path.join(img_dir, "sprite_mo_bullet.png")).convert()
meteor_images = []
meteor_list = [ 'meteorBrown_big1.png', 'meteorBrown_big2.png', 
				'meteorBrown_big3.png', 'meteorBrown_big4.png',
				'meteorBrown_med1.png', 'meteorBrown_med3.png',
				'meteorBrown_small1.png', 'meteorBrown_small2.png',
				'meteorBrown_tiny1.png']
for img in meteor_list:
	meteor_images.append(pygame.image.load(path.join(img_dir, img)).convert())	

mob_bullet_img = pygame.image.load(path.join(img_dir, "laserRed08.png")).convert()
mob_bullet_images = []
mob_bullet_list = [ 'sprite_que_bullet_1.png', 'sprite_que_bullet_2.png', 'sprite_que_bullet_3.png', 'sprite_que_bullet-2-1.png', 'sprite_que_bullet-2-2.png', 'sprite_que_bullet-2-3.png']

for img in mob_bullet_list:
	mob_bullet_images.append(pygame.image.load(path.join(img_dir, img)).convert())

mob_ufo_img = pygame.image.load(path.join(img_dir, "Queen.png")).convert()
mob_boss_img = pygame.image.load(path.join(img_dir, "Queen.png")).convert_alpha()
# print(">>>>", mob_boss_img.get_at((0, 0)))


explosion_anim = {}
explosion_anim['lg'] = []
explosion_anim['sm'] = []
explosion_anim['player'] = []
for i in range(9):
	filename = 'regularExplosion0{}.png'.format(i)
	img = pygame.image.load(path.join(img_dir, filename)).convert()
	img.set_colorkey(BLACK)
	img_lg = pygame.transform.scale(img, (80, 80))
	explosion_anim['lg'].append(img_lg)
	img_sm = pygame.transform.scale(img, (35, 35))
	explosion_anim['sm'].append(img_sm)
	filename = 'sonicExplosion0{}.png'.format(i)
	img = pygame.image.load(path.join(img_dir, filename)).convert()
	img.set_colorkey(BLACK)
	explosion_anim['player'].append(img)

powerup_images = {}
powerup_images['shield'] = pygame.image.load(path.join(img_dir, 'shield_gold.png')).convert()
powerup_images['gun'] = pygame.image.load(path.join(img_dir, 'bolt_gold.png')).convert()

# Load all game sounds
shoot_sfx = pygame.mixer.Sound(path.join(snd_dir, 'Laser_Shoot10.wav'))
shoot_sfx.set_volume(PLAYER_SHOOT_VOL)
shield_sfx = pygame.mixer.Sound(path.join(snd_dir, 'Powerup2.wav'))
shield_sfx.set_volume(SFX_VOL)
power_sfx = pygame.mixer.Sound(path.join(snd_dir, 'Powerup1.wav'))
power_sfx.set_volume(SFX_VOL)
expl_sfx = []
expl_sfx_list = [ 'Explosion8.wav', 'Explosion9.wav', 'Explosion11.wav']
for sfx in expl_sfx_list:
	new_sfx = pygame.mixer.Sound(path.join(snd_dir,sfx))
	new_sfx.set_volume(SFX_VOL)
	expl_sfx.append(new_sfx)

player_die_sfx = pygame.mixer.Sound(path.join(snd_dir,'rumble1.ogg'))
player_die_sfx.set_volume(SFX_VOL)
player_hit_sfx = pygame.mixer.Sound(path.join(snd_dir, 'Hit_Hurt10.wav'))
player_hit_sfx.set_volume(SFX_VOL)

pygame.mixer.music.load(path.join(snd_dir, 'Challenger.ogg'))
pygame.mixer.music.set_volume(MUSIC_VOL)

# BULLETML TESTS

target = bulletml.Bullet()


file_idx = 0

interval = 0

blinds_width = 20

curr_blinds_width = blinds_width


outro_delay = pygame.time.get_ticks()

# filename = bullet_pattern_dir[file_idx % len(bullet_pattern_dir)]
# doc = bulletml.BulletML.FromDocument(open(filename, "rU"))
# source = bulletml.Bullet.FromDocument(
# 	doc, x=WIDTH/2, y=150, target=target, rank=0.5)

# active = set([source])
# source.vanished = True

# frames = 0
# total = 0
# print("FILENAME",filename)

pygame.mixer.music.play(-1)
#Game loop
game_over = True
running = True
paused = False
stat_menu = True
round_end = False

all_sprites = pygame.sprite.LayeredUpdates()
title_bg = pygame.sprite.LayeredUpdates()

bg_art = pygame.sprite.Group()
title_art = pygame.sprite.Group()

while running:
	if game_over:
		print("Game vars reset")
		pygame.time.delay(50)

		show_go_screen()
		all_sprites = pygame.sprite.LayeredUpdates()
		title_bg = pygame.sprite.LayeredUpdates()

		mobs = pygame.sprite.Group()
		bullets = pygame.sprite.Group()
		powerups = pygame.sprite.Group()
		mob_bullets = pygame.sprite.Group()
		mob_ufos = pygame.sprite.Group()
		bosses = pygame.sprite.Group()
		players = pygame.sprite.Group()

		bg_art = pygame.sprite.Group()
		title_art = pygame.sprite.Group()


		wall_texture = BG_Art(2)
		cloud_texture_1 = BG_Art(0)
		cloud_texture_2 = BG_Art(1)

		bg_art.add(wall_texture)
		bg_art.add(cloud_texture_1)
		bg_art.add(cloud_texture_2)

		all_sprites.add(wall_texture)
		all_sprites.add(cloud_texture_1)
		all_sprites.add(cloud_texture_2)

		player = Player()
		players.add(player)
		all_sprites.add(player)

		mob_boss = Mob_Boss(player.rect)
		bosses.add(mob_boss)
		all_sprites.add(mob_boss)

		score = 0
		total = 0
		curr_blinds_width = blinds_width
		blinds_width_out = 0
		outro_timer = 2500
		intro_timer = 2500
		unpause_timer = 3000
		unpause_timer_conv = unpause_timer / 1000
		unpause_count = unpause_timer_conv

		blinds_width = 20
		curr_blinds_width = blinds_width
		fade_in_val = 255
		overlay_in = 0
		curr_count_down = 0
		curr_menu_item = 1

		restart_OK = False
		round_end= False
		stat_menu = True
		endgame_delay_complete = False
		round_start = False
		in_outro = False
		paused = False
		set_unpause = False
		game_over = False



		outro_delay = pygame.time.get_ticks()
		intro_delay = pygame.time.get_ticks()
		unpause_delay = pygame.time.get_ticks()



	# print("BG ART SPRITE GROUP", len(bg_art))

	for event in pygame.event.get():
		# check for window close
		if event.type == pygame.QUIT:
			running = False
		# if event.type == pygame.KEYUP:
		# restart for debug purposes
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_r:
				game_over = True
				# game_over = True
			if event.key == pygame.K_p and round_start and not round_end:
				if paused and not set_unpause:
					# dos tuff
					unpause_count = unpause_timer_conv

					unpause_delay = pygame.time.get_ticks()
					set_unpause = True
				if not paused:
					paused = True
					player.paused = paused
				# game_over = True

				if event.key == pygame.K_UP:
					curr_menu_item -= 1
					if curr_menu_item <= 0: curr_menu_item = len(menu_items)
					# print("CURMENUITEM", menu_items[curr_menu_item % len(menu_items)])
				if event.key == pygame.K_DOWN:
					curr_menu_item += 1
					if curr_menu_item > len(menu_items): curr_menu_item = 1
					# print("CURMENUITEM", menu_items[curr_menu_item % len(menu_items)])
					
					# transitioning = True
				if event.key == pygame.K_z:
					if curr_menu_item == 1:
						transitioning = True
					elif curr_menu_item == len(menu_items):
						pygame.quit()
			if event.key == pygame.K_RETURN:
				if round_end:
					if in_outro and stat_menu:
						print(">>>>>show end menu?",stat_menu)
						stat_menu = not stat_menu
					else:
						in_outro = not in_outro
				if not round_start:
					round_start = True
			if event.key == pygame.K_1:
				curr_font += 1
				print("CURR FONT", fontlist[curr_font % len(fontlist)])
			if event.key == pygame.K_2:
				curr_font -= 1
				print("CURR FONT", fontlist[curr_font % len(fontlist)])
			# if event.key == pygame.K_3:
			# 	intro_timer += 1000
			# 	print("INTRO TIMER UP", intro_timer)
			# if event.key == pygame.K_4:
			# 	intro_timer -= 1000
			# 	print("INTRO TIMER DOWN", intro_timer)

		# mouse controls
		if event.type == pygame.MOUSEBUTTONDOWN:
			if pygame.mouse.get_pressed()[0]:
				player.deg_shield_end += 10
				print("PLAYER DEG SHIELD END", player.deg_shield_end)
				player.can_shoot = True
				player.speed = player.start_speed / 2
			if pygame.mouse.get_pressed()[2]:
				player.deg_shield_end -= 10
				print("PLAYER DEG SHIELD END", player.deg_shield_end)		
		if event.type == pygame.MOUSEBUTTONUP:
			if not pygame.mouse.get_pressed()[0]:
				player.can_shoot = False
				player.speed = player.start_speed
	


	if set_unpause:
		clock.tick(FPS)

		new_unpause_timer = pygame.time.get_ticks()

		unpause_count = unpause_timer - (new_unpause_timer - unpause_delay) / 1000
		new_time = unpause_timer - unpause_count
		curr_count_down = (unpause_timer_conv - new_time) + 1
		print("unpause_timer", curr_count_down, "SECONDS")
		if new_unpause_timer - unpause_delay > unpause_timer:
			print(">>>>>UNPAUSE DELAY WORKING")
			paused = not paused
			player.paused = paused
			set_unpause = False

	if not round_start and not paused:
		player.deg_shield_start = math.radians(-90)
		player.deg_shield_end = math.radians(-89)
		
		clock.tick(FPS)
		# Update
		transition_blinds_in(curr_blinds_width)

		all_sprites.update()

		# Draw / render
		screen.fill(P_BLACK)

		all_sprites.draw(screen)

		# s= pygame.Surface((360, 640))

		draw_text(screen, str(score), 18, WIDTH - 90, HEIGHT - 60)
		draw_shield_bar(screen, int(WIDTH / 2) - (((mob_boss.max_shield / 4) * 5) / 2), 5, (mob_boss.shield / 4) * 5, P_RED, (mob_boss.max_shield / 4) * 5)
		# def draw_shield_bar(surf, x, y, pct, color, bar_length)
		if player.is_invuln:
			draw_invuln_circle(screen, player.rect.centerx, player.rect.centery, player.inv_color, player.radius * player.radius_mod)

		draw_lives(screen, WIDTH - 90, HEIGHT - 25, player.lives, player_mini_img)

		# def draw_radial_meter(surf, color_ellipse, color_arc, rect, arc_start, arc_end, width_ellipse=2, width_arc=6):
		shield_rect = (((player.rect.centerx - player.rect.width), (player.rect.centery - player.rect.height)) , (player.rect[2] * 2, player.rect[3] * 2))
		draw_radial_meter(screen, player.inv_color, shield_rect, player.deg_shield_start, player.deg_shield_end, width_arc=int((player.rect[2] * 2) / 20))

		
		# transition_blinds_in(curr_blinds_width)
		
		if curr_blinds_width >= 0 and curr_blinds_width <= blinds_width:

			if curr_blinds_width == 19:
				time.sleep(0.5)

			curr_blinds_width -= 1
		else:
			new_game_timer = pygame.time.get_ticks()
			# print("intro_delay", new_game_timer - intro_delay)
			if new_game_timer - intro_delay > intro_timer:
				# print(">>>>>INTRO IS WORKING")
				round_start = True
		
				

	if round_start: # round_start and not paused:
		# print("PAUSE?", paused)

		mob_boss.pattern_target_tracker()

		if not paused:
			# if not round_endif not :
			lactive = list(mob_boss.active)
			# start = time.time()
			# count = len(active)
			# print(">>>len ACTIVE", len(mob_boss.active),"ACTIVE<<<")
			for obj in lactive:
				# print(">>>LACTIVE",lactive,"LACTIVE<<<")
				# print('>>>OBJ', obj)
				new = obj.step()
				total += len(new)
				mob_boss.active.update(new)
				# remove bullets once out of specified bounds
				# these are using good o'l pygame co-ords
				# account for bullet size as well, as an update
				if (obj.finished
					or not (0 < obj.x < WIDTH)
					or not (0 < obj.y < HEIGHT)):
					mob_boss.active.remove(obj)

				elif round_end:
					# print("DESTROYING LEFTOVER BULLETS")
					expl = Explosion((obj.x, HEIGHT - obj.y), 'lg')
					all_sprites.add(expl)
					mob_boss.active.remove(obj)
			# check for collisions among active 
			# entities and set 'collides' True of False
		collides = []
		col_bullet = []

		if lactive and not round_end:
			collides = collides_all(mob_boss.target, lactive)

			if bullets:
				for bullet in bullets:
					col_bullet = collides_all(bullet.target, lactive)
					for obj in col_bullet:
						if col_bullet and obj.max_hp > 0:
							print(">>>COLLIDED OBJ  HP>>>", obj.hp)
							obj.hp -= 1
							score += 10
							random.choice(expl_sfx).play()
							expl = Explosion((obj.x, HEIGHT - obj.y), 'sm')
							all_sprites.add(expl)
							bullet.kill()
							if obj.hp <= 0:
								print(">>>>DEDED>>>>")
								expl = Explosion((obj.x, HEIGHT - obj.y), 'lg')
								all_sprites.add(expl)
								mob_boss.active.remove(obj)
							# else:
							# 	# print(">>>CURRENT obj HP>>>", obj.hp)
							# 	print("BULLET COLLISION", col_bullet)
			
			if collides and player.is_invuln == False:
				# print(">>>BULLETML TAG>>>", collides)
				for obj in collides:
					print(">>>Hit Player!!>>>")	
					mob_boss.active.remove(obj)
				
				# mob_boss.active.remove(collides[1])
				
				pygame.time.delay(50)
				player_die_sfx.play()
				death_explosion = Explosion(player.rect.center, 'player')
				all_sprites.add(death_explosion)
				player.hide()
				player.lives -= 1

				for obj in lactive:
					if obj == collides:
						print(">>>>>>>>>>>>>>>>>>>>", obj)

				mob_boss.can_shoot = False
				if mob_boss.can_shoot == False:
					mob_boss.pattern_delay = 2.5
					if not mob_boss.pattern_repeat and mob_boss.rep_count < 1:
						mob_boss.pattern_repeat = True
						print("can pattern repeat")


		# check if bullet hit mob and delete both
		hits = pygame.sprite.groupcollide(mobs, bullets, True, True)
		for hit in hits:
			score += 100 - hit.radius
			random.choice(expl_sfx).play()
			expl = Explosion(hit.rect.center, 'lg')
			all_sprites.add(expl)
			# 10% powerup
			if random.random() > 0.9:
				pow = Pow(hit.rect.center)
				all_sprites.add(pow)
				powerups.add(pow)
			newmob(Mob(), all_sprites, mobs)

		# check if bullet hit Mob Boss
		# check if bullet hit Mob Boss
		# check if bullet hit Mob Boss
		# check if bullet hit Mob Boss
		hits = pygame.sprite.groupcollide(bosses, bullets, False, True, pygame.sprite.collide_circle)
		for hit in hits:
			# print("HITHITHITHITHITHITHITHITHITHIT")
			pygame.time.delay(30)

			score += 10 * player.lives
			mob_boss.shield -= 1
			# mob_boss.Fx_Hit()			
			random.choice(expl_sfx).play()
			expl = Explosion(mob_boss.rect.center, 'sm')
			all_sprites.add(expl)
			if mob_boss.shield <= 0:
				# round_end  = True
				player_die_sfx.play()
				death_explosion = Explosion(mob_boss.rect.center, 'player')
				all_sprites.add(death_explosion)
				mob_boss.hide()
			

		# check if mob hit player
		hits = pygame.sprite.spritecollide(player, mobs, True, pygame.sprite.collide_circle) 
		for hit in hits:
			player_hit_sfx.play()
			player.shield -= 1
			expl = Explosion(hit.rect.center, 'sm')
			all_sprites.add(expl)
			newmob(Mob(), all_sprites, mobs)
			if player.shield <= 0:
				player_die_sfx.play()
				death_explosion = Explosion(player.rect.center, 'player')
				all_sprites.add(death_explosion)
				player.hide()
				player.lives -= 1





		# check if mob_bullet hit player
		hits = pygame.sprite.spritecollide(player, mob_bullets, True, pygame.sprite.collide_circle) 
		for hit in hits:
			# player_hit_sfx.play()
			# player.shield -= 1
			# expl = Explosion(hit.rect.center, 'sm')
			# all_sprites.add(expl)
			pygame.time.delay(50)

			if player.is_invuln == False:
				pygame.time.delay(50)
				player_die_sfx.play()
				death_explosion = Explosion(player.rect.center, 'player')
				all_sprites.add(death_explosion)
				player.hide()
				player.lives -= 1
				mob_boss.can_shoot = False
				if mob_boss.can_shoot == False:
					mob_boss.pattern_delay = 2.5
					if not mob_boss.pattern_repeat and mob_boss.rep_count < 1:
						mob_boss.pattern_repeat = True
						print("can pattern repeat")
			else:
				print("player is invuln:", player.is_invuln)

		# check if ufo hit player
		hits = pygame.sprite.spritecollide(player, mob_ufos, True, pygame.sprite.collide_circle) 
		for hit in hits:
			# player_hit_sfx.play()
			# player.shield -= 1
			# expl = Explosion(hit.rect.center, 'sm')
			# all_sprites.add(expl)
			# newmob(Mob_Ufo(), mob_ufos)
			if player.is_invuln == False:
				player_die_sfx.play()
				death_explosion = Explosion(player.rect.center, 'player')
				all_sprites.add(death_explosion)
				player.hide()
				player.lives -= 1

		# check to see if player hit powerup
		hits = pygame.sprite.spritecollide(player, powerups, True)
		for hit in hits:
			if hit.type == 'shield':
				player.shield += random.randrange(10, 30)
				shield_sfx.play()
				if player.shield >= 100:
					player.shield = 100
			if hit.type == 'gun':
				player.powerup()
				power_sfx.play()


		# if mob_boss.shield == 0 or player.lives == 0 and not death_explosion.alive():
		# 	game_over = True

		#keep loop running at right speed
		# dt = clock.tick(FPS) / 1000
		clock.tick(FPS)
		# Update
		if not paused: all_sprites.update()

		# Draw / render
		screen.fill(P_BLACK)

		all_sprites.draw(screen)

		# s= pygame.Surface((360, 640))
		# check if bullet hit Mob Boss
		for bullet in bullets:
			boss_hits_fx = pygame.sprite.collide_circle(mob_boss, bullet)
			if boss_hits_fx: mob_boss.Fx_Hit() 
			
		# for hit in boss_hits_fx:
		# 	mob_boss.Fx_Hit()

		draw_text(screen, str(score), 18, WIDTH - 90, HEIGHT - 60)
		draw_shield_bar(screen, int(WIDTH / 2) - (((mob_boss.max_shield / 4) * 5) / 2), 5, (mob_boss.shield / 4) * 5, P_RED, (mob_boss.max_shield / 4) * 5)
		# def draw_shield_bar(surf, x, y, pct, color, bar_length)
		if player.is_invuln:
			draw_invuln_circle(screen, player.rect.centerx, player.rect.centery, player.inv_color, player.radius * player.radius_mod)

		draw_lives(screen, WIDTH - 90, HEIGHT - 25, player.lives, player_mini_img)

		# def draw_radial_meter(surf, color_ellipse, color_arc, rect, arc_start, arc_end, width_ellipse=2, width_arc=6):
		shield_rect = (((player.rect.centerx - player.rect.width), (player.rect.centery - player.rect.height)) , (player.rect[2] * 2, player.rect[3] * 2))
		draw_radial_meter(screen, player.inv_color, shield_rect, player.deg_shield_start, player.deg_shield_end, width_arc=int((player.rect[2] * 2) / 20))
		# draw bulletml objects
		# print("PLAYER RECT", shield_rect)


		for obj in mob_boss.active:
			# print("=========>", obj)
			try:
				x, y = obj.x, obj.y
				hp = obj.hp
			except AttributeError:
				pass
			else:
				if not obj.vanished:
					x -= 1
					y -= 1
					obj.radius = mob_boss.bullet_radius

					bullet = mob_boss.ammo_sprite.get(obj.appearance, mob_boss.norm)
					# upscale bullet img
					shot = pygame.transform.scale2x(bullet)

					screen.blit(shot, [x - mob_boss.bullet_posx, (HEIGHT - mob_boss.bullet_posy) - y])
					
					# for debug, see bullet hitbox radius
					# pygame.draw.circle(screen, P_RED, ( int(round(obj.x)), int(round(HEIGHT - obj.y)) ), int(round(obj.radius)) )

		if paused:
			# trans_overlay()
			trans_overlay(size=(WIDTH, HEIGHT * 0.20), pos=(((0, HEIGHT / 2 - HEIGHT/2 + (HEIGHT * 0.40)))))
			if set_unpause:
				# pygame.draw.rect(screen, P_BLACK, ((0, HEIGHT / 2 - HEIGHT/2 + (HEIGHT * 0.40)), (WIDTH, HEIGHT - HEIGHT * 0.80)))
				draw_text(screen, "%d" % curr_count_down, int(120/curr_count_down), WIDTH / 2, HEIGHT * 0.42)
			else:
				pygame.draw.rect(screen, P_BLACK, ((0, (HEIGHT * 0.375)), (WIDTH, HEIGHT * 0.02)))
				pygame.draw.rect(screen, P_BLACK, ((0, (HEIGHT * 0.575)), (WIDTH, HEIGHT * 0.02)))
				# trans_overlay(size=(WIDTH, HEIGHT - HEIGHT * 0.80), pos=(((0, HEIGHT / 2 - HEIGHT/2 + (HEIGHT * 0.40)))))

				draw_text(screen, "Paused", 18, WIDTH / 2, (HEIGHT * 0.37))
				draw_text(screen, "Score %d" % score, 32, WIDTH / 2, (HEIGHT - HEIGHT * 0.7) + (32 * 2))
				draw_text(screen, "Lives %d" % player.lives, 32, WIDTH / 2, (HEIGHT - HEIGHT * 0.7) + (32 * 3))
				draw_text(screen, "P to unpause", 18, WIDTH / 2, (HEIGHT * 0.57))

	if restart_OK or mob_boss.shield == 0 and not death_explosion.alive() or player.lives == 0 and not death_explosion.alive():
			

		if not round_end:
			round_end = True
			outro_delay = pygame.time.get_ticks()
			print("setting round end conditions")
		
		if stat_menu:
			now = pygame.time.get_ticks()
			# print("outro_delay", now - outro_delay)
			
			if now - outro_delay > outro_timer or in_outro:
				trans_overlay()
				# FADE IN WORKS BUT NOT NECESSARY
				# offset = self.bob_rangey * (self.tween(self.stepy / self.bob_rangey) - self.stepy_start)
				# self.rect.centery = self.pos[1] + offset * self.diry
				# self.stepy += self.bob_speedy
				# if self.stepy > self.bob_rangey:
				# 	self.stepy = 0
				# 	self.diry *= -1

				in_outro = True
				pygame.draw.rect(screen, P_BLACK, ((WIDTH / 2 - WIDTH/2 + 10, HEIGHT * 0.3), (WIDTH - 20, HEIGHT * 0.25)))
				if mob_boss.shield == 0: draw_text(screen, "You Win!", 64, WIDTH / 2, HEIGHT / 4)
				else: draw_text(screen, "Game Over", 64, WIDTH / 2, HEIGHT / 4, P_RED)
				draw_text(screen, "Score %d" % score, 32, WIDTH / 2, HEIGHT / 4 + (64 + (32 * 1)))
				draw_text(screen, "Lives %d" % player.lives, 32, WIDTH / 2, HEIGHT / 4 + (64 + (32 * 2)))
				draw_text(screen, "Hit Enter to Continue" , 18, WIDTH / 2, HEIGHT / 4 + (64 + (32 * 3)))
				
				# pass
			else:
				# outro_delay = now
				if expl in(all_sprites) or lactive: 
					# print("EXPL", expl)
					pass
				
				else:
					fade_out(overlay_in)
					if overlay_in >= 0 and overlay_in <= 128:
						overlay_in += 7
						# print(">>>>FADE IN VAL", overlay_in)
					# trans_overlay()
					pygame.draw.rect(screen, P_BLACK, ((0, HEIGHT / 2 - 32 * 3), (WIDTH, 32 * 3)))
					
					if mob_boss.shield == 0: draw_text(screen, "Great Job!", 32, WIDTH / 2, HEIGHT / 4 + (64 + (32 * 1)))
					else: draw_text(screen, "Keep Trying!", 32, WIDTH / 2, HEIGHT / 4 + (64 + (32 * 1)))

				# print(now - outro_delay, "NOW - TIME DELAY COMPLETE")
			
		else:
			transition_blinds_out(blinds_width_out)
			if blinds_width_out >= 0 and blinds_width_out <= blinds_width:
				blinds_width_out += 1
			else:
			# if blinds_width_out == blinds_width:
				print("GAME OVER SEQUENCE", blinds_width_out)

				time.sleep(0.5)

				game_over = True
	else:
		# in transition
		if not round_start:
			# pygame.draw.rect(screen, P_BLACK, ((0, HEIGHT / 2 - 32 * 3), (WIDTH, 32 * 4)))
			trans_overlay(alpha=200, size=(WIDTH, (18 + 44) * 2), pos=(((0, HEIGHT / 2 - HEIGHT/2 + (HEIGHT * 0.33)))))

			draw_text(screen, "Stage 1", 18, WIDTH / 2, HEIGHT * 0.35)
			draw_text(screen, "Morgana's Hive", 44, WIDTH / 2, HEIGHT * 0.4)

		
		if curr_blinds_width >= 0 and curr_blinds_width <= blinds_width:

			transition_blinds_in(curr_blinds_width)
			if curr_blinds_width == 19:
				print("START SEQUENCE", curr_blinds_width)
				time.sleep(0.5)

			curr_blinds_width -= 1
		# else:
	# FADE IN WORKS BUT NOT NECESSARY
	# if fade_in_val >= 0 and fade_in_val <= 255:
	# 	fade_in(fade_in_val)
	# 	fade_in_val -= 7
	# 	print("FADE IN VAL", fade_in_val)


	scan_lines()


	# Always do this *after* drawing everything,
	pygame.display.flip()

pygame.quit()