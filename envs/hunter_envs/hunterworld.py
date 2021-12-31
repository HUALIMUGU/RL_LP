from envs.pygamewrapper import PyGameWrapper
import sys
sys.path.append('.')
from agent import *
from utils import *
from pygame.constants import *
import pygame
from numpy import random
from math import sqrt, sin, cos

import pyximport
pyximport.install()
from hunter_utils import *

COLOR_MAP = {"white": (255, 255, 255),
             "hunter": (0, 0, 255),
             "prey": (20, 255, 20),
             "toxin": (255, 20, 20),
             'grey': (144, 144, 144),
             'n':(178,34,34)}

Key_mapping = {
    0: {"up": K_UP, "left": K_LEFT, "right": K_RIGHT, "down": K_DOWN},
    1: {"up": K_w, "left": K_a, "right": K_d, "down": K_s},
    2: {"up": K_3, "left": K_4, "right": K_e, "down": K_r},
    3: {"up": K_5, "left": K_6, "right": K_t, "down": K_y},
    4: {"up": K_7, "left": K_8, "right": K_u, "down": K_i},
    5: {"up": K_9, "left": K_0, "right": K_o, "down": K_p},
    6: {"up": K_a, "left": K_s, "right": K_z, "down": K_x},
    7: {"up": K_d, "left": K_f, "right": K_c, "down": K_v},
    8: {"up": K_g, "left": K_h, "right": K_b, "down": K_n},
    9: {"up": K_j, "left": K_k, "right": K_m, "down": K_COMMA}
}


