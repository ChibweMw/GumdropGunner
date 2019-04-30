# Pygame template for basic game project
import pygame
import random

WIDTH = 360
HEIGHT = 480
FPS = 30

# define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

#initialize pygame and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shootah")
clock = pygame.time.Clock()

all_sprites = pygame.sprite.Group()
#Game loop
running = True
while running:
	#keep loop running at right speed
	clock.tick(FPS)

	# Process input (events)
	for event in pygame.event.get():
		# check for window close
		if event.type == pygame.QUIT:
			running = False	
	
	# Update
	all_sprites.update()
	
	# Draw / render
	screen.fill(BLACK)
	all_sprites.draw(screen)

	# Always do this *after* drawing everything,
	pygame.display.flip()

pygame.quit()