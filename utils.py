def flatten(tup):
    if len(tup) == 1:
        return tup[0]
    return tup

def get_direction(degrees):
    fraction = (degrees % 360) / 360
    orientation = None
    match fraction:
        case 0:
            orientation = "up"
        case 0.25:
            orientation = "right"
        case 0.5:
            orientation = "down"
        case 0.75:
            orientation = "left"
    return orientation

def is_facing_monster(agent):
    """You may wish to use this in all_safe_next_actions"""
    if agent.KB.monster == set():
        return False
    x, y = agent.loc
    wx, wy = agent.KB.monster
    direction = get_direction(agent.degrees)
    return (direction == "up" and wx == x and wy > y) or \
            (direction == "down" and wx == x and wy < y) or \
            (direction == "left" and wx < x and wy == y) or \
            (direction == "right" and wx > x and wy == y)