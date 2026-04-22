import streamlit as st
import cv2
import numpy as np
import random

# --- STYLING ---
st.set_page_config(page_title="SteganoTech Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    .stTextArea>div>div>textarea { background-color: #ffffff; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)


# --- CORE LOGIC ---
def text_to_bits(text):
    return [int(b) for char in text for b in format(ord(char), '08b')]


def bits_to_text(bits):
    chars = [chr(int("".join(map(str, bits[i:i + 8])), 2)) for i in range(0, len(bits), 8) if len(bits[i:i + 8]) == 8]
    return "".join(chars)


# --- UI HEADER ---
st.title("🔐 SteganoTech Laboratory")
st.subheader("Secure Data Treatment & Image Encryption")
st.divider()

tab1, tab2 = st.tabs(["📥 ENCRYPTION", "📤 DECRYPTION"])

# --- ENCRYPTION TAB ---
with tab1:
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("### 1. Load Carrier")
        uploaded_file = st.file_uploader("Upload Cover Image", type=["png"], help="Lossless PNG recommended")

        st.markdown("### 2. Secret Data")
        secret_text = st.text_area("Message to Hide", placeholder="Type your encrypted message here...")

        # Hiding the key using password type
        passphrase = st.text_input("Encryption Key", type="password", help="This seed generates the random pixel map.")

        # Convert passphrase to a numeric seed for random
        seed = sum(ord(c) for c in passphrase) if passphrase else 1234

    with col2:
        if uploaded_file:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            # Capacity Calculation
            total_pixels = img.shape[0] * img.shape[1]
            used_pixels = 32 + (len(secret_text) * 8)
            capacity_pct = (used_pixels / total_pixels) * 100

            st.markdown("### 3. Image Analysis")
            m1, m2 = st.columns(2)
            m1.metric("Total Capacity", f"{total_pixels // 1024} KB")
            m2.metric("Payload Size", f"{used_pixels} bits", delta=f"{capacity_pct:.2f}%", delta_color="inverse")

            if st.button("🚀 EXECUTE ENCRYPTION"):
                if used_pixels > total_pixels:
                    st.error("Error: Message exceeds image capacity!")
                else:
                    # Logic
                    msg_bits = text_to_bits(secret_text)
                    len_bits = [int(b) for b in format(len(secret_text), '032b')]
                    all_bits = len_bits + msg_bits

                    indices = [(r, c) for r in range(img.shape[0]) for c in range(img.shape[1])]
                    random.seed(seed)
                    random.shuffle(indices)

                    # Embedding
                    for i, bit in enumerate(all_bits):
                        r, c = indices[i]
                        img[r, c, 1] = (img[r, c, 1] & 254) | bit

                    st.success("Encryption Successful!")
                    st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Resulting Stego-Image")

                    _, buffer = cv2.imencode(".png", img)
                    st.download_button("💾 Download Stego-Image", buffer.tobytes(), "encrypted_payload.png")

# --- DECRYPTION TAB ---
with tab2:
    st.header("Extraction Protocol")
    col_dec1, col_dec2 = st.columns([1, 1])

    with col_dec1:
        stego_file = st.file_uploader("Upload Stego-Image", type=["png"], key="dec_upload")
        # Hiding the key here too
        dec_passphrase = st.text_input("Enter Extraction Key", type="password", key="dec_key")
        dec_seed = sum(ord(c) for c in dec_passphrase) if dec_passphrase else 1234

        if stego_file and st.button("🔓 EXTRACT SECRET"):
            file_bytes = np.asarray(bytearray(stego_file.read()), dtype=np.uint8)
            stego_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            indices = [(r, c) for r in range(stego_img.shape[0]) for c in range(stego_img.shape[1])]
            random.seed(dec_seed)
            random.shuffle(indices)

            # Extract Header
            header_bits = [stego_img[indices[i][0], indices[i][1], 1] & 1 for i in range(32)]
            msg_len = int("".join(map(str, header_bits)), 2)

            if msg_len > 100000 or msg_len < 0:
                st.error("Access Denied: Invalid Key or Corrupted Payload.")
            else:
                # Extract Message
                msg_bits = [stego_img[indices[i][0], indices[i][1], 1] & 1 for i in range(32, 32 + (msg_len * 8))]
                result = bits_to_text(msg_bits)

                with col_dec2:
                    st.markdown("### Decoded Content")
                    st.info(result)