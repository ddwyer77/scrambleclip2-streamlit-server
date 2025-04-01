#!/usr/bin/env python3

# This is a fixed script to correct all imports in the generator.py file

fixed_content = """import os, random
import warnings
import hashlib
import numpy as np
from collections import defaultdict
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ColorClip
# Import specific effects
from moviepy.video.fx.loop import loop
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
import traceback
import threading
"""

with open('src/generator.py', 'w') as f:
    f.write(fixed_content)

print("Fixed imports in generator.py")

# Now let's verify the content
with open('src/generator.py', 'r') as f:
    content = f.read()
    print("\nVerification:")
    print(content)
