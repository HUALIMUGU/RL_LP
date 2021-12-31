class Other(Agent):
    def __init__(self, id, radius, color, speed, screen_width, screen_height, walls, type):
        Agent.__init__(self, id, radius, speed, screen_width, screen_height, walls, type)
        image = pygame.Surface([radius * 2, radius * 2])
        image.set_colorkey((0, 0, 0))
        pygame.draw.circle(
            image,
            color,
            (radius, radius),
            radius,
            0
        )
        self.image = image.convert()
        self.rect = self.image.get_rect()

    def update(self, dt):
        new_x = self.pos[0] + self.velocity[0] * self.speed * dt
        new_y = self.pos[1] + self.velocity[1] * self.speed * dt

        flag = True
        for wall in self.walls:
            if wall.rect.left < new_x < wall.rect.right:
                if wall.rect.top < new_y - self.radius < wall.rect.bottom:
                    self.pos[1] = wall.rect.bottom + self.radius
                    self.velocity[1] = -self.velocity[1]
                    flag = False
                elif wall.rect.top < new_y + self.radius < wall.rect.bottom:
                    self.pos[1] = wall.rect.top - self.radius
                    self.velocity[1] = -self.velocity[1]
                    flag = False
            if wall.rect.top < new_y < wall.rect.bottom:
                if wall.rect.left < new_x - self.radius < wall.rect.right:
                    self.pos[0] = wall.rect.right + self.radius
                    self.velocity[0] = -self.velocity[0]
                    flag = False
                elif wall.rect.left < new_x + self.radius < wall.rect.right:
                    self.pos[0] = wall.rect.left - self.radius
                    self.velocity[0] = -self.velocity[0]
                    flag = False

        if flag:
            if new_x >= self.SCREEN_WIDTH - self.radius:
                self.pos[0] = self.SCREEN_WIDTH - self.radius
                self.velocity[0] = -self.velocity[0]
            elif new_x < self.radius:
                self.pos[0] = self.radius
                self.velocity[0] = -self.velocity[0]
            else:
                self.pos[0] = new_x

            if new_y >= self.SCREEN_HEIGHT - self.radius:
                self.pos[1] = self.SCREEN_HEIGHT - self.radius
                self.velocity[1] = -self.velocity[1]
            elif new_y < self.radius:
                self.pos[1] = self.radius
                self.velocity[1] = -self.velocity[1]
            else:
                self.pos[1] = new_y

        self.rect.center = (self.pos[0], self.pos[1])