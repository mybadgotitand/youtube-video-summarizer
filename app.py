import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from transformers import pipeline
import re
import yt_dlp
import os
import speech_recognition as sr
from pydub import AudioSegment
import tempfile

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

# Function to download audio from YouTube video using yt-dlp
def download_audio(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',  # Download the best audio format
        'outtmpl': 'downloaded_audio.%(ext)s',  # Output template for the downloaded audio
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        audio_file = ydl.prepare_filename(info_dict)
        audio_file = os.path.splitext(audio_file)[0] + '.mp3'  # Use .mp3 format instead of .wav
        return audio_file

# Function to convert audio to WAV using pydub (if required)
def convert_to_wav(audio_file):
    try:
        sound = AudioSegment.from_mp3(audio_file)  # If the file is mp3
        wav_file = audio_file.replace('.mp3', '.wav')  # Change the extension to .wav
        sound.export(wav_file, format="wav")
        return wav_file
    except Exception as e:
        return None

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
                try:
                    audio_file = download_audio(video_url)
                    st.write(f"Audio downloaded: {audio_file}")

                    # Convert to .wav if necessary
                    wav_file = convert_to_wav(audio_file)
                    if wav_file:
                        st.write(f"Audio converted to WAV: {wav_file}")
                        # Perform transcription
                        audio_text = transcribe_audio_to_text(wav_file)
                        if audio_text:
                            video_text = audio_text
                        else:
                            st.error("Failed to transcribe audio.")
                    
                        # Clean up downloaded audio file
                        os.remove(wav_file)
                    else:
                        st.error("Failed to convert audio to WAV.")
                    
                    # Clean up downloaded .mp3 file
                    os.remove(audio_file)
                except Exception as e:
                    st.error(f"Error during audio download or transcription: {str(e)}")
                    return

            # Summarize the transcript or audio text
            summary = summarize_text(video_text, max_length=max_summary_length)

            # Display summarized text
            st.subheader("Video Summary:")
            st.write(summary)

        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
