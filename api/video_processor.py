import cv2
import os
from pathlib import Path
from tqdm import tqdm

def create_clips(filename, title, output_folder='static/output'):
    # Set up paths and folders
    input_path = os.path.join('static/uploads', filename)
    video_basename = Path(filename).stem
    output_path = os.path.join(output_folder, video_basename)
    os.makedirs(output_path, exist_ok=True)
    
    # Load the video
    cap = cv2.VideoCapture(input_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Define reel size (Instagram Reels are 1080 x 1920)
    reel_width, reel_height = 1080, 1920
    
    # Clip duration and frame count
    clip_duration_sec = 50
    clip_frame_count = clip_duration_sec * fps

    # Progress tracking
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_clips = (total_frames // clip_frame_count) + (1 if total_frames % clip_frame_count else 0)
    
    clip_index = 0
    clip_names = []
    progress_bar = tqdm(total=total_clips, desc="Creating Clips")

    try:
        # Processing each clip
        while True:
            # Initialize video writer for each clip
            clip_filename = f"part{clip_index + 1}.mp4"
            clip_output_path = os.path.join(output_path, clip_filename)
            clip_names.append(clip_filename)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(clip_output_path, fourcc, fps, (reel_width, reel_height))
            
            # Write frames into the current clip
            for frame_num in range(clip_frame_count):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize frame to fit within the reel canvas
                x_offset = (reel_width - frame_width) // 2
                y_offset = (reel_height - frame_height) // 2
                canvas = cv2.resize(frame, (frame_width, frame_height))
                reel_canvas = cv2.copyMakeBorder(
                    canvas, y_offset, y_offset, x_offset, x_offset, cv2.BORDER_CONSTANT, value=(0, 0, 0)
                )

                # Add title and part number overlays
                part_text = f"Part {clip_index + 1}"
                cv2.putText(reel_canvas, title, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
                cv2.putText(reel_canvas, part_text, (50, reel_height - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Write the frame to the clip video
                out.write(reel_canvas)
            
            # Release the writer and update progress
            out.release()
            clip_index += 1
            progress_bar.update(1)
            
            # Check if we have reached the end of the video
            if not ret:
                break

    finally:
        # Ensure progress bar closes properly
        progress_bar.close()

    cap.release()
    print(f"All clips created successfully in {output_path}")
    print("Clip names:", clip_names)
