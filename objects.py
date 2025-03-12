# -*- coding: utf-8 -*-

import pygame
import groups
import control
import random
import math
import os

SCREEN_RECT = pygame.Rect(0, 0, 640, 480)
score = control.Score((50,16))
lvl = control.Level((450,16))
hScore = control.HighScore((270,16))

# Game Entities

class Ship(pygame.sprite.Sprite):
    def __init__(self,position):
        #Register into Group
        self._layer = 2
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.ships)

        imgfile = os.path.join(control.main_dir, "sprites", "ship.png")
        self.image = pygame.image.load(imgfile).convert_alpha()

        self.rect = self.image.get_rect(center=position)
        self.xspeed = 3
        self.yspeed = 0
        self.direction = 1
        self.bToSpawn = 0

        #Important Ship Vars
        self.level = 1
        self.threshold = 1.5
        self.startTime = 0
        self.levelupthreshold = 10000
        self.flowercoords = [128,256,384,512]
    
    def rampage(self):
        self.xspeed = 7.5
        self.threshold = 6
    
    def update(self):
        # Move the Ship
        self.rect.move_ip(self.direction * self.xspeed, self.yspeed)
        if (self.rect.bottom < 0): 
            self.kill()
        if self.yspeed == 0 and (self.rect.left <= 0 or self.rect.right >= 640):
            self.direction *= -1
            self.image = pygame.transform.flip(self.image, True, False)
        
        # Drop Bombs Randomly
        bomb_gen = random.randrange(0,100,1)
        if (bomb_gen < self.threshold):
            if (self.startTime == 75 and len(groups.bombs) < 10 and len(groups.flowers) != 0):
                # Check if a bonus can spawn
                if (self.bToSpawn > 0 and len(groups.bonuses) == 0):
                    # Spawn a Bonus
                    Bonus((self.rect.centerx,self.rect.centery + 64),(self.direction / abs(self.direction)))
                    self.bToSpawn -= 1
                else:
                    # Spawn a Bomb
                    Bomb((self.rect.centerx,96))
                    if pygame.mixer and control.bombdrop_snd is not None:
                        control.bombdrop_snd.play()
        
        # Turn around Randomly if over flower
        if (100 - bomb_gen < self.threshold):
            for x in self.flowercoords:
                if (abs(x - self.rect.centerx) < 16):
                    self.direction *= -1
                    self.image = pygame.transform.flip(self.image, True, False)
                    
        
        # Give the player some grace time
        if (self.startTime < 75): self.startTime += 1

        # Level up if Score is high enough
        if (score.levelup >= self.levelupthreshold):
            score.levelup -= self.levelupthreshold
            self.levelupthreshold = control.cap(self.levelupthreshold + 2500, 25000)
            lvl.level += 1
            self.level = control.cap(self.level + 1, 15) 
            score.bonusspawn += 50

            self.xspeed = (self.level / 2) + 2.5
            self.threshold = (self.level / 2) + 1
            for wFlower in groups.wilted:
                wFlower.revive()
        
        #Check if there are any bonuses to add
        if (score.bonusspawn >= 100):
            score.bonusspawn -= 100
            self.bToSpawn += 1

class Explosion(pygame.sprite.Sprite):
    def __init__(self,position,comb):
        self._layer = 4
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.explosions)
        self.font = pygame.font.SysFont("Consolas", 12)
        self.color = (255,0,0)
        self.combo = comb
        self.expScore = 100 * len(groups.flowers) * self.combo
        score.score_to_add += self.expScore
        score.bonusspawn += self.combo
        self.scoreText = self.font.render(str(self.expScore), 1, self.color)


        # Load Spritesheet
        imgfile = os.path.join(control.main_dir, "sprites", "explosion.png")
        self.sheet = pygame.image.load(imgfile).convert_alpha()

        self.width = 64
        self.height = 64

        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect(center=position)
        self.textRect = self.scoreText.get_rect(center=self.image.get_rect().center)
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))

        if pygame.mixer and control.explode_snd is not None:
            control.explode_snd.play()

        self.timer = 20
        self.sheetPos = 0

    def update(self):
        self.timer -= 1
        if (self.timer == 0):
            self.kill()
        if (self.timer % 2 == 1):
            if (self.timer < 10):
                self.sheetPos -= self.width
            else:
                self.sheetPos += self.width
        if (self.sheetPos < 0 or self.sheetPos > self.width * 6):
            self.kill()
        self.sheet.set_clip(pygame.Rect(self.sheetPos, 0, self.width, self.height))
        self.image.fill((0,0,0,0))
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()), (0,0))
        if (self.expScore != 0): self.image.blit(self.scoreText, self.textRect)

