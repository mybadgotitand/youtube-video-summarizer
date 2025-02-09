import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from transformers import pipeline
import re
import requests
from moviepy.editor import VideoFileClip
import tempfile
import os
from pydub import AudioSegment
import speech_recognition as sr

# Function to summarize text
def summarize_text(text, max_length=5000):
    summarization_pipeline = pipeline("summarization")
    summary = summarization_pipeline(text, max_length=max_length, min_length=50, do_sample=False)
    return summary[0]['summary_text']

# Function to extract YouTube video ID from URL
def extract_video_id(url):
    video_id = None
    patterns = [
        r'v=([^&]+)',  # Pattern for URLs with 'v=' parameter
        r'youtu.be/([^?]+)',  # Pattern for shortened URLs
        r'youtube.com/embed/([^?]+)'  # Pattern for embed URLs
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    return video_id

# Function to download the video audio
def download_video_audio(video_url):
    # This function will download the audio of the video from YouTube using an external tool or API
    # You can use `yt-dlp` or similar tools to download the video/audio
    # Placeholder logic for the sake of example
    pass

# Function to transcribe audio to text using speech recognition
def transcribe_audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    audio = sr.AudioFile(audio_file)
    with audio as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Audio could not be understood."
    except sr.RequestError:
        return "Could not request results from the speech recognition service."

# Main Streamlit app
def main():
    st.title("YouTube Video Summarizer")

    # User input for YouTube video URL
    video_url = st.text_input("Enter YouTube Video URL:", "")

    # User customization options
    max_summary_length = st.slider("Max Summary Length:", 1000, 20000, 5000)

    if st.button("Summarize"):
        try:
            # Extract video ID from URL
            video_id = extract_video_id(video_url)
            if not video_id:
                st.error("Invalid YouTube URL. Please enter a valid URL.")
                return

            # Try to get transcript of the video
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                video_text = ' '.join([line['text'] for line in transcript])
                st.write("Transcript found!")
            except (TranscriptsDisabled, NoTranscriptFound):
                st.write("Transcript not available, attempting to summarize from audio or metadata.")
                
                # Download audio and transcribe it if no transcript is available
                # You can implement an actual video-to-audio downloader here
                # e.g., `download_video_audio(video_url)`
                
                audio_text = "This is where the transcribed text from audio would go."
                # Perform transcription (replace with actual transcription logic)
                # audio_text = transcribe_audio_to_text('path_to_audio_file.wav')

                if audio_text == "This is where the transcribed text from audio would go.":
                    # If no transcription was performed, try to use metadata
                    video_metadata = "Video metadata summary based on title and description."  # Placeholder
                    video_text = video_metadata

            # Summarize the transcript or audio text
            summary = summarize_text(video_text, max_length=max_summary_length)

            # Display summarized text
            st.subheader("Video Summary:")
            st.write(summary)

        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
