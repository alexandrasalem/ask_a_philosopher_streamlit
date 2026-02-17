import requests
import streamlit as st
import json
import hmac
import os
#from rp_handler_ask_a_phil import handler
#from google.cloud import texttospeech
#from google.oauth2 import service_account



# @st.cache_resource
# def get_tts_client():
#     credentials = service_account.Credentials.from_service_account_info(
#         st.secrets["gcp_service_account"]
#     )
#     return texttospeech.TextToSpeechClient(credentials=credentials)
#
# client = get_tts_client()
#
# def generate_tts(text):
#     synthesis_input = texttospeech.SynthesisInput(text=text)
#
#     voice = texttospeech.VoiceSelectionParams(
#         language_code="en-US",
#         name="en-US-Neural2-J"
#     )
#
#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.MP3
#     )
#
#     response = client.synthesize_speech(
#         input=synthesis_input,
#         voice=voice,
#         audio_config=audio_config
#     )
#
#     return response.audio_content

def on_sidebar_change():
    config = (
        st.session_state.phil,
        st.session_state.mode
    )

    # prevent duplicate triggers
    if st.session_state.last_config == config:
        return

    st.session_state.last_config = config

    # st.session_state.messages.append({
    #     "role": "assistant",
    #     "content": (
    #         f"Switched to **{st.session_state.mode}** mode "
    #         f"for **{st.session_state.phil}** philosopher."
    #     ),
    # })

    st.session_state.messages.append({
        "role": "assistant",
        "content": f"I am the philosopher {st.session_state.phil}. Please submit your question below.",
        "avatar": f"{st.session_state.phil}.jpg"
    })


def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("Demo Login")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):
        if hmac.compare_digest(
            password,
            os.environ.get("APP_PASSWORD")#st.secrets["APP_PASSWORD"]
        ):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    return False

if not check_password():
    st.stop()

MAX_MESSAGES = 30

st.session_state.setdefault("messages", [])
st.session_state.setdefault("last_config", None)

if len(st.session_state.messages) >= MAX_MESSAGES:
    st.warning("Demo limit reached. Please refresh later.")
    st.stop()

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {os.environ.get("RUNPOD_API_KEY")}'
}

st.title("Ask a Philosopher")
st.caption("An LLM-powered chatbot to ask an AI-philosopher questions")

with st.sidebar:
    phil = st.selectbox(
        "Which philosopher would you like to chat with?",
        options = ("Aristotle", "Confucius"),
        key = "phil",
        on_change = on_sidebar_change
    )
    mode = st.selectbox(
        "Which LLM-mode do you want to use?",
        options = ("Retriever-Augmented Generation", "LLM-only"),
        key = "mode",
        on_change = on_sidebar_change
    )
if st.session_state["messages"] == []:
    st.session_state["messages"].append({"role": "assistant",
                                         "content": f"I am the philosopher {phil}. Please submit your question below.",
                                         "avatar": f"{phil}.jpg"})


# Display existing chat messages
for message in st.session_state.messages:
    avatar = None

    if message["role"] == "assistant":
        avatar = f"{message['avatar']}"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

    # with st.chat_message(message["role"], avatar=avatar):
    #     col1, col2 = st.columns([7, 2])
    #     with col1:
    #         st.markdown(message["content"])
    #     with col2:
    #         st.session_state[f"audio_0"] = generate_tts(message["content"])
    #         st.audio(st.session_state[f"audio_0"], format="audio/mp3")



# Handling user input through chat
if question := st.chat_input():
    # Preparing payload for the API request based on user input and sidebar configurations
    data = {
        'input': {"question":question, "philosopher":phil, "mode":mode},
        'stream': True
    }
    # Update session state with user message
    st.session_state.messages.append({"role": "user", "content": question, "avatar": None})
    # Display user message in chat
    st.chat_message("user").write(question)
    # Send API request and process the streaming response
    #response = handler(data)
    response = requests.post('https://api.runpod.ai/v2/38z94rrm7q5n9c/runsync', stream=True, json=data, headers=headers)
    #msg, sim = response['output']
    for line in response.iter_lines():
        # Filter out keep-alive newlines
        if line:
            decoded_line = line.decode('utf-8')

    # Extract the assistant's response from the API response and update session state
    msg = json.loads(decoded_line)['output'][0]
    #msg = f"{msg} {str(json.loads(decoded_line)['output'][1])}"
    st.session_state.messages.append({"role": "assistant", "content": msg, "avatar": f"{phil}.jpg"})
    # Display the assistant's response in chat

    with st.chat_message("assistant", avatar=f"{phil}.jpg"):
        st.markdown(msg)
        # col1, col2 = st.columns([7, 2])
        # with col1:
        #     st.markdown(msg)
        # with col2:
        #     st.session_state[f"audio_0"] = generate_tts(msg)
        #     st.audio(st.session_state[f"audio_0"], format="audio/mp3")



