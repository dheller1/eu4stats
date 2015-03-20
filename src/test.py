import pygame, sys, time
from pygame.constants import QUIT
pygame.init()

windowSurface = pygame.display.set_mode((800, 600), 0, 32)
pygame.display.set_caption('Hello World!')

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

basicFont = pygame.font.SysFont("Times New Roman", 100)

text = basicFont.render('Hello world! :D', True, WHITE)

def blit_mask(source, dest, destpos, mask, maskrect):

        """
        Blit an source image to the dest surface, at destpos, with a mask, using
        only the maskrect part of the mask.
        """
        windowSurface.fill(WHITE)
        tmp = source.copy()

        tmp.blit(mask, destpos, maskrect, special_flags=pygame.BLEND_RGBA_MULT)  # mask 1 green


        tmp.blit(red, (destpos[0]+100,0), maskrect, special_flags=pygame.BLEND_RGBA_MULT)  # mask 2 red

        dest.blit(tmp, (0,0), dest.get_rect().clip(maskrect))

        pygame.display.update()

red = pygame.Surface((200,100))
red.fill(RED)

green = pygame.Surface((100,100),0)
green.fill(GREEN)

for a in range(700):
    blit_mask(text, windowSurface , (a,0), green, (0,0,800,600))

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()