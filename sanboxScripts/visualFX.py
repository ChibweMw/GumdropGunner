#!/usr/bin/env python

import os
import sys
import time
import pygame
from pygame import surfarray
from pygame.locals import *

main_dir = os.path.split(os.path.abspath(__file__))[0]


def transition():
	diamonds = [ ... ] # List of arrays containing 1 and 2 arranged in enlarging diamond patterns, say 100x100
	for diamond in diamonds: # you probably want timers and events rather than a tight loop
		for x in [0,100,200, ...]:
			for y in [0,100,200, ...]:
				screen[x:x+100, y:y+100] = diamond.choose(screen1[x:x+100,y:y+100], screen2[x:x+100,y:y+100])
		# Pause for transition effect
		time.sleep(0.01)

	pygame.quit()

def surfdemo_show(array_img, name):
	"displays a surface, waits for user to continue"
	screen = pygame.display.set_mode(array_img.shape[:2], 0, 32)
	surfarray.blit_array(screen, array_img)
	pygame.display.flip()
	pygame.display.set_caption(name)
	while 1:
		e = pygame.event.wait()
		if e.type == KEYDOWN and e.key == K_SPACE: break
		elif e.type == KEYDOWN and e.key == K_s:
			pygame.image.save(screen, name+'.png')
		elif e.type == QUIT:
			raise SystemExit()

def main(arraytype=None):
	"""show various surfarray effects

	If arraytype is provided then use that array package. Valid
	values are 'numeric' or 'numpy'. Otherwise default to NumPy,
	or fall back on Numeric if NumPy is not installed.

	"""
	if arraytype not in ('numpy', None):
 		raise ValueError('Array type not supported: %r' % arraytype)

	import numpy as N
	from numpy import int32, uint8, uint

	pygame.init()
	print ('Using %s' % surfarray.get_arraytype().capitalize())
	print ('Press the mouse button to advance image.')
	print ('Press the "s" key to save the current image.')



	#striped
	#the element type is required for N.zeros in  NumPy else
	#an array of float is returned.
	striped = N.zeros((180*2, 320*2, 3), int32)
	striped[:] = (0, 0, 0)
	striped[:,::2] = (0, 25, 255)
	surfdemo_show(striped, 'striped')

	# Let's define two arrays to work on. They should be replaced with your surfaces
	a = N.ones((180*2, 320*2, 3))
	b = N.zeros((180*2, 320*2, 3))

	a[100:110,200:210] = b[100:110, 200:210]
	
	diamonds = [ ... ] # List of arrays containing 1 and 2 arranged in enlarging diamond patterns, say 100x100
	print("DIAMONDS>>>", diamonds)
	# for diamond in diamonds: # you probably want timers and events rather than a tight loop
	# 	for x in [0,100,200, ...]:
	# 		for y in [0,100,200, ...]:
	# 			screen[x:x+100, y:y+100] = diamond.choose(screen1[x:x+100,y:y+100], screen2[x:x+100,y:y+100])
	# 	# Pause for transition effect
	# 	time.sleep(0.01)

	# pygame.quit()

	#allblack
	allblack = N.zeros((128, 128), int32)
	surfdemo_show(allblack, 'allblack')

	#alldone
	pygame.quit()

if __name__ == '__main__':
	main()


