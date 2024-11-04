import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from api.video_processor import create_clips
import subprocess
from pathlib import Path
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip


app = Flask(__name__)
app.secret_key = 'a_secure_and_unique_string_here'

# Configuration for file upload
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = 'static/output'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)


# Progress tracking dictionary
progress = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        # Check if a file has been uploaded
        if 'file' not in request.files:
            flash("No file part in the request", "warning")
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash("No selected file", "warning")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("File uploaded successfully!", "success")
            return redirect(url_for('dashboard'))

    # Get the list of uploaded videos
    videos = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('dashboard.html', videos=videos)

@app.route('/video_preview/<filename>')
def video_preview(filename):
    return render_template('video_preview.html', filename=filename)



# Route to create clips
@app.route('/create_clips/<filename>', methods=['GET', 'POST'])
def create_clips_route(filename):
    if request.method == 'POST':
        title = request.form.get('title', 'Default Title')
        # Reset progress for this filename
        progress[filename] = {'total_clips': 0, 'completed_clips': 0}
        
        # Start the clip creation
        create_clips(filename, title)
        flash("Clips created successfully!", "success")
        return redirect(url_for('dashboard'))
    
    return render_template('create_clips.html', filename=filename)

@app.route('/progress/<filename>')
def progress_status(filename):
    return jsonify(progress.get(filename, {}))

def create_clips(filename, title):
    # Set up paths and folders
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video_basename = Path(filename).stem
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], video_basename)
    os.makedirs(output_path, exist_ok=True)
    
    # Load the video
    original_video = VideoFileClip(input_path)
    total_duration = original_video.duration
    clip_duration_sec = 50

    # Calculate total clips
    total_clips = int(total_duration // clip_duration_sec) + (1 if total_duration % clip_duration_sec > 0 else 0)
    progress[filename] = {'total_clips': total_clips, 'completed_clips': 0}
    clip_index = 0

    while clip_index < total_clips:
        start_time = clip_index * clip_duration_sec
        end_time = min((clip_index + 1) * clip_duration_sec, total_duration)
        
        # Extract subclip
        video_clip = original_video.subclip(start_time, end_time)
        
        # Create title overlay as a TextClip
        title_text = f"{title} - Part {clip_index + 1}"
        title_overlay = TextClip(
            title_text, fontsize=70, color='white', size=(video_clip.w, 80)
        ).set_position(("center", 10)).set_duration(2)  # Position text at the top

        # Composite the video and overlay
        final_clip = CompositeVideoClip([video_clip, title_overlay.set_start(0)])  # Overlay starts from 0

        # Output path for each clip
        clip_filename = f"part{clip_index + 1}.mp4"
        clip_output_path = os.path.join(output_path, clip_filename)
        
        # Write the final clip to a file
        final_clip.write_videofile(clip_output_path, codec="libx264", audio_codec="aac")

        # Update progress
        clip_index += 1
        progress[filename]['completed_clips'] = clip_index

    print("Completed clip output!")

if __name__ == '__main__':
    app.run(debug=True)
