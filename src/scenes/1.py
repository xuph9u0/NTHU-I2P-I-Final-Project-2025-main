class Character:
    def __init__(self, name, hp, attack, defense):
        self.name = name
        self.hp = hp
        self.attack = attack
        self.defense = defense
        self.buff_func = lambda atk, dfs, hp: (atk, dfs, hp)  # identity function

    def apply_buffs(self):
        self.hp,self.attack,self.defence=self.buff_func(self.hp,self.attack,self.defence)
        return self.hp,self.attack,self.defence
  
    def is_alive(self):
        return self.hp>0

    def take_damage(self, amount):
        self.hp-=amount
  
    def attack_target(self, other):
        dmg=max(1,self.attack-others.defence)
        other.take_damage(dmg)

  
def compose_buffs(*funcs):
    """Compose multiple buffs into one function."""
    pass
  
def buff_factory(cmd, x):
    """Return a buff function that modifies (atk, dfs, hp)."""
    if cmd == "atk_add":
        pass
    elif cmd == "atk_mul":
        pass
    elif cmd == "dfs_add":
        pass
    elif cmd == "dfs_mul":
        pass
    else:
        pass
  
def battle(c1, c2):
    turn=0
    while c1.is_alive and c2.is_alive:

        c1.apply_buffs()
        c2.apply_buffs()

        if turn%2==0:
            c1 attack_target(c2)
        else:
            c2 attack_target(c1)
    if c1.is_alive():
        return c1.name,ci.hp
    else:
        return c2.name,c2.hp
  
if __name__ == "__main__":
    # Input format:
    # name1 hp1 atk1 dfs1
    # name2 hp2 atk2 dfs2
    # n
    # Then n lines:
    # target cmd value
    # (target is either name1 or name2)
    n1, h1, a1, d1 = input().split()
    n2, h2, a2, d2 = input().split()
    c1 = Character(n1, int(h1), int(a1), int(d1))
    c2 = Character(n2, int(h2), int(a2), int(d2))
  
    n = int(input())
    buffs_c1 = []
    buffs_c2 = []
    for _ in range(n):
        target, cmd, val = input().split()
        buff = buff_factory(cmd, float(val))
        if target == c1.name:
            buffs_c1.append(buff)
        elif target == c2.name:
            buffs_c2.append(buff)
  
    c1.buff_func = compose_buffs(*buffs_c1)
    c2.buff_func = compose_buffs(*buffs_c2)
  
    winner, hp_left = battle(c1, c2)
    print(f"{winner} wins with {hp_left:.1f} HP left.")