class Bomb(pygame.sprite.Sprite):
    def __init__(self,position):
        self._layer = 1
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.bombs)

        # Load Spritesheet
        imgfile = os.path.join(control.main_dir, "sprites", "bomb.png")
        self.sheet = pygame.image.load(imgfile).convert_alpha()

        #state of sprite; 0 is normal, 1 is "dragged" aka touched an explosion
        self.state = 0
        self.combo = 0

        self.width = 32
        self.height = 32

        self.xspeed = 0
        self.yspeed = 2
        self.timer = 30

        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))
        self.image = self.sheet.subsurface(self.sheet.get_clip())
        self.rect = self.image.get_rect(center=position)
        self.x = self.rect.centerx
        self.y = self.rect.centery + 12
        self.dir = 0

    def explode(self):
        self.kill()
        if pygame.mixer and control.bombdrag_snd is not None:
            if (control.drag.get_busy()):
                control.drag.stop()
        Explosion((self.x,self.y),self.combo)

    def startDrag(self,expX,expY,tim):
        if pygame.mixer and control.bombdrag_snd is not None:
            control.drag.play(control.bombdrag_snd)
        
        while (tim > 0):
            tim -= 1

        self.yspeed = 0
        self.state = 1

        # Set direction
        xdist = self.x - expX
        ydist = self.y - expY
        hyp = math.pow(math.pow(xdist,2)+math.pow(ydist,2),(1/2))
        if (hyp == 0):
            # Prevents Divide by Zero Error
            self.explode()
        else:
            self.xspeed = (4 * (xdist / hyp))
            self.yspeed = (4 * (ydist / hyp))

    def update(self):
        self.y = self.rect.centery + 12

        if (self.state == 1): 
            self.x = self.rect.centerx
            self.timer -= 1
            if (self.timer == 0):
                self.explode()
            self.sheet.set_clip(pygame.Rect(self.width * (self.timer % 2), 0, self.width, self.height))
            self.image = self.sheet.subsurface(self.sheet.get_clip())

        self.rect.move_ip(self.xspeed,self.yspeed)
        if self.rect.bottom >= 416:
            self.explode()

class Bonus(pygame.sprite.Sprite):
    def __init__(self,position,spd):
        self._layer = 1
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.bonuses)

        # Load Spritesheet
        self.font = pygame.font.SysFont("Consolas", 12)
        self.color = (255,0,0)
        self.scoreText = self.font.render("", 1, self.color)

        # Load Spritesheet
        imgfile = os.path.join(control.main_dir, "sprites", "bonus.png")
        self.sheet = pygame.image.load(imgfile).convert_alpha()

        self.width = 64
        self.height = 32

        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect(center=position)
        self.textRect = self.scoreText.get_rect(center=self.image.get_rect().center)
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))

        self.speed = 7 * spd
        self.frame = 0
        self.timer = 600
        self.combo = 0

        if pygame.mixer and control.bonus_snd is not None:
            control.bonus_snd.play()

    def explode(self):
        if pygame.mixer and control.oof_snd is not None:
            control.oof_snd.play()
        self.speed = 0
        self.expScore = 1000 * len(groups.flowers) * self.combo
        score.score_to_add += self.expScore
        self.scoreText = self.font.render(str(self.expScore), 1, self.color)
        self.textRect = self.scoreText.get_rect(center=self.image.get_rect().center)
        self.timer = -20

    def update(self):
        self.image.fill((0,0,0,0))
        if (self.timer == 0):
            self.kill()
        elif (self.timer < 0):
            self.frame = 7
            self.timer += 1
        else:
            self.frame = (self.frame + 1) % 7
            self.timer -= 1
            if (self.timer == 0):
                if pygame.mixer and control.bonusmiss_snd is not None:
                    control.bonusmiss_snd.play()

        self.rect.move_ip(self.speed,0)
        if (self.rect.left <= 0 or self.rect.right >= 640):
            self.speed *= -1
        
        self.sheet.set_clip(pygame.Rect(0, 32*self.frame, self.width, self.height))
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))
        self.image.blit(self.scoreText, self.textRect)


