import pygame
import sys
import random
from collections import deque

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_COLOR = (255, 0, 0)
PLATFORM_COLOR = (0, 255, 0)
BACKGROUND_COLOR = (20, 20, 40)
REWIND_TRAIL_COLOR = (255, 0, 0, 100)
MAX_HISTORY = 300
NORMAL_GRAVITY = 0.45

class WardenAI:
    def __init__(self, level, player):
        self.level = level
        self.player = player
        self.glitch_timer = 0
        self.glitch_interval = random.randint(300, 600)
        self.active_glitch = None
        self.glitch_duration = 0

    def update(self):
        if self.active_glitch:
            self.run_active_glitch()
        else:
            self.glitch_timer += 1
            if self.glitch_timer >= self.glitch_interval:
                self.trigger_random_glitch()
                self.glitch_timer = 0
                self.glitch_interval = random.randint(300, 600)

    def trigger_random_glitch(self):
        glitch_type = random.choice(['platform_flicker', 'gravity_shift', 'control_scramble'])
        
        if glitch_type == 'platform_flicker':
            self.active_glitch = 'platform_flicker'
            self.glitch_duration = 120 # 2 seconds
            if self.level.platform_list:
                self.target_platform = random.choice(self.level.platform_list.sprites())
                self.level.platform_list.remove(self.target_platform)

        elif glitch_type == 'gravity_shift':
            self.active_glitch = 'gravity_shift'
            self.glitch_duration = 180 # 3 seconds
            self.player.gravity_modifier = -1

        elif glitch_type == 'control_scramble':
            self.active_glitch = 'control_scramble'
            self.glitch_duration = 240 # 4 seconds
            self.player.controls_scrambled = True

    def run_active_glitch(self):
        self.glitch_duration -= 1
        if self.glitch_duration <= 0:
            self.end_glitch()

    def end_glitch(self):
        if self.active_glitch == 'platform_flicker':
            self.level.platform_list.add(self.target_platform)
        
        elif self.active_glitch == 'gravity_shift':
            self.player.gravity_modifier = 1

        elif self.active_glitch == 'control_scramble':
            self.player.controls_scrambled = False
            
        self.active_glitch = None

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([40, 50])
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = SCREEN_HEIGHT - self.rect.height - 100
        
        self.change_x = 0
        self.change_y = 0
        self.level = None
        self.is_rewinding = False
        self.history = deque(maxlen=MAX_HISTORY)
        self.gravity_modifier = 1
        self.controls_scrambled = False

    def update(self):
        if self.is_rewinding:
            self.rewind()
        else:
            self.calc_grav()
            self.rect.x += self.change_x
            
            block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
            for block in block_hit_list:
                if self.change_x > 0:
                    self.rect.right = block.rect.left
                elif self.change_x < 0:
                    self.rect.left = block.rect.right

            self.rect.y += self.change_y

            block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
            for block in block_hit_list:
                if self.change_y > 0:
                    self.rect.bottom = block.rect.top
                elif self.change_y < 0:
                    self.rect.top = block.rect.bottom
                self.change_y = 0
            
            self.record_history()

    def record_history(self):
        if not self.is_rewinding:
            self.history.append((self.rect.x, self.rect.y))

    def rewind(self):
        if len(self.history) > 0:
            last_pos = self.history.pop()
            self.rect.x, self.rect.y = last_pos
        else:
            self.is_rewinding = False

    def calc_grav(self):
        if self.change_y == 0:
            self.change_y = 1 * self.gravity_modifier
        else:
            self.change_y += NORMAL_GRAVITY * self.gravity_modifier

    def jump(self):
        if self.is_rewinding: return
        
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        self.rect.y -= 2
        
        if len(platform_hit_list) > 0 and self.gravity_modifier > 0:
            self.change_y = -12
    
    def go_left(self):
        if not self.is_rewinding:
            self.change_x = 6 if self.controls_scrambled else -6

    def go_right(self):
        if not self.is_rewinding:
            self.change_x = -6 if self.controls_scrambled else 6

    def stop(self):
        self.change_x = 0

class Platform(pygame.sprite.Sprite):
    def __init__(self, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(PLATFORM_COLOR)
        self.rect = self.image.get_rect()

class Level:
    def __init__(self, player):
        self.platform_list = pygame.sprite.Group()
        self.player = player

    def update(self):
        self.platform_list.update()

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)
        
        if self.player.is_rewinding and len(self.player.history) > 0:
            for i, pos in enumerate(list(self.player.history)[-50:]):
                alpha = int(255 * (i / 50))
                trail_surf = pygame.Surface((40, 50), pygame.SRCALPHA)
                trail_surf.fill((255, 100, 100, alpha))
                screen.blit(trail_surf, pos)

        self.platform_list.draw(screen)

class Level_01(Level):
    def __init__(self, player):
        Level.__init__(self, player)
        
        level_platforms = [
            [500, 50, 0, SCREEN_HEIGHT - 50],
            [200, 50, 600, SCREEN_HEIGHT - 180],
            [250, 50, 900, SCREEN_HEIGHT - 350],
        ]
        
        for platform_data in level_platforms:
            block = Platform(platform_data[0], platform_data[1])
            block.rect.x = platform_data[2]
            block.rect.y = platform_data[3]
            block.player = self.player
            self.platform_list.add(block)

def main():
    pygame.init()

    size = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Chrono-Glitch")
    
    player = Player()
    
    level_list = []
    level_list.append(Level_01(player))
    
    current_level_no = 0
    current_level = level_list[current_level_no]
    
    player.level = current_level
    
    warden = WardenAI(current_level, player)

    active_sprite_list = pygame.sprite.Group()
    active_sprite_list.add(player)
    
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    player.go_left()
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    player.go_right()
                if event.key == pygame.K_UP or event.key == pygame.K_w or event.key == pygame.K_SPACE:
                    player.jump()
                if event.key == pygame.K_r:
                    player.is_rewinding = True
            
            if event.type == pygame.KEYUP:
                if (event.key == pygame.K_LEFT or event.key == pygame.K_a):
                    if not (player.controls_scrambled and player.change_x > 0) and player.change_x < 0:
                        player.stop()
                if (event.key == pygame.K_RIGHT or event.key == pygame.K_d):
                     if not (player.controls_scrambled and player.change_x < 0) and player.change_x > 0:
                        player.stop()
                if event.key == pygame.K_r:
                    player.is_rewinding = False
        
        if not player.is_rewinding:
            warden.update()

        active_sprite_list.update()
        current_level.update()
        
        current_level.draw(screen)
        active_sprite_list.draw(screen)
        
        clock.tick(60)
        
        pygame.display.flip()

if __name__ == "__main__":
    main()