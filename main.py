import pygame
import objects
import control
import groups
import os

clock = pygame.time.Clock()

FPS = 60

#important consts
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
SCREEN_RECT = pygame.Rect(0, 0, 640, 480)

player_width = 64
player_height = 64

#important game vars
timer = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cannon-Bomb")
imgfile = os.path.join(control.main_dir, "sprites", "bomb.png")
imgsheet = pygame.image.load(imgfile).convert_alpha()
imgsheet.set_clip(pygame.Rect(0, 0, 32, 32))
dispimage = imgsheet.subsurface(imgsheet.get_clip())
pygame.display.set_icon(dispimage)
	
#load images

ground_image = pygame.image.load(control.os.path.join(control.main_dir, "sprites", "ground.png")).convert_alpha()
bg_image = pygame.image.load(control.os.path.join(control.main_dir, "sprites", "background.png")).convert_alpha()
healthSheet = pygame.image.load(control.os.path.join(control.main_dir, "sprites", "bonus.png")).convert_alpha()
healthSheet.set_clip(pygame.Rect(30, 10, 1, 16))
healthImage = healthSheet.subsurface(healthSheet.get_clip())

bg_width = bg_image.get_width()
ground_width = ground_image.get_width()	
ground_height = ground_image.get_height()	

#draw background images 
def draw_bg():
	screen.blit(bg_image,(0,0))

#draw background
def draw_ground():
	x = 0
	y = SCREEN_WIDTH / ground_width
	while (x < y):
		screen.blit(ground_image, ((x * ground_width),SCREEN_HEIGHT-ground_height))
		x += 1

#draw healthbar for cannon
def draw_health(player):
	i = 0
	while (i < player.health):
		screen.blit(healthImage, ((200 + (i / 2)), 16))
		i += 1	

run = True
game_playing = False
logo_playing = True
new_score = False
start = control.StartScreen((320,208))
starttext = control.StartText((320,320))
gOver = objects.GameOver((320,192))
sBoard = objects.Scoreboard()
newscoreroom = None
entered = False
teveglogo = None