class Wilted(pygame.sprite.Sprite):
    def __init__(self,position):
        #Register into Group
        self._layer = 1
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.wilted)

        # Load Spritesheet
        imgfile = os.path.join(control.main_dir, "sprites", "flower.png")
        self.sheet = pygame.image.load(imgfile).convert_alpha()

        self.width = 32
        self.height = 64
        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))
        
        self.image = self.sheet.subsurface(self.sheet.get_clip())
        self.rect = self.image.get_rect(center=position)
        if pygame.mixer and control.oof_snd is not None:
            control.oof_snd.play()
        
        # State of flower; 0 is wilted, 1 is "Dead"
        self.state = (len(groups.flowers) <= math.floor(lvl.level / 10))

        # Used for animation
        self.animation_timer = 0
        self.flip = 0
    
    def revive(self):
        if (self.state == 0):
            newFlower = Flower((self.rect.centerx,self.rect.centery))
            newFlower.animation_timer = 60
            self.kill()

    def update(self):
        if (self.animation_timer < 7): 
            self.flip = 1 - self.flip
            if (self.flip == 0): self.animation_timer += 1
            self.sheet.set_clip(pygame.Rect(self.width * self.animation_timer, self.height * (self.state == 1 and self.animation_timer != 0), self.width, self.height))
            self.image = self.sheet.subsurface(self.sheet.get_clip())

class Flower(pygame.sprite.Sprite):
    def __init__(self,position):
        #Register into Group
        self._layer = 1
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.flowers)

        # Load Spritesheet
        imgfile = os.path.join(control.main_dir, "sprites", "flower.png")
        self.sheet = pygame.image.load(imgfile).convert_alpha()

        self.width = 32
        self.height = 64
        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))

        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        
        self.rect = self.image.get_rect(center=position)
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))

        # Used when flower revives
        self.animation_timer = 0

    def wilt(self):
        self.kill()
        Wilted((self.rect.centerx,self.rect.centery))
    
    def update(self):
        if (self.animation_timer > 0): 
            self.image.set_alpha(128)
            self.animation_timer -= 1
        if (self.animation_timer == 0): self.image.set_alpha(256)
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))

class Shell(pygame.sprite.Sprite):

    def __init__(self, position):
        self._layer = 2
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.shells)

        imgfile = os.path.join(control.main_dir, "sprites", "shell.png")
        self.image = pygame.image.load(imgfile).convert_alpha()
        self.rect = self.image.get_rect(center=position)
        self.speed = 4

    def update(self):
        self.rect.move_ip(0,-1 * self.speed)
        if self.rect.y <= -12:
            self.kill()

class Character(pygame.sprite.Sprite):
    def __init__(self, position):

        #init sprite
        self._layer = 5
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.players)

        #load image
        self.width = 64
        self.height = 64

        imgfile = os.path.join(control.main_dir, "sprites", "cannon.png")
        self.sheet = pygame.image.load(imgfile).convert_alpha()
        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))

        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect(midtop=position)

        self.speed = 5
        
        self.reloading = 0
        self.stuntimer = 0
        self.health = 100

    def move(self, direction):
        if ((direction == 'left')):
            self.rect.move_ip(-1 * self.speed, 0)
        if ((direction == 'right')):
            self.rect.move_ip(self.speed, 0)
        self.rect = self.rect.clamp(SCREEN_RECT)

        
    def update(self):
        if (self.stuntimer > 0): 
            self.image.set_alpha(128)
            self.stuntimer -= 1
            self.health -= 1
            if (self.health == 0):
                Explosion((self.rect.centerx,self.rect.centery),0)
                for ship in groups.ships:
                    ship.rampage()
                self.kill()
        else: 
            self.image.set_alpha(256)
            self.health = control.cap(self.health + 1,100)
        if (self.stuntimer == 1):
            self.speed = 5
            self.reloading = 0
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))
        

    def handle_event(self, event):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.move('left')
        if keys[pygame.K_RIGHT]:
            self.move('right')
        quit = keys[pygame.K_q]
        if quit:
            Explosion((self.rect.centerx,self.rect.centery),0)
            if pygame.mixer and control.oof_snd is not None:
                control.oof_snd.play()
            for ship in groups.ships:
                ship.rampage()
            self.kill()
        
        firing = keys[pygame.K_SPACE]
        if not self.reloading and firing and self.speed > 0 and len(groups.shells) < 3:
            Shell((self.rect.centerx,self.rect.y))
            if pygame.mixer and control.shell_snd is not None:
                control.shell_snd.play()
            
        self.reloading = firing

class GameOver(pygame.sprite.Sprite):
    def __init__(self, position):
        #init sprite
        self._layer = 3
        pygame.sprite.Sprite.__init__(self, groups.layers)

        imgfile = os.path.join(control.main_dir, "sprites", "gameover.png")
        self.sheet = pygame.image.load(imgfile).convert_alpha()

        self.width = 304
        self.height = 176

        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect(center=position)
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))

        self.load = 0
    
    def update(self):
        self.image.fill((0,0,0,0))
        if (self.load):
            self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))

