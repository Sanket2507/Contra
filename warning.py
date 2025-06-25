# This is just pseudocode for creating a warning sign image
# You'll need to actually create this image and save it as ./graphics/warning.png

import pygame as pg

def create_warning_sign():
    """
    Creates a warning sign image and saves it to ./graphics/warning.png
    Run this script once to generate the image.
    """
    # Create a new surface for the warning sign
    warning = pg.Surface((200, 180), pg.SRCALPHA)
    
    # Triangle shape
    triangle_points = [(100, 10), (10, 170), (190, 170)]
    
    # Draw yellow triangle with black border
    pg.draw.polygon(warning, (255, 255, 0), triangle_points)
    pg.draw.polygon(warning, (0, 0, 0), triangle_points, 4)
    
    # Draw exclamation mark
    pg.draw.rect(warning, (0, 0, 0), (90, 50, 20, 70))
    pg.draw.circle(warning, (0, 0, 0), (100, 140), 10)
    
    # Save the image
    pg.image.save(warning, "./graphics/warning.png")
    
    print("Warning sign created successfully")

if __name__ == "__main__":
    pg.init()
    create_warning_sign()
    pg.quit()