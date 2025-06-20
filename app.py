import streamlit as st
import requests
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration, SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
import os
import torch
import soundfile as sf
from datasets import load_dataset
import matplotlib.pyplot as plt
import numpy as np
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'


@st.cache_resource
def initialize_image_captioning():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

@st.cache_resource
def initialize_speech_synthesis():
    processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
    model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
    vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
    embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
    speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)
    return processor, model, vocoder, speaker_embeddings

def generate_caption(processor, model, image):
    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs)
    output_caption = processor.decode(out[0], skip_special_tokens=True)
    return output_caption

def generate_speech(processor, model, vocoder, speaker_embeddings, caption):
    inputs = processor(text=caption, return_tensors="pt")
    speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)
    sf.write("speech.wav", speech.numpy(), samplerate=16000)

def play_sound():
    audio_file = open("speech.wav", 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/wav')

def visualize_speech():
    data, samplerate = sf.read("speech.wav")
    duration = len(data) / samplerate

    # Create time axis
    time = np.linspace(0., duration, len(data))

     # Plot the speech waveform
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(time, data)
    ax.set(xlabel="Time (s)", ylabel="Amplitude", title="Speech Waveform")

    # Display the plot using st.pyplot()
    st.pyplot(fig)

def main():
    st.set_page_config(
    page_title="Image description with AI Voice Assistance",
    page_icon="📸",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

    st.sidebar.markdown("---")
    st.sidebar.markdown("## Image Description with AI Voice Assistance")
    
    st.markdown(
        """
        <style>
        .container {
            max-width: 800px;
        }
        .title {
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .description {
            margin-bottom: 30px;
        }
        .instructions {
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Title
    st.markdown("<div class='title'>Image Description with AI voice Assistance</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])

    with col1:
        st.write("")

    

    with col3:
        st.write("")

    # Model Description
    

    # Instructions
    with st.expander("Instructions"):
        st.markdown("1. Upload an image or provide the URL of an image.")
        st.markdown("2. Click the 'Generate Caption and Speech' button.")
        st.markdown("3. The generated caption will be displayed, and the speech will start playing.")


    # Choose image source
    image_source = st.radio("Select Image Source:", ("Upload Image", "Open from URL"))

    image = None

    if image_source == "Upload Image":
        # File uploader for image
        uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
        else:
            image = None

    else:
        # Input box for image URL
        url = st.text_input("Enter the image URL:")
        if url:
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    image = Image.open(response.raw)
                else:
                    st.error("Error loading image from URL.")
                    image = None
            except requests.exceptions.RequestException as e:
                st.error(f"Error loading image from URL: {e}")
                image = None

    # Generate caption and play sound button
    if image is not None:
        # Display the uploaded image
        st.image(image, caption='Uploaded Image', use_column_width=True)

        # Initialize image captioning models
        caption_processor, caption_model = initialize_image_captioning()

        # Initialize speech synthesis models
        speech_processor, speech_model, speech_vocoder, speaker_embeddings = initialize_speech_synthesis()

        # Generate caption
        with st.spinner("Generating Caption..."):
            output_caption = generate_caption(caption_processor, caption_model, image)

        # Display the caption
        st.subheader("Caption:")
        st.write(output_caption)
        
        # Generate speech from the caption
        with st.spinner("Generating Speech..."):
            generate_speech(speech_processor, speech_model, speech_vocoder, speaker_embeddings, output_caption)

        
        st.subheader("Audio:")
        # Play the generated sound
        play_sound()

        # Visualize the speech waveform
        with st.expander("See visualization"):
            visualize_speech()


if __name__ == "__main__":
    main()