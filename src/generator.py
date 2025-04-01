import os, random
import warnings
import hashlib
import numpy as np
from collections import defaultdict
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ColorClip
# Import specific effects
from moviepy.video.fx.loop import loop
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.video.fx.colorx import colorx
from moviepy.video.fx.crop import crop
from moviepy.video.fx.mirror_x import mirror_x
from moviepy.video.fx.mirror_y import mirror_y
from moviepy.video.fx.time_symmetrize import time_symmetrize
from moviepy.video.fx.invert_colors import invert_colors
from moviepy.video.fx.blackwhite import blackwhite

from .utils import get_video_files, get_random_clip, pad_clip_to_ratio, prepare_clip_for_concat
from .video_analysis import VideoContentAnalyzer

# Suppress MoviePy warnings that might confuse users
warnings.filterwarnings("ignore", category=UserWarning)

class VideoGenerator:
    def __init__(self, input_video_path):
        """
        Initialize the VideoGenerator with an input video path.
        
        Args:
            input_video_path (str): Path to the input video file
        """
        self.input_video_path = input_video_path
        self.video_analyzer = VideoContentAnalyzer()
        
    def generate_scrambled_videos(self, num_videos=5, segment_duration=0.5, output_dir="outputs", 
                                 additional_videos=None, audio_path=None, text_overlay=None):
        """
        Generate multiple unique scrambled versions of the input video(s).
        
        Parameters:
            num_videos (int): Number of videos to generate
            segment_duration (float): Duration of each segment in seconds
            output_dir (str): Directory to save output videos
            additional_videos (list): List of additional video paths to use
            audio_path (str): Path to audio file to add to videos
            text_overlay (dict): Dictionary containing text overlay parameters:
                - text: The text to display
                - color: Text color in hex format
                - stroke_color: Stroke color in hex format
                - font_size: Size of the text
                - stroke_width: Width of the stroke
                - opacity: Text opacity (0-1)
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Combine input video paths
        video_paths = [self.input_video_path]
        if additional_videos:
            video_paths.extend(additional_videos)
            
        # Generate the videos
        output_paths = generate_batch(
            video_paths,
            audio_files=[audio_path] if audio_path else None,
            num_videos=num_videos,
            min_clips=10,
            max_clips=30,
            min_clip_duration=1.5,
            max_clip_duration=3.5,
            output_dir=output_dir,
            use_effects=True,
            use_text=bool(text_overlay),
            custom_text=text_overlay['text'] if text_overlay and 'text' in text_overlay else None,
            text_color=text_overlay['color'] if text_overlay and 'color' in text_overlay else '#FFFFFF',
            stroke_color=text_overlay['stroke_color'] if text_overlay and 'stroke_color' in text_overlay else '#000000',
            font_size=text_overlay['font_size'] if text_overlay and 'font_size' in text_overlay else 60,
            stroke_width=text_overlay['stroke_width'] if text_overlay and 'stroke_width' in text_overlay else 2,
            text_opacity=text_overlay['opacity'] if text_overlay and 'opacity' in text_overlay else 1.00
        )
        
        return output_paths

    def generate_scrambled_video(self, segment_duration, output_dir="outputs", additional_videos=None, audio_path=None):
        """
        Generate a single scrambled version of the input video(s).
        
        Args:
            segment_duration (float): Duration of each segment in seconds
            output_dir (str): Directory to save the output video
            additional_videos (list): List of additional video paths to include in the remix
            audio_path (str): Path to the audio file to use as background music
            
        Returns:
            str: Path to the generated video file
        """
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Generate a unique output filename
        output_filename = f"scrambled_{os.path.basename(self.input_video_path)}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Combine all video paths
        all_videos = [self.input_video_path]
        if additional_videos:
            all_videos.extend(additional_videos)
        
        # Use the existing generate_batch function with all videos
        output_paths = generate_batch(
            input_videos=all_videos,
            num_videos=1,
            min_clip_duration=segment_duration,
            max_clip_duration=segment_duration,
            output_dir=output_dir,
            use_effects=False,  # Disable effects for simplicity
            use_text=False,     # Disable text for simplicity
            progress_callback=None
        )
        
        if output_paths and audio_path:
            # Load the video and audio
            video = VideoFileClip(output_paths[0])
            audio = AudioFileClip(audio_path)
            
            # If audio is longer than video, trim it
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)
            # If audio is shorter than video, loop it
            else:
                audio = audio.loop(duration=video.duration)
            
            # Set the audio of the video
            video = video.set_audio(audio)
            
            # Write the final video with the new audio
            video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=os.path.join(output_dir, "temp-audio.m4a"),
                remove_temp=True
            )
            
            # Close the clips
            video.close()
            audio.close()
            
            # Remove the original output file
            if os.path.exists(output_paths[0]):
                os.remove(output_paths[0])
        
        return output_path if output_paths else None

# Default paths (can be overridden when called from GUI)
INPUT_VIDEO_PATH = "../assets/input_videos"
INPUT_AUDIO_PATH = "../assets/input_audio/audio.mp3"
OUTPUT_PATH = "../outputs"

# Initialize video analyzer
video_analyzer = VideoContentAnalyzer()

def generate_batch(input_videos, audio_files=None, num_videos=5, min_clips=10, max_clips=30, 
                   min_clip_duration=1.5, max_clip_duration=3.5, output_dir="outputs", 
                   use_effects=False, use_text=False, custom_text=None, text_color='#FFFFFF',
                   stroke_color='#000000', font_size=60, stroke_width=2, text_opacity=1.00, 
                   progress_callback=None):
    """
    Generate a batch of videos by randomly selecting clips from input videos
    and concatenating them.
    
    Parameters:
        input_videos (list): List of paths to input video files
        audio_files (list, optional): List of paths to audio files
        num_videos (int): Number of videos to generate in batch
        min_clips (int): Minimum number of clips per output video
        max_clips (int): Maximum number of clips per output video
        min_clip_duration (float): Minimum duration of each clip in seconds
        max_clip_duration (float): Maximum duration of each clip in seconds
        output_dir (str): Directory to save output videos
        use_effects (bool): Whether to use AI effects and transitions
        use_text (bool): Whether to add text overlay to videos
        custom_text (str): Custom text to use (if None, random captions will be used)
        text_color (str): Color of the text overlay
        stroke_color (str): Color of the text stroke
        font_size (int): Size of the text overlay (default: 60)
        stroke_width (int): Width of the text stroke (default: 2)
        text_opacity (float): Opacity of the text overlay (default: 1.00)
        progress_callback (callable): Function to report progress (progress_pct, status_message)
    
    Returns:
        list: Paths to the generated video files
    """
    # Target duration for output videos (16 seconds)
    TARGET_DURATION = 16.0
    
    if not input_videos:
        raise ValueError("No input videos provided")

    if progress_callback:
        progress_callback(0, f"Loading {len(input_videos)} videos...")
    else:
        print(f"Loading {len(input_videos)} videos...")
    
    # Load all input videos as MoviePy clips
    try:
        input_clips = [VideoFileClip(video_path) for video_path in input_videos]
    except Exception as e:
        # If we fail to load some videos, try to load them one by one to identify which ones work
        input_clips = []
        for video_path in input_videos:
            try:
                clip = VideoFileClip(video_path)
                input_clips.append(clip)
                if progress_callback:
                    progress_callback(5, f"Successfully loaded {os.path.basename(video_path)}")
                else:
                    print(f"Successfully loaded {video_path}")
            except Exception as e:
                if progress_callback:
                    progress_callback(5, f"Failed to load {os.path.basename(video_path)}: {e}")
                else:
                    print(f"Failed to load {video_path}: {e}")
    
    if not input_clips:
        raise ValueError("No valid input videos could be loaded")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create a global history of used clip segments across all videos in batch
    # This tracks which parts of which clips have been used to avoid reuse across the batch
    clip_history = {}  # Maps clip_index to a list of (start_time, end_time) tuples
    
    # Track visual similarity of clips to avoid similar looking clips
    # Create a visual fingerprint for each video to compare similarity
    if len(input_clips) > 1:  # Only calculate if we have multiple clips
        if progress_callback:
            progress_callback(5, "Creating visual signatures for clip diversity...")
        visual_signatures = create_video_signatures(input_clips)
    else:
        visual_signatures = None
        
    output_paths = []
    
    # Set consistent dimensions for output videos
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    
    for i in range(num_videos):
        # Calculate overall progress: each video is worth (90/num_videos)% of progress
        base_progress = 10 + (i * (80 / num_videos))
        
        if progress_callback:
            progress_callback(int(base_progress), f"Building video {i+1}/{num_videos}...")
        else:
            print(f"Building {output_dir}/output_{i+1:02d}.mp4 using MoviePy...")
        
        # Generate unique output filename for this video
        output_filename = f"output_{i+1:02d}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        # Calculate clip parameters based on target duration
        # For 16 second videos, adjust number and duration of clips
        # Aim for ~10-12 clips with 1.5-2 seconds each to fit in 16 seconds
        min_clip_count = 8  # Reduced to fit target duration
        max_clip_count = 15
        num_clips = random.randint(min_clip_count, max_clip_count)
        
        # Calculate average clip duration to fit target duration
        avg_clip_duration = TARGET_DURATION / num_clips
        # Add some variation around the average
        min_clip_dur = max(0.5, avg_clip_duration * 0.7)  # Min 0.5 seconds
        max_clip_dur = avg_clip_duration * 1.3  # Max 1.3x the average
        
        # Randomly select clips and durations
        selected_clips = []
        total_duration = 0
        
        # Track the already used clips for this video to avoid repetition
        # Keep last N clips to avoid repetition of similar clips
        used_clips_memory = []
        memory_size = min(5, len(input_clips) // 2)  # Remember last 5 clips or half of available clips
        
        # Initialize local clip history for this video
        local_clip_history = defaultdict(list)
        
        for j in range(num_clips):
            # Progress update for clip selection
            clip_progress = base_progress + ((j / num_clips) * (20 / num_videos))
            if progress_callback:
                progress_callback(int(clip_progress), f"Selecting clip {j+1}/{num_clips} for video {i+1}/{num_videos}")
            
            # Get available clip indices, avoiding recently used clips
            available_clip_indices = list(range(len(input_clips)))
            
            # Remove recently used clips from consideration
            for used_idx in used_clips_memory:
                if used_idx in available_clip_indices and len(available_clip_indices) > 1:
                    available_clip_indices.remove(used_idx)
            
            # If we have visual signatures, try to select dissimilar clips
            if visual_signatures and len(available_clip_indices) > 1:
                # If we have at least one selected clip already, try to find a dissimilar one
                if selected_clips:
                    clip_index = select_dissimilar_clip(
                        available_clip_indices, 
                        used_clips_memory, 
                        visual_signatures
                    )
                else:
                    # For the first clip, just choose randomly
                    clip_index = random.choice(available_clip_indices)
            else:
                # If no visual signatures or only one clip available, choose randomly
                clip_index = random.choice(available_clip_indices)
                
            input_clip = input_clips[clip_index]
            
            # Add to used clips memory
            used_clips_memory.append(clip_index)
            if len(used_clips_memory) > memory_size:
                used_clips_memory.pop(0)  # Remove oldest
            
            # Calculate remaining duration needed to hit the target
            remaining_clips = num_clips - j
            remaining_duration = max(0, TARGET_DURATION - total_duration)
            
            # Adjust duration for this clip
            if remaining_clips > 1:
                # Leave some duration for remaining clips
                max_this_clip = min(max_clip_dur, remaining_duration / remaining_clips * 1.5)
                clip_duration = random.uniform(min_clip_dur, max_this_clip)
            else:
                # Last clip - use remaining duration
                clip_duration = min(max_clip_dur, remaining_duration)
                clip_duration = max(min_clip_dur, clip_duration)  # Ensure minimum duration
            
            # Determine a random start time for the clip that avoids previously used segments
            max_start = max(0, input_clip.duration - clip_duration)
            if max_start <= 0:
                continue  # Skip if the clip is too short
            
            # Find available segments that haven't been used yet (globally or locally)
            available_segments = find_available_segments(
                clip_index, clip_duration, input_clip.duration,
                global_history=clip_history.get(clip_index, []),
                local_history=local_clip_history.get(clip_index, [])
            )
            
            # If no available segments, try another clip
            if not available_segments:
                # Try again with a different clip
                j -= 1  # Repeat this iteration
                continue
                
            # Choose a random segment from available ones
            segment_start, segment_end = random.choice(available_segments)
            start_time = random.uniform(segment_start, segment_end - clip_duration)
            
            # Record this usage in both global and local history
            used_segment = (start_time, start_time + clip_duration)
            if clip_index not in clip_history:
                clip_history[clip_index] = []
            clip_history[clip_index].append(used_segment)
            
            if clip_index not in local_clip_history:
                local_clip_history[clip_index] = []
            local_clip_history[clip_index].append(used_segment)
            
            # Extract the subclip
            try:
                subclip = input_clip.subclip(start_time, start_time + clip_duration)
                
                # Ensure consistent dimensions and padding for all clips
                processed_clip = ensure_consistent_dimensions(subclip)
                
                # Apply AI-powered effects if enabled (but with reduced probability)
                if use_effects and random.random() < 0.3:  # Only 30% chance of effects
                    try:
                        processed_clip = apply_smart_effects(processed_clip, intensity=0.3)
                    except Exception as e:
                        print(f"Error applying effects to clip: {e}")
                
                selected_clips.append(processed_clip)
                total_duration += clip_duration
                
            except Exception as e:
                print(f"Error processing clip: {e}")
                continue
            
            # If we've reached the target duration, stop adding clips
            if total_duration >= TARGET_DURATION:
                break
        
        if not selected_clips:
            if progress_callback:
                progress_callback(int(base_progress), f"Warning: No valid clips could be extracted for video {i+1}")
            else:
                print(f"Warning: No valid clips could be extracted for {output_path}")
            continue
        
        final_clip = None

        try:
            # Progress update for effect stage
            effect_progress = base_progress + (60 / num_videos)
            if progress_callback:
                progress_callback(int(effect_progress), f"Applying effects and transitions for video {i+1}/{num_videos}")
            
            # If we're using effects, add simple transitions between clips
            if use_effects:
                final_clips = []
                
                # Process each clip
                for idx, clip in enumerate(selected_clips):
                    if idx == 0:
                        # First clip gets a fade in
                        clip = clip.fadein(0.3)
                    elif idx == len(selected_clips) - 1:
                        # Last clip gets a fade out
                        clip = clip.fadeout(0.3)
                    
                    final_clips.append(clip)
                
                # Simple concatenation with crossfades
                final_clip = concatenate_videoclips(final_clips, method="compose")
            else:
                # Simple concatenation without transitions
                final_clip = concatenate_videoclips(selected_clips)
            
            # Check final clip dimensions and ensure they're correct
            final_clip = ensure_consistent_dimensions(final_clip)
            
            # Check if the final clip is too long and trim if necessary
            if final_clip.duration > TARGET_DURATION + 1:  # Allow 1 second buffer
                if progress_callback:
                    progress_callback(int(effect_progress), f"Trimming video to target duration ({TARGET_DURATION}s)")
                final_clip = final_clip.subclip(0, TARGET_DURATION)
            
            # Add text overlay if enabled
            if use_text:
                text_progress = base_progress + (65 / num_videos)
                if progress_callback:
                    progress_callback(int(text_progress), f"Adding text overlay to video {i+1}/{num_videos}")
                
                try:
                    # Use custom text if provided, otherwise generate a random caption
                    if custom_text:
                        caption = custom_text
                    else:
                        # Generate a random caption
                        captions = [
                            "WATCH TILL THE END 😱",
                            "POV: When the beat drops 🔥",
                            "This is INSANE 🤯",
                            "Wait for it... 👀",
                            "Best moments 💯",
                            "Try not to be amazed 😮",
                            "Crazy skills 💪",
                            "Ultimate compilation 🏆",
                            "The perfect edit doesn't exi- 😲",
                            "Caught in 4K 📸",
                            "Vibe check ✅",
                            f"Part {i+1} 🎬"
                        ]
                        caption = random.choice(captions)
                    
                    print(f"Creating text overlay with text: '{caption}', color: {text_color}, size: {font_size}, opacity: {text_opacity}")
                    
                    # Create text overlay with custom parameters
                    txt_clip = create_text_overlay(
                        caption,
                        (int(final_clip.w), int(final_clip.h)),  # Ensure dimensions are integers
                        color=text_color,
                        font_size=font_size,
                        opacity=text_opacity,
                        stroke_color=stroke_color,
                        stroke_width=stroke_width
                    )
                    
                    # Add text to the video if creation was successful
                    if txt_clip is not None:
                        # Ensure the text duration matches the video
                        txt_clip = txt_clip.set_duration(final_clip.duration)
                        
                        # Composite the text on top of the video
                        final_clip = CompositeVideoClip([final_clip, txt_clip])
                        
                        if progress_callback:
                            progress_callback(int(text_progress), f"Added text overlay: '{caption}'")
                        else:
                            print(f"Successfully added text overlay: '{caption}'")
                    else:
                        if progress_callback:
                            progress_callback(int(text_progress), f"Warning: Text overlay creation failed")
                        else:
                            print(f"Warning: Text overlay creation failed")
                except Exception as e:
                    if progress_callback:
                        progress_callback(int(text_progress), f"Error adding text: {e}")
                    else:
                        print(f"Error adding text overlay: {e}")
                        import traceback
                        traceback.print_exc()
            
            # Progress update for audio stage
            audio_progress = base_progress + (70 / num_videos)
            if progress_callback:
                progress_callback(int(audio_progress), f"Adding audio to video {i+1}/{num_videos}")
                
            # Select or generate audio
            if audio_files and len(audio_files) > 0:
                audio_path = random.choice(audio_files)
                try:
                    audio = AudioFileClip(audio_path)
                    
                    # Ensure audio is exactly as long as the video
                    target_duration = final_clip.duration
                    if audio.duration < target_duration:
                        # Loop the audio to match video duration exactly
                        audio = loop(audio, duration=target_duration)
                    else:
                        # Trim audio to match video duration exactly
                        audio = audio.subclip(0, target_duration)
                        
                    final_clip = final_clip.set_audio(audio)
                    if progress_callback:
                        progress_callback(int(audio_progress), f"Added audio to video {i+1}/{num_videos}")
                    else:
                        print(f"Added audio from {audio_path}")
                except Exception as e:
                    if progress_callback:
                        progress_callback(int(audio_progress), f"Error adding audio: {e}")
                    else:
                        print(f"Error adding audio from {audio_path}: {e}")
            
            # Progress update for rendering stage
            render_progress = base_progress + (75 / num_videos)
            if progress_callback:
                progress_callback(int(render_progress), f"Rendering video {i+1}/{num_videos}...")
            else:
                print(f"Writing audio for {output_path}...")
            
            # Ensure final clip has exact 9:16 dimensions before writing
            if final_clip.w != TARGET_WIDTH or final_clip.h != TARGET_HEIGHT:
                final_clip = final_clip.resize(width=TARGET_WIDTH, height=TARGET_HEIGHT)
            
            # Write the final video
            try:
                # Create a callback for write_videofile progress
                def writing_callback(t):
                    if progress_callback:
                        # Map t from 0-duration to render_progress-(render_progress+20)
                        write_pct = min(100, int(render_progress + (t / final_clip.duration) * (20 / num_videos)))
                        progress_callback(write_pct, f"Rendering video {i+1}/{num_videos}: {int((t / final_clip.duration) * 100)}%")
                
                # First try without callback which might not be supported in some MoviePy versions
                try:
                    final_clip.write_videofile(
                        output_path,
                        codec="libx264",
                        audio_codec="aac",
                        preset="fast",
                        threads=4,
                        logger=None
                    )
                except TypeError as e:
                    # If first attempt fails with TypeError, it might be an old MoviePy version
                    if "unexpected keyword argument" in str(e):
                        final_clip.write_videofile(
                            output_path,
                            codec="libx264",
                            audio_codec="aac",
                            preset="fast",
                            threads=4
                        )
                    else:
                        raise
                
                if progress_callback:
                    progress_callback(int(base_progress + (90 / num_videos)), f"Video {i+1}/{num_videos} complete!")
                else:
                    print(f"Video {output_path} is ready!")
                
                # Add the output path to our list
                if os.path.exists(output_path):
                    output_paths.append(output_path)
                else:
                    print(f"Warning: Output file was not created: {output_path}")
                    
            except Exception as e:
                if progress_callback:
                    progress_callback(int(render_progress), f"Error writing video file: {e}. Trying simplifier method...")
                else:
                    print(f"Error writing video file {output_path}: {e}")
                try:
                    # Try a simpler approach if the first attempt fails
                    if progress_callback:
                        progress_callback(int(render_progress), f"Using simplified render settings...")
                    else:
                        print("Trying with simpler options...")
                    final_clip.write_videofile(output_path)
                    if os.path.exists(output_path):
                        output_paths.append(output_path)
                    else:
                        print(f"Warning: Output file was not created: {output_path}")
                except Exception as e2:
                    if progress_callback:
                        progress_callback(int(render_progress), f"Failed again: {e2}")
                    else:
                        print(f"Failed again: {e2}")
                    
        except Exception as e:
            if progress_callback:
                progress_callback(int(base_progress), f"Error creating final clip: {e}")
            else:
                print(f"Error creating final clip: {e}")
                import traceback
                traceback.print_exc()
        
        # Clean up memory
        if final_clip:
            final_clip.close()
        
        for clip in selected_clips:
            clip.close()
    
    # Clean up
    for clip in input_clips:
        clip.close()
    
    # Final progress update
    if progress_callback:
        progress_callback(100, f"All {len(output_paths)} videos complete!")
    
    return output_paths

def apply_smart_effects(clip, intensity=0.3):
    """
    Apply minimal effects to avoid freezing issues.
    """
    # Only attempt one simple effect
    effect_choice = random.random()
    
    try:
        if effect_choice < 0.4:  # 40% chance of slight color boost
            return colorx(clip, 1.0 + (intensity * 0.2))
        elif effect_choice < 0.6:  # 20% chance of slight fade
            return clip.crossfadein(0.3)
        else:  # 40% chance of no effect
            return clip
    except Exception as e:
        print(f"Effect failed, returning original clip: {e}")
        return clip

def create_text_overlay(text, size, color='white', font_size=60, opacity=1.00, stroke_color='black', stroke_width=2):
    """Create a text overlay with stroke effect."""
    try:
        print(f"Creating text overlay with text: '{text}', color: {color}, size: {font_size}, opacity: {opacity}, stroke: {stroke_color} ({stroke_width}px)")
        
        # Ensure size is a tuple of integers
        if isinstance(size, tuple):
            width, height = map(int, size)
        else:
            width, height = map(int, (size.w, size.h))
        
        # Create the main text clip
        text_clip = TextClip(
            text,
            fontsize=font_size,
            color=color,
            font='Arial',  # Use a basic font that's guaranteed to exist
            size=(width, None),  # Width fixed, height auto
            method='caption',
            align='center',
            stroke_color=stroke_color,
            stroke_width=stroke_width
        )
        
        # Set duration (will be adjusted later)
        text_clip = text_clip.set_duration(10)
        
        # Set opacity
        text_clip = text_clip.set_opacity(opacity)
        
        # Position in center
        text_clip = text_clip.set_position(('center', 'center'))
        
        return text_clip
        
    except Exception as e:
        print(f"Error in create_text_overlay: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        return None  # Return None instead of raising to allow graceful fallback

# Add a function to preserve original dimensions 
def preserve_original_dimensions(original_clip, processed_clip):
    """
    Ensure a processed clip maintains the same dimensions and aspect ratio
    as the original clip. This prevents unwanted padding from being added.
    
    Args:
        original_clip: The original video clip with correct dimensions
        processed_clip: The processed clip that might have different dimensions
        
    Returns:
        A clip with the same content as processed_clip but dimensions of original_clip
    """
    # Get original dimensions
    orig_w, orig_h = original_clip.size
    
    # If dimensions already match, return the processed clip
    if processed_clip.w == orig_w and processed_clip.h == orig_h:
        return processed_clip
    
    # Resize the processed clip to match original dimensions exactly
    # without allowing any automatic padding
    return processed_clip.resize(width=orig_w, height=orig_h)

# Update ensure_consistent_dimensions to properly handle 9:16 videos
def ensure_consistent_dimensions(clip, target_ratio=(9, 16)):
    """
    Ensure consistent dimensions for all clips, properly handling vertical videos.
    For 9:16 videos, ensure they fill the screen with no black bars.
    For other ratios, add minimal black bars as needed.
    """
    if clip is None:
        raise ValueError("Clip cannot be None")
        
    # Set fixed target dimensions for 9:16 videos (e.g., 1080x1920)
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    
    # Get current dimensions
    w, h = clip.size
    
    # For vertical videos (taller than wide)
    if h > w:  # This is a vertical video
        # Resize to fixed 9:16 dimensions (1080x1920)
        # First scale by height to ensure we fill vertically
        scale_factor = TARGET_HEIGHT / h
        new_width = int(w * scale_factor)
        
        if new_width < TARGET_WIDTH:
            # If scaled width is less than target width, scale by width instead
            # This ensures we fill the full width with no black bars on sides
            return clip.resize(width=TARGET_WIDTH)
        else:
            # If wider than target, crop the sides to fit exactly 9:16
            resized = clip.resize(height=TARGET_HEIGHT)
            # Center crop to target width
            x_center = resized.w // 2
            x1 = max(0, x_center - TARGET_WIDTH // 2)
            x2 = min(resized.w, x_center + TARGET_WIDTH // 2)
            return crop(resized, x1=x1, y1=0, x2=x2, y2=TARGET_HEIGHT)
    
    # For horizontal videos (wider than tall)
    else:
        # Scale by width to ensure we fill horizontally
        scale_factor = TARGET_WIDTH / w
        new_height = int(h * scale_factor)
        
        # Resize first
        resized = clip.resize(width=TARGET_WIDTH)
        
        # Add black bars to top and bottom to make it exactly 9:16
        padding_y = (TARGET_HEIGHT - new_height) // 2
        return resized.margin(top=padding_y, bottom=padding_y, color=(0, 0, 0))

# Helper function to select a clip that is visually dissimilar to recently used clips
def select_dissimilar_clip(available_indices, recently_used, visual_signatures, top_n=3):
    """
    Select a clip that is visually dissimilar to recently used clips.
    
    Args:
        available_indices: List of available clip indices to choose from
        recently_used: List of recently used clip indices
        visual_signatures: Dictionary of clip signatures for comparison
        top_n: Number of candidates to consider
        
    Returns:
        Index of selected clip
    """
    # If no recently used clips or no signatures, choose randomly
    if not recently_used or not visual_signatures:
        return random.choice(available_indices)
    
    # Select a few random candidates
    candidates = random.sample(
        available_indices, 
        min(top_n, len(available_indices))
    )
    
    # Calculate average dissimilarity score for each candidate
    scores = []
    for candidate in candidates:
        # Skip if candidate doesn't have a signature
        if candidate not in visual_signatures:
            scores.append(0)
            continue
            
        # Calculate average dissimilarity to recently used clips
        dissimilarity = 0
        count = 0
        for used in recently_used:
            if used in visual_signatures:
                # Higher score means more dissimilar
                dissimilarity += 1.0 - calculate_similarity(
                    visual_signatures[candidate],
                    visual_signatures[used]
                )
                count += 1
        
        # Average dissimilarity (higher is better)
        avg_dissimilarity = dissimilarity / count if count > 0 else 0
        scores.append(avg_dissimilarity)
    
    # Select the most dissimilar candidate
    if scores:
        # Return the candidate with highest dissimilarity score
        return candidates[scores.index(max(scores))]
    
    # Fallback to random selection
    return random.choice(available_indices)

# Calculate similarity between two visual signatures
def calculate_similarity(sig1, sig2):
    """
    Calculate similarity between two visual signatures.
    Returns a value between 0 and 1, where 1 is identical.
    """
    # Simple implementation: use cosine similarity
    # Convert to numpy arrays if they aren't already
    sig1 = np.array(sig1)
    sig2 = np.array(sig2)
    
    # Calculate cosine similarity
    dot_product = np.dot(sig1, sig2)
    norm1 = np.linalg.norm(sig1)
    norm2 = np.linalg.norm(sig2)
    
    # Avoid division by zero
    if norm1 == 0 or norm2 == 0:
        return 0
        
    return dot_product / (norm1 * norm2)

# Create simple visual signatures for videos
def create_video_signatures(clips, samples=5):
    """
    Create simple visual signatures for a list of video clips.
    This is a simplified approach - in production, you'd use more sophisticated
    visual feature extraction.
    
    Args:
        clips: List of MoviePy VideoFileClip objects
        samples: Number of frames to sample from each clip
        
    Returns:
        Dictionary mapping clip index to signature
    """
    signatures = {}
    
    for i, clip in enumerate(clips):
        try:
            # Sample frames evenly throughout the clip
            duration = clip.duration
            if duration <= 0:
                continue
                
            frame_times = np.linspace(0, duration * 0.9, samples)
            
            # Extract color features from each frame
            signature = []
            for t in frame_times:
                try:
                    # Get frame at this time
                    frame = clip.get_frame(t)
                    
                    # Simple color histogram as signature
                    # Average color values in each channel
                    r_avg = np.mean(frame[:, :, 0])
                    g_avg = np.mean(frame[:, :, 1])
                    b_avg = np.mean(frame[:, :, 2])
                    
                    # Calculate dominant brightness
                    brightness = (r_avg + g_avg + b_avg) / 3
                    
                    # Add to signature
                    signature.extend([r_avg, g_avg, b_avg, brightness])
                    
                except Exception:
                    # If we can't get a frame, add zeros
                    signature.extend([0, 0, 0, 0])
            
            # Store normalized signature
            signatures[i] = signature
            
        except Exception:
            # If we can't process a clip, skip it
            continue
    
    return signatures

# Find available segments in a clip that haven't been used yet
def find_available_segments(clip_index, desired_duration, clip_duration, 
                           global_history=None, local_history=None, 
                           min_segment_size=0.5, buffer=0.1):
    """
    Find available segments in a clip that haven't been used yet.
    
    Args:
        clip_index: Index of the clip
        desired_duration: Desired duration of the segment
        clip_duration: Total duration of the clip
        global_history: List of (start, end) tuples of globally used segments
        local_history: List of (start, end) tuples of locally used segments
        min_segment_size: Minimum size of an available segment to consider
        buffer: Buffer around used segments to avoid too-similar clips
        
    Returns:
        List of (start, end) tuples representing available segments
    """
    if global_history is None:
        global_history = []
    if local_history is None:
        local_history = []
    
    # Combine global and local history
    all_used = global_history + local_history
    
    # If no used segments, the entire clip is available
    if not all_used:
        return [(0, clip_duration - desired_duration)]
    
    # Sort used segments by start time
    used_segments = sorted(all_used, key=lambda x: x[0])
    
    # Add buffer around used segments
    buffered_segments = []
    for start, end in used_segments:
        buffered_start = max(0, start - buffer)
        buffered_end = min(clip_duration, end + buffer)
        buffered_segments.append((buffered_start, buffered_end))
    
    # Merge overlapping segments
    merged = []
    for segment in buffered_segments:
        if not merged or segment[0] > merged[-1][1]:
            merged.append(segment)
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], segment[1]))
    
    # Find available segments
    available = []
    
    # Check if there's space before the first used segment
    if merged[0][0] > desired_duration:
        available.append((0, merged[0][0]))
    
    # Check spaces between used segments
    for i in range(len(merged) - 1):
        gap_start = merged[i][1]
        gap_end = merged[i+1][0]
        
        if gap_end - gap_start >= desired_duration + min_segment_size:
            available.append((gap_start, gap_end - desired_duration))
    
    # Check if there's space after the last used segment
    if clip_duration - merged[-1][1] >= desired_duration + min_segment_size:
        available.append((merged[-1][1], clip_duration - desired_duration))
    
    return available

if __name__ == "__main__":
    generate_batch()
