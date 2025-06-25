# BulletStorm
- This project is a single-level clone of the classic game `Contra`.

# Object-Oriented Design
- The following class diagram describes the major classes with their important attributes and methods.

```mermaid
	classDiagram
		pygame_sprite_Sprite <|-- Entity
		pygame_sprite_Sprite <|-- Bullet
		pygame_sprite_Sprite <|-- BulletAnimation
		Entity <|-- Enemy
		Entity <|-- Player
		Entity : import_assets()
		Entity : damage()
		Entity : check_alive()
		Entity : invulnerable_timer()
		Entity : fire_bullet <Func>
		Entity : speed
		Entity : health
		Entity : move_dir
		Entity : pos_vector
		Entity : direction
		Entity : ducking
		Entity : can_shoot
		Entity : time_bw_shots
		Entity : vulnerable
		Enemy : get_face_dir()
		Enemy : should_fire()
		Enemy : update()
		Player : get_move_dir()
		Player : check_on_ground()
		Player : update()
		Player : input()
		Player : collision()
		Player : move()
		Player : on_ground
		Player : gravity
		Player : jump_speed
		Player : moving_floor
		Health_Indicator --* Player
		Health_Indicator : display_health()
		Health_Indicator : player
		Bullet : update()
		Bullet : direction
		Bullet : speed
		Bullet : position
		BulletAnimation --o Entity
		BulletAnimation : animate()
		BulletAnimation : move_with_entity()
		BulletAnimation : update()
```


## Features
- This is a single-level, single-player game.
- The game features multiple enemies who shoot at the player, moving platforms which the player can use to move onto higher platforms.
- The player has a health indicator.
- The game has sounds which play persistently as well as based on some event (firing a bullet).


## Controls
| Key | Action |
| --- | ------ |
| Up arrow key | Jump |
| Down arrow key | Duck |
| Left arrow key | Move left |
| Right arrow key | Move right |
| Spacebar | Shoot bullets |

## Requirements and Running the Project
- Maps for this game were created using Tiled Map Editor, it uses assets and sounds from multiple sources online.
- The project uses the following libraries as dependencies (can be sourced from https://pypi.org/)
    - pygame
    - os (usually part of Python 3.x installations)
    - math (usually part of Python 3.x installations)
    - sys (usually part of Python 3.x installations)
    - pytmx (https://pypi.org/project/PyTMX/)
- Once the dependencies are installed, you can run the game by:


Note: Project has been build by someone else. I have added a few additonal features.
