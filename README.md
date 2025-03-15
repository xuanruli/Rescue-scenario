# Wampa World: AI-Powered Rescue Robot

A simulation of a rescue robot navigating a partially observable environment to save a human while avoiding dangers.

## Overview

In Wampa World, you control a rescue robot (R2D2) tasked with finding and rescuing Luke Skywalker from a cave system inhabited by dangerous Wampas and treacherous pits. The robot uses logical inference to build knowledge about its environment and make intelligent decisions.

## Key Features

- **Partial Observability**: The robot has limited perception and must use logical reasoning to infer the state of the world
- **Knowledge-Based Agent**: The robot builds and updates a knowledge base to track what it knows about the environment
- **Logical Inference**: Multiple levels of inference are used to determine safe paths and identify dangers
- **Pathfinding**: BFS algorithm finds optimal paths to targets

## How to Run

To run one of the predefined scenarios (Available scenarios range from S1 to S6):

```
python3 wampa_world.py S1
```


## Inference & Action Systems
### Inference Levels
1. **Basic Perception**: Updates KB from percepts (breeze, stench, bumps)
2. **Constraint Reasoning**: Deduces dangers when only one possible location exists
3. **Model-Based Reasoning**: Tests if knowledge entails specific facts by checking possible worlds

### Action Priority
1. **Mission Critical**: Grab Luke, exit with Luke, shoot Wampas when possible
2. **Exploration**: Find and follow shortest path to nearest unvisited safe room
3. **Random**: Choose safe random actions when no clear targets remain

## Game End Conditions

- **Success**: Robot rescues Luke and exits the cave
- **Failure**: Robot falls into a pit or is eaten by a Wampa

## Screenshots

![Shooting a Wampa](img_1.png)  
*The robot eliminating a Wampa with its blaster*

![Game Complete](img.png)  
*Success screen after rescuing Luke and exiting the cave*
