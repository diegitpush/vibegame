# Vibegame

This is a 2D game completely vibe coded.

## How to Play

Six teams compete on a 10x8 grid map. You control the Azure team while AI controls the other five teams (Crimson, Verdant, Solar, Mystic, and Ember).

### Controls

- **Click** your territory, then click an adjacent enemy territory to attack
- **H** - Spend 10 resources to boost happiness
- **M** - Spend 10 resources to boost military power
- **SPACE** - End your turn

### Rules

- **Turn-based**: Take your actions, then press SPACE to end your turn. AI teams act in sequence after you.
- **Stats**: Each team has three stats:
  - **Resources** - Used to buy happiness and military power
  - **Happiness** - Affects resource growth; decays by 5 each turn
  - **Military Power** - Determines attack strength
- **Territory**: More territories = more resource growth
- **Combat**: Attack adjacent enemy territories. Success depends on military power with some randomness.
- **Elimination**: A team is eliminated when they lose all territories.
