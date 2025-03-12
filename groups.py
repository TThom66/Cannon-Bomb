import pygame

if pygame.get_sdl_version()[0] == 2:
    pygame.mixer.pre_init(44100, 32, 2, 1024)
pygame.init()

players = pygame.sprite.Group()
ships = pygame.sprite.Group()
shells = pygame.sprite.Group()
flowers = pygame.sprite.Group()
wilted = pygame.sprite.Group()
bombs = pygame.sprite.Group()
bonuses = pygame.sprite.Group()
explosions = pygame.sprite.Group()
scoreboards = pygame.sprite.Group()
letters = pygame.sprite.Group()
layers = pygame.sprite.LayeredUpdates()

