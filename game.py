import sys
import random
import math
import os
import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy, Enemy_m
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark, Blood
from tkinter import *



class Game:
    def __init__(self):
        pygame.init()
        
        win= Tk()
        self.screen_width = win.winfo_screenwidth()
        self.screen_height = win.winfo_screenheight()

        self.res = (self.screen_width, self.screen_height)
        self.res_half = (int(self.screen_width / 2), int(self.screen_height / 2))
        
        #self.res = (500, 400)
        #self.res_half = (250, 200)
        
        pygame.display.set_caption("game")
        self.screen = pygame.display.set_mode(self.res)
        self.display = pygame.Surface(self.res_half, pygame.SRCALPHA)
        self.display_no_overlay = pygame.Surface(self.res_half)

        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(None, 36)  # Load font
        
        self.movement = [False, False]
        self.move = False

        self.pause_tid = 1
        
        self.assets = {
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "player": load_image("entities/player.png"),
            "background" : load_image("background.png"),
            "main_menu" : load_image("main_menu.png"),
            "clouds" : load_images("clouds"),
            "enemy/idle" : Animation(load_images("entities/enemy/idle"), img_dur=6),
            "enemy/run" : Animation(load_images("entities/enemy/run"), img_dur=12),
            "enemy/shoot" : Animation(load_images("entities/enemy/shoot"), img_dur=6),
            "enemy/idle_m" : Animation(load_images("entities/enemy_m/idle"), img_dur=6),
            "enemy/run_m" : Animation(load_images("entities/enemy_m/run"), img_dur=6),
            "player/idle" : Animation(load_images("entities/Mist walker/idle"), img_dur=8),
            "player/run" : Animation(load_images("entities/Mist walker/run"), img_dur=4),
            "player/jump" : Animation(load_images("entities/Mist walker/jump")),
            "player/fall" : Animation(load_images("entities/Mist walker/fall")),
            "player/wall_slide" : Animation(load_images("entities/Mist walker/wall_slide")),
            "particle/leaf": Animation(load_images("particles/leaf"), img_dur=20, loop=False),
            "particle/particle": Animation(load_images("particles/particle"), img_dur=6, loop=False),
            "particle/particle2": Animation(load_images("particles/particle2"), img_dur=6, loop=False),
            "projectile" : load_image("projectile.png"),
        }
        
        self.sfx = {
            "jump" : pygame.mixer.Sound("data/sfx/jump.wav"),
            "dash" : pygame.mixer.Sound("data/sfx/dash.wav"),
            "hit" : pygame.mixer.Sound("data/sfx/hit.wav"),
            "shoot" : pygame.mixer.Sound("data/sfx/shoot.wav"),
            "ambience" : pygame.mixer.Sound("data/sfx/ambience.wav"),
        }
        
        self.sfx["ambience"].set_volume(0.2)
        self.sfx["shoot"].set_volume(0.4)
        self.sfx["hit"].set_volume(0.3)
        self.sfx["dash"].set_volume(0.1)
        self.sfx["jump"].set_volume(0.2)

        self.clouds = Clouds(self.assets["clouds"], count=16)
        
        self.scaled_background = pygame.transform.scale(self.assets["background"], self.res_half)
        self.scaled_menu = pygame.transform.scale(self.assets["main_menu"], self.res)
        
        self.player = Player(self, (50, 50), (22, 37))
        
        self.tilemap = Tilemap(self, tile_size=16)

        
        
        self.level = 0
        self.load_level(self.level)
        
        self.screenshake = 0

        self.w = False

        self.s = False
        
    def load_level(self, map_id):
        self.tilemap.load("data/maps/" + str(map_id) + ".json")
        
        self.leaf_spawners = []
        for tree in self.tilemap.extract([("large_decor", 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13))
        for bush in self.tilemap.extract([("large_decor", 1)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + bush["pos"][0], 1 + bush["pos"][1], 18, 10))
            
        self.enemies = []       
        for spawner in self.tilemap.extract([("spawners", 0), ("spawners", 1), ("spawners", 2)]):
            if spawner["variant"] == 0:
                self.player.pos = spawner["pos"]
                self.player.air_time = 0
            elif spawner["variant"] == 1:
                self.enemies.append(Enemy(self, spawner["pos"], (22, 32)))
            else:
                self.enemies.append(Enemy_m(self, spawner["pos"], (12, 29)))
        
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        
    click = False

    

    def draw_text(self, text, x, y):
        text_surface = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surface, (x, y))

    def main_menu(self):
        click = False  # Move outside the loop

        self.sfx["ambience"].stop()
        pygame.mixer.music.set_volume(0.0)
        pygame.mixer.music.stop()

        while True:
            self.display.fill((0, 0, 0))  # Fill with black

            mx, my = pygame.mouse.get_pos()

            button_1 = pygame.Rect(self.screen_width * 0.388, self.screen_height * 0.91, 147, 50)
            button_2 = pygame.Rect(self.screen_width * 0.505, self.screen_height * 0.91, 147, 50)

            self.screen.blit(self.scaled_menu, (0, 0))

            #hitbox for knapper
            #pygame.draw.rect(self.screen, (255, 0, 0), button_1)
            #pygame.draw.rect(self.screen, (255, 0, 0), button_2)

            if button_1.collidepoint((mx, my)) and click:
                Game().run()  # Uncomment when you have a Game class
            if button_2.collidepoint((mx, my)) and click:
                pygame.quit()
                sys.exit()

            click = False  # Reset click after processing events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    click = True
            
            pygame.display.flip()
            self.clock.tick(60)

 

    def run(self):
        running = True
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load("data/music.wav")
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
        
            self.sfx["ambience"].play(-1)
        
        else:
            pygame.mixer.music.set_volume(0.3)
            self.sfx["ambience"].play(-1)
        
        while running:
            self.current_time = pygame.time.get_ticks()
            
            self.display.fill((0, 0, 0, 0))
            self.display_no_overlay.blit(self.scaled_background, (0, 0))
            
            self.screenshake = max(0, self.screenshake - 1)
            
            if not len(self.enemies):
                self.transition += 1
                
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir("data/maps")) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1
            
            if self.dead:
                if self.dead == 1:
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.sparks.append(Blood(self.player.rect().center, angle, 2 + random.random()))
                        self.particles.append(Particle(self, "particle2", self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)
            
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            for rect in self.leaf_spawners:
                if random.random() * 299999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, "leaf", pos, velocity=[0.1, 0.3], frame=random.randint(0, 20)))
            
            self.clouds.update()
            
            self.clouds.render(self.display_no_overlay, offset=render_scroll)
            
            self.tilemap.render(self.display, offset=render_scroll)
            for enemy in self.enemies:
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
                        
            if not self.dead:
                if not self.transition:
                    self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                    self.player.render(self.display, offset=render_scroll)
            
            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets["projectile"]
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(5):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 30:
                    if self.player.rect().collidepoint(projectile[0]):
                        if not self.dead:
                            self.projectiles.remove(projectile)
                            self.dead += 1
                            self.sfx["hit"].play()
                            self.screenshake = max(30, self.screenshake)   
            
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
                
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0 ,0 ,0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_no_overlay.blit(display_sillhouette, offset)
            
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == "leaf":
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.sfx["ambience"].stop()
                        Game().pause_menu()
                        pygame.time.wait(self.pause_tid)
                        

                    if event.key == pygame.K_a:
                        self.movement[0] = 1.7
                        self.move = True
                        if self.player.wall_slide:
                            self.player.wall_slide = False
                            self.player.velocity[0] = -2
                            self.player.jumps = 1
                            self.movement[1] = 0

                    if event.key == pygame.K_d:
                        self.movement[1] = 1.7
                        self.move = True
                        if self.player.wall_slide:
                            self.player.wall_slide = False
                            self.player.velocity[0] = 2
                            self.player.jumps = 1
                            self.movement[0] = 0
                            
                        
                    if self.player.dashing < 50:
                        if not self.transition:
                            if event.key == pygame.K_s:
                                self.s = True
                                if self.player.wall_slide:
                                    self.player.wall_slide = False
                                    self.player.velocity[0] = 0
                                
                            if event.key == pygame.K_w:
                                self.w = True
                                if self.player.jump():
                                    self.sfx["jump"].play()
                    if event.key == pygame.K_SPACE and self.s == True:
                        self.player.dashdown()
                    elif event.key == pygame.K_SPACE and self.w == True:
                        self.player.dashup()
                    elif event.key == pygame.K_SPACE:
                        self.player.dash()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                        if event.key == pygame.K_d:
                            self.move = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                        if event.key == pygame.K_a:
                            self.move = False
                    if event.key == pygame.K_w:
                        self.w = False
                    if event.key == pygame.K_s:
                        self.s = False
                        
            self.check_hold = pygame.key.get_pressed()

            if self.move == False and not self.player.wall_slide and self.player.jumps == 2:
                self.movement[1] = 0
                self.movement[0] = 0
              
            if self.transition:
                self.movement[0] = 0
                self.movement[1] = 0
                self.player.velocity[0] = 0
                self.player.velocity[1] = 0
                self.player.dashing = 50
                self.player.cooldown = 30
                self.player.iframes = 20
                self.player.dash_up = 0
                self.player.dash_down = 0
                
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 18)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
                
            self.display_no_overlay.blit(self.display, (0, 0))
                        
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_no_overlay, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)
    
    def pause_menu(self):
        self.pause = True
        click = False  # Move outside the loop

        self.sfx["ambience"].stop()
        pygame.mixer.music.set_volume(0.1)

        while self.pause:
            self.pause_tid += 1
            self.screen.fill((0, 0, 0))  # Fill with black

            mx, my = pygame.mouse.get_pos()

            button_1 = pygame.Rect(50, 100, 200, 50)
            button_2 = pygame.Rect(50, 200, 200, 50)

            pygame.draw.rect(self.screen, (255, 0, 0), button_1)
            pygame.draw.rect(self.screen, (255, 0, 0), button_2)

            self.draw_text("Resume Game", 70, 115)
            self.draw_text("Main Menu", 110, 215)

            if button_1.collidepoint((mx, my)) and click:
                self.pause_tid = 0
                self.pause = False
                
                
            if button_2.collidepoint((mx, my)) and click:
                self.pause = False
                Game().main_menu()

            click = False  # Reset click after processing events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.pause_tid = 0
                    self.pause = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    click = True
            
            pygame.display.flip()
            self.clock.tick(60)

Game().main_menu()