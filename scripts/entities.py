
import math
import random

import pygame

from scripts.particle import Particle
from scripts.spark import Spark, Blood

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {"up": False, "down": False, "right": False, "left": False}
        
        self.action = ""
        self.anim_offset = (-9, -2)
        self.gun_anim_offset = (-9, -3)
        self.melee_anim_offset = (-12, -6)
        
        self.flip = False
        self.set_action("idle")
        
        self.last_movement = [0, 0]
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {"up": False, "down": False, "right": False, "left": False}
        
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions["right"] = True
                    
                    
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions["left"] = True
                    
                    
                    
                self.pos[0] = entity_rect.x
        
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y
                
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
            
        self.last_movement = movement
        
        self.velocity[1] = min(8, self.velocity[1] + 0.15)
        
        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0
            
        self.animation.update()
        
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
    
    def render_gun(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.gun_anim_offset[0], self.pos[1] - offset[1] + self.gun_anim_offset[1]))

    def render_melee(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.melee_anim_offset[0], self.pos[1] - offset[1] + self.melee_anim_offset[1]))

class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "enemy", pos, size)
        
        self.walking = 0
        self.fire_cd = 30
        
    def update(self, tilemap, movement=(0, 0)):
        
        
        
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 35)):
                if (self.collisions["right"] or self.collisions["left"]):
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.6 if self.flip else 0.6, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)

        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        
        super().update(tilemap, movement=movement)

        dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
        if (abs(dis[1]) < 22):
            if (self.flip and dis[0] < 0):
                self.set_action("shoot")
                self.fire_cd = max(0, self.fire_cd - 1)
                if self.fire_cd == 0:
                    self.game.sfx["shoot"].play()
                    self.game.projectiles.append([[self.rect().centerx -2, self.rect().centery -5], -1.5, 0])
                    for i in range(4):
                        self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))

            elif (not self.flip and dis[0] > 0):
                self.set_action("shoot")
                self.fire_cd = max(0, self.fire_cd - 1)
                if self.fire_cd == 0:
                    self.game.sfx["shoot"].play()
                    self.game.projectiles.append([[self.rect().centerx -2, self.rect().centery -10], 1.5, 0])
                    for i in range(4):
                        self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
            
            elif movement[0] != 0:
                self.set_action("run")
                self.fire_cd = min(60, self.fire_cd + 10)
            else:
                self.set_action("idle")
                self.fire_cd = min(60, self.fire_cd + 10)
        
        
        elif movement[0] != 0:
            self.set_action("run")
            self.fire_cd = min(60, self.fire_cd + 10)
        else:
            self.set_action("idle")
            self.fire_cd = min(60, self.fire_cd + 10)
        
        if self.fire_cd == 0:
            self.fire_cd = min(120, self.fire_cd + 120)

            
        if abs(self.game.player.dashing) >= 48 and self.game.dead == 0:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx["hit"].play()
                self.game.player.cooldown -= 35
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Blood(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, "particle2", self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                
                
                
                return True
            
        if abs(self.game.player.dash_up) >= 48 and self.game.dead == 0:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx["hit"].play()
                self.game.player.cooldown -= 35
            
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Blood(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, "particle2", self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                
                
                
                return True
        
        if abs(self.game.player.dash_down) >= 48 and self.game.dead == 0:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx["hit"].play()
                self.game.player.cooldown -= 35
                self.game.player.velocity[1] = -4
                self.game.player.jumps = 1
                self.game.player.dash_down = 0
                self.game.player.iframes = 10
            
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Blood(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, "particle2", self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                
                
                

                return True
                
            
    def render(self, surf, offset=(0, 0)):
        super().render_gun(surf, offset=offset)

class Enemy_m(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "enemy", pos, size)
        
        self.walking = 0
        self.air_time = 0
        
    def update(self, tilemap, movement=(0, 0)):
        dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
        
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 35)):
                if (self.collisions["right"] or self.collisions["left"]):
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.6 if self.flip else 0.6, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)

        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        if (abs(dis[1]) < 55 and abs(dis[1]) > -35):
            if (self.flip and dis[0] < 0):
                movement = (-1.5, movement[1])
                if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 35)):
                    self.flip = self.flip
                    
            elif (not self.flip and dis[0] > 0):
                movement = (1.5, movement[1])
                if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 35)):
                    self.flip = self.flip
                    
            else:
                if (self.collisions["right"]):
                    movement = (1.0, -4.0)
                if (self.collisions["left"]):
                    movement = (-1.0, -4.0)
            

            
            
        super().update(tilemap, movement=movement)

        if self.velocity[1] > 0:
            self.air_time += 1 * (self.velocity[1] // 4)

        if self.collisions["down"]:
            self.air_time = 0

        if self.air_time > 120:
            return True

        dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
        if (abs(dis[1]) < 22):
            if (self.flip and dis[0] < 0):
                self.walking == 1
                
            elif (not self.flip and dis[0] > 0):
                self.walking == 10
            
            elif movement[0] != 0:
                self.set_action("run_m")
                
            else:
                self.set_action("idle_m")

        if movement[0] != 0:
            self.set_action("run_m")
            
        else:
            self.set_action("idle_m")
            
        if abs(self.game.player.dashing) >= 48 and self.game.dead == 0:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx["hit"].play()
                self.game.player.cooldown -= 35
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Blood(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, "particle2", self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                
                return True
            
        if abs(self.game.player.dash_up) >= 48 and self.game.dead == 0:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx["hit"].play()
                self.game.player.cooldown -= 35
            
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Blood(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, "particle2", self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                
                return True
        
        if abs(self.game.player.dash_down) >= 48 and self.game.dead == 0:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx["hit"].play()
                self.game.player.cooldown -= 35
                self.game.player.velocity[1] = -4
                self.game.player.iframes = 10
                self.game.player.jumps = 1
                self.game.player.dash_down = 0
            
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Blood(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(Particle(self.game, "particle2", self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                
                return True

        if abs(self.game.player.dash_down) < 40 and abs(self.game.player.dash_up) < 48 and abs(self.game.player.dashing) < 48 and self.game.dead == 0:
            if self.rect().colliderect(self.game.player.rect()):
                print("")
                
                self.game.screenshake = max(30, self.game.screenshake)
                self.game.sfx["hit"].play()
                self.game.dead += 1
            
    def render(self, surf, offset=(0, 0)):
        super().render_melee(surf, offset=offset)

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        self.air_time = 0
        self.jumps = 2
        self.wall_slide = False
        self.dashing = 0
        self.cooldown = 1
        self.dash_up = 0
        self.dash_down = 0
        self.iframes = 30
        self.let_go = 0
        self.air_time_start = 0

    def update(self, tilemap, movement=(0, 0)):
        
        super().update(tilemap, movement=movement)
        
        self.iframes = max(0, self.iframes - 1)
        
        if not self.collisions["down"] or not self.wall_slide:
            self.air_time_start += 1
        

        if self.velocity[1] > 0:
            self.air_time += 1 * (self.velocity[1] // 4)
        elif self.velocity[1] < 0:
            self.air_time = max(5, self.air_time - 1 * ((self.velocity[1] * -1) // 4))

        self.cooldown = max(0, self.cooldown - 1)
        
        if self.air_time > 120:
            if not self.game.dead:
                self.game.screenshake = max(30, self.game.screenshake)
            self.game.dead += 1
        
        
            
        self.wall_slide = False
        
        if (self.collisions["right"] or self.collisions["left"]) and self.air_time > 4:
            self.air_time = 5
            self.wall_slide = True
            self.air_time_start = 0
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions["right"]:
                self.flip = False
                
            else:
                self.flip = True
                
            self.set_action("wall_slide")
        
        if self.collisions["down"]:
            self.air_time = 0
            self.jumps = 2
            self.air_time_start = 0

        
        if self.wall_slide and self.flip == False and self.air_time >= 4:
            self.velocity[0] = 1.1
            self.game.movement[1] = 1.7
            self.let_go = 1
        elif self.wall_slide and self.flip == True and self.air_time > 4:
            self.velocity[0] = -1.1
            self.game.movement[0] = 1.7
            self.let_go = 1
        
        
        print(self.game.move)
        if self.let_go == 1 and self.air_time_start == 1:
            self.game.movement[0] = 0
            self.game.movement[1] = 0
            self.let_go = 0
        


        if not self.wall_slide:
            
            if self.velocity[1] < 0:
                self.set_action("jump")

            elif self.air_time > 4:
                self.set_action("fall")
            elif movement[0] != 0 and not self.collisions["right"] or self.collisions["left"]:
                self.set_action("run")
            else:
                self.set_action("idle")
        
        if abs(self.dashing) in {60, 50}:
            
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, "particle", self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[1] = -0.1
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, "particle", self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        
        if abs(self.dash_up) in {60, 50}:
            
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.sin(angle) * speed, math.cos(angle) * speed]
                self.game.particles.append(Particle(self.game, "particle", self.rect().center, velocity=[0, 2], frame=random.randint(0, 7)))
        if self.collisions["up"] == True:
            self.dash_up = 0
        if self.dash_up > 0:
            self.dash_up = max(0, self.dash_up - 1)
        if self.dash_up < 0:
            self.dash_up = min(0, self.dash_up + 1)
        if abs(self.dash_up) > 50:
            self.velocity[1] = abs(self.dash_up) / self.dash_up * 8
            if abs(self.dash_up) == 51:
                self.velocity[1] *= 0.1
            pvelocity = [abs(self.dash_up) / self.dash_up * min(random.random() * 2 - random.random() * 2, 1.5), 2]
            self.game.particles.append(Particle(self.game, "particle", self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))

        if abs(self.dash_down) in {60, 50}:
            
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.sin(angle) * speed, math.cos(angle) * speed]
                self.game.particles.append(Particle(self.game, "particle", self.rect().center, velocity=[0, 2], frame=random.randint(0, 7)))
            if self.collisions["down"] == True:
                self.dash_down = 0
                
        if self.dash_down > 0:
            self.dash_down = max(0, self.dash_down - 1)
        if self.dash_down < 0:
            self.dash_down = min(0, self.dash_down + 1)
        if abs(self.dash_down) > 50:
            self.velocity[1] = abs(self.dash_down) / self.dash_down * 8
            
            pvelocity = [abs(self.dash_down) / self.dash_down * min(random.random() * 2 - random.random() * 2, 1.5), -1.5]
            self.game.particles.append(Particle(self.game, "particle", self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
    
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing or self.dash_down or self.dash_up) <= 50:
            super().render(surf, offset=offset)
            
    def jump(self):
        if self.wall_slide:
            self.jumps = 2
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 4
                self.velocity[1] = -3.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                self.game.movement[1] = 0
                self.game.movement[0] = 0
                return True
                
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -4
                self.velocity[1] = -3.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                self.game.movement[1] = 0
                self.game.movement[0] = 0
                return True
                
        elif not self.wall_slide:       
            if self.jumps == 2:
                self.velocity[1] = -4.0
                self.jumps -= 1
                self.air_time = 5
                return True
                
            elif self.jumps == 1 and not (self.collisions["right"] or self.collisions["left"]):
                self.velocity[1] = -3.3
                self.velocity[0] = 0
                self.jumps -= 1
                self.air_time = 5

                for i in range(13):
                    self.game.particles.append(Particle(self.game, "particle", self.rect().center, velocity=[min(random.random() * 2 - random.random() * 2, 1.5), random.random() / 2 * -1], frame=random.randint(0, 7)))
                return True
    
    def dash(self):
        if self.cooldown <= 0:
            self.game.sfx["dash"].play()
            self.cooldown = 65
            if self.flip:
                self.dashing = -65
            else:
                self.dashing = 65

    def dashup(self):
        if self.cooldown <= 0:
            self.game.sfx["dash"].play()
            self.cooldown = 65
            if self.flip:
                self.dash_up = -62
            else:
                self.dash_up = -62

    def dashdown(self):
        if self.air_time >= 5:
            if self.cooldown <= 0:
                self.game.sfx["dash"].play()
                self.cooldown = 65
                if self.flip:
                    self.dash_down = 62
                else:
                    self.dash_down = 62