while run:
	clock.tick(FPS)
	screen.fill((0,0,0))
	if (logo_playing == False):
		draw_bg()
		draw_ground()
	elif (teveglogo == None):
		teveglogo = control.DispLogo((320,240))
	elif (teveglogo.ready == 1):
		logo_playing = False
		for inst in groups.letters:
			inst.kill()
		teveglogo.kill()
		teveglogo = None

	for event in pygame.event.get():
		if(event.type == pygame.QUIT):
			run = False

	for instance in groups.layers:
			screen.blit(instance.image,(instance.rect.x,instance.rect.y))
			# try:
			instance.update()
			#except:
			#	print("Can't Update instance " + str(instance))
	
	if (game_playing):

		if (len(groups.players) > 0):
			player.handle_event(event)
			draw_health(player)

		# Collisions
		for shell in pygame.sprite.spritecollide(enemy_ship, groups.shells, 0):
			shell.kill()
		for bomb in pygame.sprite.groupcollide(groups.bombs, groups.shells, 0, 1):
			bomb.combo = 1
			bomb.explode()
		for bonus in pygame.sprite.groupcollide(groups.bonuses, groups.shells, 0, 1):
			if (bonus.timer > 0):
				bonus.combo = 1
				bonus.explode()
		#Bombs and Explosions
		bomExpColl = pygame.sprite.groupcollide(groups.bombs, groups.explosions, 0, 0)
		for bomb in bomExpColl:
			for explosion in bomExpColl[bomb]:
				if (bomb.state == 0): 
					bomb.combo = explosion.combo * 2
					if (bomb.combo > 16): bomb.combo = 16
					bomb.startDrag(explosion.rect.centerx,explosion.rect.centery,explosion.timer)
		#Bonuses and Explosions
		bonExpColl = pygame.sprite.groupcollide(groups.bonuses, groups.explosions, 0, 0)
		for bonus in bonExpColl:
			for explosion in bonExpColl[bonus]:
				if (bonus.timer > 0):
					bonus.combo = explosion.combo * 2
					if (bonus.combo > 16): bonus.combo = 16
					bonus.explode()

		doubleBomb = pygame.sprite.groupcollide(groups.bombs, groups.bombs, 0, 0)
		for bomb in doubleBomb:
			test_group = pygame.sprite.Group([b for b in groups.bombs if b != bomb])
			if pygame.sprite.spritecollide(bomb, test_group, 0):
				if (bomb.state > 0): bomb.explode()

		bomFloColl = pygame.sprite.groupcollide(groups.bombs, groups.flowers, 0, 0)
		for bomb in bomFloColl:
			for flower in bomFloColl[bomb]:
				bomb.explode()
		for flower in pygame.sprite.groupcollide(groups.flowers, groups.explosions, 0, 0):
			if (flower.animation_timer == 0): flower.wilt()
		for bomb in pygame.sprite.groupcollide(groups.bombs, groups.players, 0, 0):
			bomb.explode()
		if pygame.sprite.spritecollide(player,groups.explosions,0):
			if (player.stuntimer) == 0:
				if pygame.mixer and control.oof_snd is not None:
					control.oof_snd.play()
				player.speed = 0
				player.reloading = 1
				player.stuntimer = 60

		if (len(groups.flowers) == 0):
			# Prepare to End Game
			enemy_ship.yspeed = -2.5
			objects.score.score_to_add = 0
			player.speed = 0
			pygame.mixer.music.fadeout(1000)
			for bomb in groups.bombs:
				bomb.explode()
			for bonus in groups.bonuses:
				bonus.kill()

		if (len(groups.ships) == 0):
			if (gOver.load == 0):
				control.reload(gOver)
			timer -= 1
			if (timer <= 0):
				game_playing = False
				player.kill()
				for flower in groups.wilted:
					flower.kill()
				for bonus in groups.bonuses:
					bonus.kill()
				control.reload(gOver)

				#Reset Score and Update High-Score
				if (objects.score.score > objects.hScore.highscores[9]):
					sPlace = objects.hScore.lowerscore(objects.score.score)
					newscoreroom = objects.nameEntry((320,112),sPlace)
					pygame.mixer.music.load(control.hs_bgm)
					pygame.mixer.music.play(-1)
					pygame.mixer.music.set_volume(0.4)
					if pygame.mixer and control.bombdrag_snd is not None:
						control.bombdrag_snd.play()
				else:
					objects.score.score = -100
					objects.score.levelup = -100
					objects.score.score_to_add = 100
					timer = 600
					control.reload(start)
					control.reload(starttext)
				sBoard = objects.Scoreboard()
				objects.score.bonusspawn = 0
				objects.lvl.level = 1
			elif (timer == 20):
				trans = control.Transition((0,0),(SCREEN_WIDTH,SCREEN_HEIGHT),20)

	elif (newscoreroom != None):
		startkey = pygame.key.get_pressed()
		if (startkey[pygame.K_RETURN] and not entered):
			newscoreroom.retScore()
			pygame.mixer.music.stop()
			objects.score.score = -100
			objects.score.levelup = -100
			objects.score.score_to_add = 100
			timer = 600
			control.reload(start)
			control.reload(starttext)
			pygame.mixer.music.fadeout(1000)
			newscoreroom = None
		entered = startkey[pygame.K_RETURN]
	elif (logo_playing):
		pass
	else:
		startkey = pygame.key.get_pressed()
		if (startkey[pygame.K_RETURN] and not entered):
			game_playing = True
			# Create Game sprites
			player = objects.Character((320, 353))
			enemy_ship = objects.Ship((96,64))
			timer = 180
			for x in range(1,5):
				objects.Flower((128*x,384))
			
			# Start Music
			pygame.mixer.music.load(control.game_bgm)
			pygame.mixer.music.play(-1)
			pygame.mixer.music.set_volume(0.4)

			# Get rid of the start sprites
			control.reload(start)
			control.reload(starttext)
			sBoard.kill()
			sBoard = None
		entered = startkey[pygame.K_RETURN]
	
	# groups.layers.update()
	objects.groups.layers.draw(screen)

	pygame.display.update()

pygame.quit()