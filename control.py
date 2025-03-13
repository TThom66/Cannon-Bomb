import pygame
import groups
import os
import sys
import shelve
import wave
import pathlib
import numpy as np

# The main directory where the necessary game files are stored
main_dir = os.path.split(os.path.abspath(__file__))[0]

# Used to get the folder of the saved game data
def get_savedir() -> pathlib.Path:

    home = pathlib.Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming"
    elif sys.platform == "linux":
        return home / ".local/share"
    elif sys.platform == "darwin":
        return home / "Library/Application Support"

score_dir = get_savedir() / "Cannon-Bomb"
try:
    score_dir.mkdir(parents=True)
except FileExistsError:
    pass

scoreid = 0

if pygame.mixer and not pygame.mixer.get_init():
    print("Warning, no sound")
    pygame.mixer = None
else:
    pygame.mixer.set_num_channels(8)

# Store Sound

VOLUME = 0.15

bombdrop_snd = pygame.mixer.Sound(os.path.join(main_dir, "sounds", "bombdrop.wav"))
bombdrop_snd.set_volume(VOLUME)
shell_snd = pygame.mixer.Sound(os.path.join(main_dir, "sounds", "shot.mp3"))
shell_snd.set_volume(VOLUME)
explode_snd = pygame.mixer.Sound(os.path.join(main_dir, "sounds", "explode.wav"))
explode_snd.set_volume(VOLUME)
bombdrag_snd = pygame.mixer.Sound(os.path.join(main_dir, "sounds", "dragbomb.mp3"))
bombdrag_snd.set_volume(VOLUME)
bonus_snd = pygame.mixer.Sound(os.path.join(main_dir, "sounds", "bonusspawn.wav"))
bonus_snd.set_volume(VOLUME)
bonusmiss_snd = pygame.mixer.Sound(os.path.join(main_dir, "sounds", "bonusmiss.wav"))
bonusmiss_snd.set_volume(VOLUME)
oof_snd = pygame.mixer.Sound(os.path.join(main_dir, "sounds", "ugh.mp3"))
oof_snd.set_volume(VOLUME)
intro_snd = pygame.mixer.Sound(os.path.join(main_dir, "sounds", "intro.mp3"))


game_bgm = os.path.join(main_dir, "sounds", "gameaudio.wav")
hs_bgm = os.path.join(main_dir, "sounds", "highscore.wav")

drag = pygame.mixer.Channel(5)


def cap(a,b):
    if (a > b):
        return b
    return a

def reload(obj):
    if (obj.load == 1):
        obj.load = 0
    else: obj.load = 1

class LogoLetter(pygame.sprite.Sprite):
    def __init__(self,position,img):
        self._layer = 11
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.letters)

        self.image = pygame.image.load(os.path.join(main_dir, "sprites", img)).convert_alpha()
        self.rect = self.image.get_rect(midbottom=position)
        if (img == "logoe.png"):
            self.speed = 0
            self.rect = self.image.get_rect(center=position)
        else:
            self.speed = 24
            self.rect = self.image.get_rect(midbottom=position)

        self.width = self.image.get_width()
        self.height = self.image.get_height()	

        self.timer = 12

    def update(self):
        if (self.timer > 0):
            self.rect.move_ip(0,self.speed)
            self.timer -= 1


class LogoFireball(pygame.sprite.Sprite):
    def __init__(self,position):
        self._layer = 12
        pygame.sprite.Sprite.__init__(self, groups.layers)
        self.image = pygame.image.load(os.path.join(main_dir, "sprites", "logofireball.png")).convert_alpha()
        self.rect = self.image.get_rect(center=position)

        self.timer = 0
        self.speed = 0
        self.spawned = 0
        self.logoe = "logoe.png"
    
    def update(self):
        self.rect.move_ip(self.speed,0)
        if (self.timer == 194 or self.timer == 168):
            self.spawned += 1
            LogoLetter((self.rect.centerx + (4 * self.spawned - 6),self.rect.centery),self.logoe)
        elif (self.timer == 20):
            Transition((0,0),(640,480),20)
        if (self.rect.left > 640):
            self.speed = 0
        
        self.timer -= 1

class DispLogo(pygame.sprite.Sprite):
    def __init__(self,position):
        self._layer = 10
        pygame.sprite.Sprite.__init__(self, groups.layers)
        self.sheet = pygame.image.load(os.path.join(main_dir, "sprites", "background.png")).convert_alpha()
        self.width = 640
        self.height = 480
        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((0,0,0))
        self.rect = self.image.get_rect(center=position)

        self.font = pygame.font.SysFont("Consolas", 24)
        self.color = (255,255,0)
        self.text = self.font.render("PRESENTS", 1, self.color)
        self.textRect = self.text.get_rect(center=(320,384))


        self.logot = "logot.png"
        self.logov = "logov.png"
        self.logog = "logog.png"
        self.fire = LogoFireball((-40,288))

        self.timer = 0
        self.index = 0
        self.speed = 0
        self.ready = 0
    
    def update(self):
        if (self.timer == 0):
            if (self.index < 3):
                self.timer = 24
                if (self.index == 0):
                    LogoLetter((128,0),self.logot)
                    intro_snd.play()
                elif (self.index == 1):
                    LogoLetter((320,0),self.logov)
                else:
                    LogoLetter((512,0),self.logog)
            else:
                self.timer = 240
                if (self.index > 3):
                    self.ready = 1
                else:
                    self.fire.speed = 6
                    self.fire.timer = 240
            self.index += 1
        else:
            self.timer -= 1
            if (self.fire.rect.x > 640):
                self.image.blit(self.text, self.textRect)


