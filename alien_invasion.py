import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
    """管理游戏资源和行为的类"""

    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()

        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        # 默认在全屏模式下进行游戏
        # self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        # self.settings.screen_width = self.screen.get_rect().width
        # self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")

        # 创建一个用于存储游戏统计信息的实例,并创建记分牌
        self.stats = GameStats(self)
        self.scoreboard = Scoreboard(self)
        # 设置背景色
        self.bg_color = (230, 230, 230)
        # 创建Play按钮
        self.play_button = Button(self, 'Play')
        # 创建飞船
        self.ship = Ship(self)
        # 创建子弹编组
        self.bullets = pygame.sprite.Group()
        # 创建外星人编组
        self.aliens = pygame.sprite.Group()
        # 创建外星人舰队
        self._create_fleet()

    def run_game(self):
        """开始游戏的主循环"""
        while True:
            self._check_events()

            # 只有在游戏状态处于活动状态时运行
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._upadate_screen()
            
    def _check_events(self):
        """响应按键和鼠标事件（辅助方法）"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_keydown_events(self, event):
        """响应按键"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """响应松开"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _check_play_button(self, mouse_pos):
        """在玩家单击Play按钮时开始新游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        # 仅当单击了Play按钮且游戏当前处于非活动状态时，游戏才重新开始
        if button_clicked and not self.stats.game_active:
            # 重置游戏设置
            self.settings.initialize_dynamic_settings()

            # 重置游戏统计信息
            self.stats.reset_stats()
            self.stats.game_active = True
            self.scoreboard.prep_score()
            self.scoreboard.prep_level()
            self.scoreboard.prep_ships()

            # 清空余下的外星人和子弹
            self.aliens.empty()
            self.bullets.empty()

            # 创建一群新的外星人，并将飞船放到屏幕底端的中央
            self._create_fleet()
            self.ship.center_ship()

            # 隐藏鼠标光标
            pygame.mouse.set_visible(False)

    def _fire_bullet(self):
        """创建一颗子弹，并将其加入至bullets编组中"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """更新子弹的位置并删除消失的子弹"""
        self.bullets.update()

        # 删除消失的子弹
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """响应子弹和外星人的碰撞"""
        # 检查是否有子弹击中了外星人
        # 若是，则删除相应的子弹和外星人
        collisions = pygame.sprite.groupcollide(
                        self.bullets, self.aliens, True, True)

        # 当有外星人被击中时，更新得分
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.scoreboard.prep_score()
            self.scoreboard.check_high_score()

        # 当一个外星人舰队被消灭后，再新建一个
        if not self.aliens:
            # 删除现有的子弹并新建一群外星人
            self.bullets.empty()
            self._create_fleet()
            # 提高游戏的速度
            self.settings.increase_speed()

            # 提高玩家的等级
            self.stats.level += 1
            self.scoreboard.prep_level()

    def _create_alien(self, alien_number, row_number):
        """创建一个外星人并将其放在当前行"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + (2 * alien_width * alien_number)
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + (2 * alien_height * row_number)
        self.aliens.add(alien)

    def _create_fleet(self):
        """创建外星人舰队"""
        # 创建一个外星人并计算一行可容纳多少个外星人
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height -
                                (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        # 创建多行外星人
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _check_fleet_edges(self):
        """当有外星人到达边缘时采取相应的措施"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _check_aliens_bottom(self):
        """检查是否有外星人到达了屏幕底端"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break

    def _change_fleet_direction(self):
        """将外星人舰队下移，并改变其方向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _ship_hit(self):
        """响应飞船被外星人撞到"""
        if self.stats.ships_left > 1:
            # 将剩余飞船数量减1，并更新记分牌中的统计
            self.stats.ships_left -= 1
            self.scoreboard.prep_ships()

            # 清空余下的外星人和子弹
            self.aliens.empty()
            self.bullets.empty()

            # 创建一群新的外星人，并将飞船放到屏幕底端的中央
            self._create_fleet()
            self.ship.center_ship()

            # 暂停
            sleep(1)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True) 

    def _update_aliens(self):
        """更新外星人舰队中所有外星人的位置"""
        self._check_fleet_edges()
        self.aliens.update()

        # 检查是否有外星人撞到了飞船
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # 检查是否有外星人到达了屏幕底端
        self._check_aliens_bottom()

    def _upadate_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
        # 绘制背景
        self.screen.fill(self.settings.bg_color)

        # 绘制飞船
        self.ship.blitme()

        # 绘制子弹
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()

        # 绘制外星人
        self.aliens.draw(self.screen)

        # 绘制记分牌
        self.scoreboard.show_score()

        # 如果游戏处于非活动状态，则绘制Play按钮
        if not self.stats.game_active:
            self.play_button.draw_button()

        # 让最近绘制的屏幕可见
        pygame.display.flip()

if __name__ == '__main__':
    # 创建游戏实例并运行游戏
    ai = AlienInvasion()
    ai.run_game()