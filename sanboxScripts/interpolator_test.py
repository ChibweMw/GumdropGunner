import pygame

from interpolator import *

RESOLUTION = (800, 600)  # (adjust for your resolution)
SECONDS    = 1.0         # slow enough to see how it goes, but not too slow...

class Sprite( pygame.sprite.Sprite ):

  def __init__( self, color, pos ):
    pygame.sprite.Sprite.__init__( self )
    self.image = pygame.Surface( (30, 30) )
    self.image.fill( color )

    self.rect = self.image.get_rect()
    self.rect.center = pos

    self.line = Interpolator( pos )

  def update( self, screen ):
    screen.fill( (0, 0, 0), self.rect )
    self.line.next()
    self.rect.center = self.line.pos
    screen.blit( self.image, self.rect )

def main():
  pygame.init()
  screen = pygame.display.set_mode( RESOLUTION )

  x, y = RESOLUTION
  x //= 2
  y //= 2

  shapes   = [1.0, 2.0, 2.0, 4.0, 0.5]
  middles  = [0.5, 0.5, 1.0, 0.0, 0.5]
  xoffsets = [0, -30, 30, -30, 30]
  yoffsets = [0, -30, -30, 30, 30]
  colors   = [
    ( 52,  98, 166),
    (244, 127,  48),
    (176,  84, 175),
    (229,  35,  58),
    (255, 255, 162)
    ]

  all = pygame.sprite.OrderedUpdates()
  for xoffset, yoffset, color in zip( xoffsets, yoffsets, colors ):
    all.add( Sprite( color, (x +xoffset, y +yoffset) ) )

  clock = pygame.time.Clock()

  all.update( screen )
  pygame.display.update()

  while True:
    for event in pygame.event.get():
      if event.type in [pygame.QUIT, pygame.KEYDOWN]:
        return
      elif event.type == pygame.MOUSEBUTTONDOWN:
        fps = clock.get_fps()
        x, y = event.pos
        for    sprite,   shape,  middle,  xoffset,  yoffset in zip(
          all.sprites(), shapes, middles, xoffsets, yoffsets
          ):
          sprite.line = Interpolator(
                          sprite.rect.center,
                          (x +xoffset, y +yoffset),
                          SECONDS,
                          fps,
                          shape,
                          middle
                          )

    all.update( screen )
    pygame.display.update()
    clock.tick( 60 )

main()