class Score(pygame.sprite.Sprite):
    def __init__(self, position):
        self._layer = 5
        pygame.sprite.Sprite.__init__(self, groups.layers)

        self.score = -100
        self.bonusspawn = 0
        self.levelup = -100
        self.score_to_add = 100
        self.font = pygame.font.SysFont("Consolas", 12)
        self.color = (255,0,0)
        self.update()
        self.rect = self.image.get_rect().move(position)

    def update(self):
        if self.score_to_add > 0:
                self.score += 100
                self.levelup += 100
                self.score_to_add -= 100
                msg = "Score: " + str(self.score)
                self.image = self.font.render(msg, 0, self.color)

class HighScore(pygame.sprite.Sprite):
    def __init__(self, position):
        self._layer = 5
        pygame.sprite.Sprite.__init__(self, groups.layers)

        self.d = shelve.open(os.path.join(score_dir, "score"))
        self.highscores = [200000,180000,170000,160000,150000,140000,130000,120000,110000,100000]
        self.topscore = 200000
        # self.names = ["   ","   ","   ","   ","   ","   ","   ","   ","   ","   "]
        self.names = ["TVG","TVG","TVG","TVG","TVG","TVG","TVG","TVG","TVG","TVG"]
        try:
            self.highscores = self.d['scores']
            self.topscore = self.d['score']
            self.names = self.d['name']
        except:
            print("ERR: FILE NOT FOUND")
        self.d.close()
        self.topscore = self.highscores[0]

        self.font = pygame.font.SysFont("Consolas", 12)
        self.color = (255,0,0)
        self.update()
        self.rect = self.image.get_rect().move(position)
    
    def newHScore(self, score):
        self.topscore = score
        self.d = shelve.open(os.path.join(score_dir, "score"))
        self.d['score'] = self.topscore
        self.d.close()

    def newName(self, place, nName):
        self.names[place] = nName
        self.d = shelve.open(os.path.join(score_dir, "score"))
        self.d['scores'] = self.highscores
        self.d['name'] = self.names
        self.d.close()

    def lowerscore(self, nScore):
        start = 9
        while (start > 0 and nScore > self.highscores[start - 1]):
            start -= 1
            self.highscores[start + 1] = self.highscores[start]
            self.names[start + 1] = self.names[start]
        if (start == 0):
            self.newHScore(nScore)
        self.highscores[start] = nScore
        self.names[start] = "   "
        return start

    def update(self):
        msg = "Hi-Score: " + str(self.topscore)
        self.image = self.font.render(msg, 0, self.color)

class Level(pygame.sprite.Sprite):
    def __init__(self, position):
        self._layer = 5
        pygame.sprite.Sprite.__init__(self, groups.layers)

        self.level = 1
        self.last_level = 0
        self.font = pygame.font.SysFont("Consolas", 12)
        self.color = (255,0,0)
        self.load = 0
        self.image = self.font.render("Level: 1", 0, self.color)
        self.update()
        self.rect = self.image.get_rect().move(position)

    def update(self):
        if self.last_level != self.level:
                self.last_level = self.level
                msg = "Level: " + str(self.level)
                self.image = self.font.render(msg, 0, self.color)

class StartScreen(pygame.sprite.Sprite):
    def __init__(self, position):
        self._layer = 5
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.scoreboards)

        self.sheet = pygame.image.load(os.path.join(main_dir, "sprites", "title.png")).convert_alpha()

        self.width = 464
        self.height = 176

        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect(center=position)
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))

        self.load = 1
    
    def update(self):
        self.image.fill((0,0,0,0))
        if (self.load):
            self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))


class StartText(pygame.sprite.Sprite):
    def __init__(self, position):
        self._layer = 5
        pygame.sprite.Sprite.__init__(self, groups.layers)

        self.font = pygame.font.SysFont("Consolas", 20)
        self.color = (255,0,0)
        self.text = self.font.render("PRESS ENTER TO PLAY", 1, self.color)

        self.image = pygame.Surface((256, 32), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect(center=position)
        self.textRect = self.text.get_rect(center=self.image.get_rect().center)

        self.load = 1
        self.update()

    def update(self):
        if (self.load == 1):
            self.image.blit(self.text, self.textRect)
        else:
            self.image.fill((0,0,0,0))

class Transition(pygame.sprite.Sprite):
    def __init__(self, position, size, dur):
        self._layer = 15
        pygame.sprite.Sprite.__init__(self, groups.layers)

        self.image = pygame.Surface(size, pygame.SRCALPHA)
        self.alpha = 0
        self.duration = dur
        self.stop = -1 * dur

        self.image.fill((0,0,0,self.alpha))
        self.rect = self.image.get_rect(topleft=position)

    def update(self):
        if (self.duration > self.stop):
            self.alpha = 255 * (1 - (abs(self.duration) / abs(self.stop)))
            self.image.fill((0,0,0,self.alpha))
            self.duration -= 1
        else:
            self.kill()