class Letter(pygame.sprite.Sprite):
    def __init__(self,position,id):
        self._layer = 3
        pygame.sprite.Sprite.__init__(self, groups.layers)

        imgfile = os.path.join(control.main_dir, "sprites", "text.png")
        self.sheet = pygame.image.load(imgfile).convert_alpha()

        self.width = 64
        self.height = 64
        self.sheet.set_clip(pygame.Rect(0, 0, self.width, self.height))
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect(topleft=position)
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))

        self.id = id # The ID of the block: 0 is the 1st, 1 is the 2nd, 2 is the 3rd
        self.letterid = 0 # The Letter to display and send: A is 0, B is 1,...
        self.hID = 0
        self.vID = 0
        self.enabled = False # Used if enabled
        self.isLit = False
        self.flashtimer = 30
        self.uphold = -1
        self.downhold = -1
    
    def update(self):
        self.image.fill((0,0,0,0))
        if (self.id == control.scoreid):
            if (not self.enabled):
                self.flashtimer = 30
                self.isLit = True
                self.uphold = -1
                self.downhold = -1
            self.enabled = True
        else:
            if (self.enabled):
                self.isLit = False
            self.enabled = False

        
        if (self.enabled):
            self.flashtimer -= 1
            if (self.flashtimer == 0):
                self.isLit = not self.isLit
                self.flashtimer = 30
            
            key = pygame.key.get_pressed()
            if key[pygame.K_UP]:
                self.flashtimer = 30
                self.isLit = True
                if (self.uphold <= 0):
                    self.uphold = 15 + (-15 * self.uphold)
                    self.letterid = (self.letterid - 1) % 26
            else: self.uphold = -1
            if key[pygame.K_DOWN]:
                self.flashtimer = 30
                self.isLit = True
                if (self.downhold <= 0):
                    self.downhold = 15 + (-15 * self.downhold)
                    self.letterid = (self.letterid + 1) % 26
            else: self.downhold = -1
        
        self.hID = 64 * (self.letterid % 9)
        self.vID = 64 * (math.floor(self.letterid / 9) + 3 * self.isLit)
        self.sheet.set_clip(pygame.Rect(self.hID, self.vID, self.width, self.height))
        self.image.blit(self.sheet.subsurface(self.sheet.get_clip()),(0,0))

class nameEntry(pygame.sprite.Sprite):
    def __init__(self,position,place):
        self._layer = 3
        pygame.sprite.Sprite.__init__(self, groups.layers, groups.scoreboards)

        imgfile = os.path.join(control.main_dir, "sprites", "congrats.png")
        self.image = pygame.image.load(imgfile).convert_alpha()
        self.rect = self.image.get_rect(center=position)

        self.box0 = Letter((224,208),0)
        self.box1 = Letter((288,208),1)
        self.box2 = Letter((352,208),2)
        self.lockedl = False
        self.lockedr = False
        self.place = place

    def retScore(self):
        name = chr(self.box0.letterid + 65) + chr(self.box1.letterid + 65) + chr(self.box2.letterid + 65)
        hScore.newName(self.place,name)
        self.box0.kill()
        self.box1.kill()
        self.box2.kill()
        self.kill()

    def update(self):
        keys = pygame.key.get_pressed()
        keys[pygame.K_LEFT]

        left = keys[pygame.K_LEFT]
        if not self.lockedl and left and not control.scoreid == 0:
            control.scoreid -= 1
        self.lockedl = left
        right = keys[pygame.K_RIGHT]
        if not self.lockedr and right and not control.scoreid == 2:
            control.scoreid += 1
        self.lockedr = right

class Scoreboard(pygame.sprite.Sprite):
    def __init__(self):
        self._layer = 5
        pygame.sprite.Sprite.__init__(self, groups.layers)

        self.font = pygame.font.SysFont("Consolas", 12)
        self.color = (255,0,0)
        self.text = self.font.render("00st: ", 1, self.color)

        self.image = pygame.Surface((144, 160), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect(topleft = (16,224))

        self.update()

    def update(self):
        i = 0
        while (i < 10):
            if (i == 9):
                self.text = "10th"
            else:
                self.text = " " + str(i+1)
                if (i == 0): self.text += "st"
                elif (i == 1): self.text += "nd"
                elif (i == 2): self.text += "rd"
                else: self.text += "th"
            self.text += ": " + str(hScore.highscores[i])
            self.textRect = self.font.render(self.text,0,self.color)
            self.nameRect = self.font.render(str(hScore.names[i]),1,self.color)
            self.image.blit(self.textRect, (0,16*i))
            self.image.blit(self.nameRect, (100,16*i))
            i += 1