class HunterWorld(PyGameWrapper):
    def __init__(self, draw=False, width=100, height=100, num_preys=10, num_hunters=1, num_toxins=10):

        self.actions = {k: Key_mapping[k] for k in sorted(Key_mapping.keys())[:num_hunters]}

        PyGameWrapper.__init__(self, width, height, actions=self.actions)
        self.draw = draw
        self.BG_COLOR = COLOR_MAP['white']
        self.EYES = 24

        self.MAX_HUNTER_NUM = num_hunters
        self.HUNTER_NUM = num_hunters
        self.HUNTER_COLOR = COLOR_MAP['hunter']
        self.HUNTER_SPEED = width * 0.5*2
        self.HUNTER_RADIUS = percent_round_int(width, 0.02)
        self.hunters = pygame.sprite.Group()
        self.hunters_dic = {}
        self.over = False

        self.PREY_COLOR = COLOR_MAP['prey']
        self.PREY_SPEED = width * 0.1*2
        self.PREY_NUM = num_preys
        self.PREY_RADIUS = percent_round_int(width, 0.02)
        self.preys = pygame.sprite.Group()

        self.TOXIN_NUM = num_toxins
        self.TOXIN_COLOR = COLOR_MAP['toxin']
        self.TOXIN_SPEED = 0.25 * width
        self.TOXIN_RADIUS = percent_round_int(width, 0.015)
        self.toxins = pygame.sprite.Group()
        self.walls = None
        self.preys_num = num_preys
        self.toxins_num = num_toxins
        self.all_entities = None

        self.observation = np.zeros((self.MAX_HUNTER_NUM, self.EYES * (num_hunters + 3) + 2))
        self.reward = np.zeros(self.HUNTER_NUM)
        self.info = np.zeros((self.HUNTER_NUM, self.HUNTER_NUM), dtype=int)
        self.info2 = np.zeros((self.HUNTER_NUM, self.HUNTER_NUM), dtype=int)
        self.onehot = self.agent_one_hot(self.HUNTER_NUM)

    def agent_one_hot(self, agent_num):  #对角矩阵
        tmp = np.zeros((agent_num, agent_num), dtype=int)
        for i in range(agent_num):
            tmp[i][i] = 1
        return tmp

    def _rand_postion(self, agents):
        pos = []
        for agent in agents:
            pos_x = random.uniform(agent.radius, self.width - agent.radius)
            pos_y = random.uniform(agent.radius, self.height - agent.radius)
            pos.append([pos_x, pos_y])

        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                dist = math.sqrt((pos[i][0] - pos[j][0]) ** 2 + (pos[i][1] - pos[j][1]) ** 2)
                while dist <= (agents[i].radius + agents[j].radius):
                    pos[i][0] = random.uniform(agents[i].radius, self.width - agents[i].radius)
                    pos[i][1] = random.uniform(agents[i].radius, self.height - agents[i].radius)
                    dist = math.sqrt((pos[i][0] - pos[j][0]) ** 2 + (pos[i][1] - pos[j][1]) ** 2)
        return pos

    def _init_postions(self):
        pos_list = [list(self.rng.rand(2, )) for _ in range(50)]
        return [[pos_list[i][0] * self.width, pos_list[i][1] * self.height] for i in range(len(pos_list))]

    def _init_directions(self):
        dir_list = [list(self.rng.rand(2, ) - 0.5) for _ in range(50)]
        return [normalization(dir_list[i]) for i in range(len(dir_list))]

    def get_score(self):
        return self.score

    def game_over(self):
        return False

    def init(self):

        self.all_entities = []
        self.walls = []
        self.toxins.empty()
        self.preys.empty()
        self.hunters.empty()
        self.hunters_dic = {}
        self.font = pygame.font.SysFont("monospace", 18)
        self.blood = [100,100,100,100,100]

        self.walls = []
        self.FIX_DIR = self._init_directions()
        self.FIX_POS = self._init_postions()

        id = 0
        for _ in range(self.HUNTER_NUM):
            if id ==0 :
                hunter = Hunter(id, self.HUNTER_RADIUS, self.HUNTER_COLOR,
                                self.HUNTER_SPEED, self.width, self.height, self.walls, type='hunter')
                hunter.init_direction((0, 0))
                hunter.init_positon(self.FIX_POS[id])
                self.hunters.add(hunter)
                self.hunters_dic[id] = hunter
                self.all_entities.append(hunter)
            else:
                prey = Other(id, self.PREY_RADIUS, self.PREY_COLOR, self.PREY_SPEED,
                             self.width, self.height, self.walls, type='hunter')
                prey.init_direction(self.FIX_DIR[id])
                prey.init_positon(self.FIX_POS[id])
                self.hunters.add(prey)
                self.hunters_dic[id] = prey
                self.all_entities.append(prey)
            id += 1

    def reset(self):
        for agent in self.all_entities:
            agent.reset_pos()
            agent.reset_orientation()

    def _handle_player_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                key = event.key

                for idx, actions in self.actions.items():
                    if idx in self.hunters_dic:
                        agent = self.hunters_dic[idx]

                        if key == actions["left"]:
                            agent.dx = -agent.speed
                            agent.dy = 0
                            agent.accelerate = True

                        if key == actions["right"]:
                            agent.dx = agent.speed
                            agent.dy = 0
                            agent.accelerate = True

                        if key == actions["up"]:
                            agent.dy = -agent.speed
                            agent.dx = 0
                            agent.accelerate = True

                        if key == actions["down"]:
                            agent.dy = agent.speed
                            agent.dx = 0
                            agent.accelerate = True

    # @profile
    def step(self, dt):
        self.reward[:] = 0.0
        self.info[:] = 0
        self.info2[:] = 0
        if self.game_over():
            return self.reward

        dt /= 1000.0
        self.screen.fill(self.BG_COLOR)
        self._handle_player_events()

        for hunter_1 in self.hunters:
            for hunter_2 in self.hunters:
                if hunter_1.id <= hunter_2.id or self.blood[hunter_1.id]<1 or self.blood[hunter_2.id]<1 :continue
                if count_distance_fast(hunter_1.pos[0], hunter_1.pos[1], hunter_2.pos[0], hunter_2.pos[1]) <= (hunter_2.range - hunter_1.radius):
                    self.blood[hunter_1.id] -= 1
                    self.blood[hunter_2.id] -= 1
                    if hunter_1.id or hunter_2.id != 0:
                        self.reward[0] += self.rewards["positive"]
        # print(self.blood)
        i = 0
        dic = {}
        for k, v in self.hunters.spritedict.items():
            if self.blood[i] > 0:
                dic[k] = v
            if self.blood[i]<=0 and i == 0:
                self.over = True
            i = i + 1
        self.hunters.spritedict = dic


        dic = {}
        j = 0
        for k, v in self.hunters_dic.items():
            if self.blood[k] > 0:
                dic[j] = v
                j=j+1
        self.hunters_dic = dic

        i = 0
        dic = []
        for k in self.all_entities:
            if self.blood[i] > 0:
                dic.append(k)
            i = i + 1
        self.all_entities = dic


        loc = []
        temp = []
        for i in range(self.HUNTER_NUM):
            if self.blood[i]>0:
                loc.append(i)
                temp.append(self.blood[i])
        self.blood = temp

        self.HUNTER_NUM = len(self.hunters.spritedict)

        i = 0
        for h in self.hunters:
            h.id = i
            i =i + 1

        self.hunters.update(dt)
        if self.draw:
            self.hunters.draw(self.screen)


            for idx in range(self.HUNTER_NUM):
                # label = self.font.render(str(idx), 1, (0, 0, 0))
                label = self.font.render(str(self.blood[idx]), 1, (0, 0, 0))
                self.screen.blit(label,
                                 (self.hunters_dic[idx].rect.center[0] + 5, self.hunters_dic[idx].rect.center[1] + 5))

            self.get_game_state()

        return self.reward, self.info


    def get_game_state(self):
        self.observation[:] = 0
        self.info2[:] = 0

        for i in range(self.HUNTER_NUM):
            if self.blood[i] > 0:
                hunter = self.hunters_dic[i]
                other_agents = []
                for j in range(len(self.all_entities)):
                    agent = self.all_entities[j]
                    # if agent is hunter: continue
                    if count_distance_fast(agent.pos[0], agent.pos[1], hunter.pos[0],
                                           hunter.pos[1]) <= agent.radius + hunter.out_radius:
                        other_agents.append(agent)

                ob = self.observe1(hunter, other_agents)
                state = np.append(ob, [hunter.velocity[0] / self.width, hunter.velocity[1] / self.height])
                self.observation[i] = state[:]
        assert self.observation.shape == (self.MAX_HUNTER_NUM, self.EYES * (self.MAX_HUNTER_NUM + 3) + 2)
        return self.observation

    # @profile
    def observe1(self, hunter, others):
        center = list(hunter.rect.center)
        out_radius = hunter.out_radius - hunter.radius
        observation = np.zeros((self.EYES, 3 + self.MAX_HUNTER_NUM))
        angle = 2 * np.pi / self.EYES
        other_agents = others[:]
        for i in range(0, self.EYES):
            sin_angle = sin(angle * i)
            cos_angle = cos(angle * i)

            for agent in other_agents:
                dis = line_distance_fast(center[0], center[1], sin_angle, -cos_angle, hunter.out_radius,
                                         agent.rect.center[0], agent.rect.center[1], agent.radius)
                # dis = self.line_distance1(center, [sin_angle, -cos_angle], hunter.out_radius, agent.rect.center, agent.radius)
                if dis is not False:
                    dis = max(dis - hunter.radius, 0)
                    assert 0 <= dis <= out_radius, str(dis)
                    if agent.type == 'hunter':
                        observation[i][1] = 1.0 - dis / out_radius
                        self.draw_line(center, sin_angle, cos_angle, hunter, dis, COLOR_MAP["n"])
                    break

        return observation

    def dian(self,start_pos,end_pos,n):
        x = (end_pos[0] - start_pos[0])/n
        y = (end_pos[1] - start_pos[1])/n
        dian_ji = []
        for i in range(n):
            dian_ji.append((int(start_pos[0]+i*x),int(start_pos[1]+i*y)))
        return dian_ji

    def draw_line(self, center, sin_angle, cos_angle, hunter, line, color):
        if self.draw:
            start_pos = [center[0] + sin_angle * hunter.radius, center[1] - cos_angle * hunter.radius]
            end_pos = [0, 0]
            end_pos[0] = start_pos[0] + int(sin_angle * line)
            end_pos[1] = start_pos[1] - int(cos_angle * line)
            # pygame.draw.line(self.screen, color, start_pos, end_pos, 1)
            dianji = self.dian(start_pos,end_pos,10)
            for dian in dianji:
                pygame.draw.circle(self.screen, color, dian, 1, 1)

    # http://doswa.com/2009/07/13/circle-segment-intersectioncollision.html
    def line_distance1(self, seg_a, seg_v_unit, seg_v_len, circ_pos, circ_rad):
        pt_v = [circ_pos[0] - seg_a[0], circ_pos[1] - seg_a[1]]
        proj = pt_v[0] * seg_v_unit[0] + pt_v[1] * seg_v_unit[1]
        if proj <= 0 or proj >= seg_v_len:
            return False
        proj_v = [seg_v_unit[0] * proj, seg_v_unit[1] * proj]
        closest = [int(proj_v[0] + seg_a[0]), int(proj_v[1] + seg_a[1])]
        dist_v = [circ_pos[0] - closest[0], circ_pos[1] - closest[1]]
        offset = sqrt(dist_v[0] ** 2 + dist_v[1] ** 2)
        if offset >= circ_rad:
            return False
        le = sqrt(circ_rad ** 2 - int(offset) ** 2)
        re = [closest[0] - seg_a[0], closest[1] - seg_a[1]]
        # if sqrt(re[0] ** 2 + re[1] ** 2) - le < 0:
        #     a = 1
        #     print a

        return sqrt(re[0] ** 2 + re[1] ** 2) - le


if __name__ == "__main__":
    import numpy as np
    import time

    pygame.init()
    game = HunterWorld(width=500, height=500, num_preys=5, num_hunters=5, num_toxins=0,draw=True)
    game.screen = pygame.display.set_mode(game.get_screen_dims(), 0, 32)
    game.clock = pygame.time.Clock()
    game.rng = np.random.RandomState(24)
    game.init()
    game.reset()

    while True:
        start = time.time()
        dt = game.clock.tick_busy_loop(30)
        if game.game_over():
            game.init()
        reward = game.step(dt)
        pygame.display.update()
        end = time.time()
        game.get_game_state()

