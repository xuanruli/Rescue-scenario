# Logical Rescue Robot

A simulation of a rescue robot navigating a partially observable environment to save a human while avoiding dangers.

## Overview

You control a rescue robot tasked with finding and rescuing human from a cave system inhabited by dangerous monster and treacherous pits. The robot uses logical inference to build knowledge about its environment and make intelligent decisions.

## Key Features

- **Partial Observability**: The robot has limited perception and must use logical reasoning to infer the state of the world
- **Knowledge-Based Agent**: The robot builds and updates a knowledge base to track what it knows about the environment
- **Logical Inference**: Multiple levels of inference are used to determine safe paths and identify dangers
- **Pathfinding**: BFS algorithm finds optimal paths to targets

## How to Run

To run one of the predefined scenarios (Available scenarios range from S1 to S6):

```
python3 monster_world.py S1
```


## Inference & Action Systems
### Inference Levels
1. **Basic Perception**: Updates KB from percepts (breeze, stench, bumps)
2. **Constraint Reasoning**: Deduces dangers when only one possible location exists
3. **Model-Based Reasoning**: Tests if knowledge entails specific facts by checking possible worlds

### Action Priority
1. **Mission Critical**: Grab human, exit with human, shoot monster when possible
2. **Exploration**: Find and follow shortest path to nearest unvisited safe room
3. **Random**: Choose safe random actions when no clear targets remain

## Game End Conditions

- **Success**: Robot rescues human and exits the cave
- **Failure**: Robot falls into a pit or is eaten by a monster

## Screenshots

![Shooting a monster](graph/img_1.png)  
*The robot eliminating a monster with its blaster*

![Game Complete](graph/img.png)  
*Success screen after rescuing human and exiting the cave*
