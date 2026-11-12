import streamlit as st
from faster_whisper import WhisperModel
from pathlib import Path
from datetime import datetime
import tempfile
import re
import os
import sys
import shutil
import subprocess


# =========================================================
# PROJECT FOLDERS AND SETTINGS
# =========================================================

BASE_DIR = Path(__file__).parent

UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"
SEPARATED_DIR = BASE_DIR / "separated"

UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)
SEPARATED_DIR.mkdir(exist_ok=True)

SUPPORTED_FORMATS = [
    "mp3", "wav", "m4a", "mp4", "ogg", "flac"
]

MODEL_SIZE = "small"


# =========================================================
# LANGUAGES
# =========================================================

LANGUAGES = {
    "Auto Detect": None,
    "Tamil": "ta",
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Malayalam": "ml",
    "Kannada": "kn",
    "Bengali": "bn",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Urdu": "ur",
    "Assamese": "as",
    "Odia": "or",
    "Nepali": "ne",
    "Arabic": "ar",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Japanese": "ja"
}


# =========================================================
# UI TRANSLATIONS
# =========================================================

UI = {
    "English": {
        "dashboard": "Dashboard",
        "upload": "Audio Upload",
        "batch": "Batch Processing",
        "language": "Language Selection",
        "history": "Transcription History",
        "reports": "TXT / PDF Reports",
        "about": "About Project",
        "title": "Multilanguage Voice Chatbot",
        "subtitle": "Your multilingual voice-to-text workspace",
        "start": "Start Transcription"
    },

    "தமிழ்": {
        "dashboard": "முகப்பு",
        "upload": "Audio Upload",
        "batch": "பல கோப்புகள் செயலாக்கம்",
        "language": "மொழித் தேர்வு",
        "history": "Transcription வரலாறு",
        "reports": "TXT / PDF அறிக்கைகள்",
        "about": "Project விவரம்",
        "title": "பல்மொழி குரல் உரையாடல்",
        "subtitle": "உங்கள் குரலை எழுத்தாக மாற்றும் செயலி",
        "start": "Transcription தொடங்கு"
    },

    "Tanglish": {
        "dashboard": "Dashboard",
        "upload": "Audio Upload",
        "batch": "Batch Processing",
        "language": "Language Selection",
        "history": "Transcription History",
        "reports": "TXT / PDF Reports",
        "about": "About Project",
        "title": "Multilanguage Voice Chatbot",
        "subtitle": "Unga voice-ai text-ah convert pannum app",
        "start": "Transcription Start Pannunga"
    }
}


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Multilanguage Voice Chatbot",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

[data-testid="stAppViewContainer"] {
    background: linear-gradient(
        135deg,
        #0b1420,
        #101d2b,
        #111827
    );
    color: white;
}

[data-testid="stSidebar"] {
    background: #101a28;
    border-right: 2px solid #00c9ed;
}

.main-title {
    color: #00ED24;
    font-size: 38px;
    font-weight: bold;
}

.subtitle {
    color: #c4d1df;
    font-size: 16px;
}

.hero {
    padding: 25px;
    border-radius: 18px;
    background: linear-gradient(
        110deg,
        #00c9ed22,
        #8A00ED33
    );
    border: 1px solid #00c9ed66;
    margin: 20px 0;
}

div.stButton > button {
    background-color: #00c9ed;
    color: black;
    border-radius: 10px;
    font-weight: bold;
    height: 45px;
}

div.stButton > button:hover {
    background-color: #EDBA00;
    color: black;
}

.metric-card {
    background: #172431;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #00c9ed66;
}

.metric-number {
    color: #00c9ed;
    font-size: 30px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "ui_language" not in st.session_state:
    st.session_state.ui_language = "English"


# =========================================================
# LOAD WHISPER MODEL
# =========================================================

@st.cache_resource
def load_model():

    return WhisperModel(
        MODEL_SIZE,
        device="cpu",
        compute_type="int8"
    )


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe_filename(filename):

    name = Path(filename).stem

    return re.sub(
        r"[^A-Za-z0-9_-]",
        "_",
        name
    )


def timestamp(seconds):

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours:02}:{minutes:02}:{secs:05.2f}"


def create_pdf(content, pdf_path):

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from xml.sax.saxutils import escape

    except ImportError:
        raise RuntimeError(
            "ReportLab is not installed. Run: "
            "python -m pip install reportlab"
        )

    font_name = "Helvetica"

    # Tamil font support on Windows
    font_path = Path("C:/Windows/Fonts/Nirmala.ttf")

    if font_path.exists():

        try:
            if "TamilFont" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(
                    TTFont("TamilFont", str(font_path))
                )

            font_name = "TamilFont"

        except Exception:
            pass

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    story = []

    for line in content.splitlines():

        if line.strip():

            style = styles["BodyText"]
            style.fontName = font_name
            style.leading = 15

            story.append(
                Paragraph(
                    escape(line),
                    style
                )
            )

        else:
            story.append(
                Spacer(1, 8)
            )

    doc.build(story)


# =========================================================
# FULL AUDIO TRANSCRIPTION
# =========================================================

def transcribe_audio(uploaded_file, language_code):

    suffix = Path(uploaded_file.name).suffix.lower()

    temp_path = None

    try:

        # Save uploaded audio temporarily
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=UPLOAD_DIR
        ) as temp_file:

            temp_file.write(
                uploaded_file.getbuffer()
            )

            temp_path = Path(temp_file.name)

        model = load_model()

        # Transcribe the complete audio
        segments_generator, info = model.transcribe(
            str(temp_path),
            language=language_code,
            task="transcribe",
            beam_size=5,
            vad_filter=False,
            condition_on_previous_text=True
        )

        # IMPORTANT: collect every segment
        segments = list(segments_generator)

        # Build complete transcript
        transcript = "\n".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        )

        return segments, info, transcript

    finally:

        # Delete temporary audio
        if temp_path and temp_path.exists():
            temp_path.unlink()


# =========================================================
# SAVE NORMAL TXT AND PDF REPORTS
# =========================================================

def save_reports(filename, info, segments, transcript):

    now = datetime.now()

    stamp = now.strftime("%Y%m%d_%H%M%S_%f")

    filename_clean = safe_filename(filename)

    report_name = (
        f"{filename_clean}_transcript_{stamp}"
    )

    report_content = f"""
MULTILANGUAGE VOICE-TO-TEXT REPORT

File Name: {filename}

Date: {now.strftime("%d-%m-%Y %H:%M:%S")}

Detected Language: {info.language}

Language Confidence: {info.language_probability:.1%}

Model: faster-whisper {MODEL_SIZE}

Total Segments: {len(segments)}

FULL TRANSCRIPTION WITH TIMESTAMPS

"""

    for segment in segments:

        report_content += (
            f"[{timestamp(segment.start)} - "
            f"{timestamp(segment.end)}] "
            f"{segment.text.strip()}\n"
        )

    report_content += f"""

COMPLETE TRANSCRIPT

{transcript}
"""

    txt_path = REPORT_DIR / f"{report_name}.txt"
    pdf_path = REPORT_DIR / f"{report_name}.pdf"

    txt_path.write_text(
        report_content,
        encoding="utf-8"
    )

    create_pdf(
        report_content,
        pdf_path
    )

    return txt_path, pdf_path


# =========================================================
# SPEAKER DIARIZATION MODEL
# =========================================================

@st.cache_resource
def load_speaker_model():

    token = os.getenv("HF_TOKEN")

    if not token:
        raise RuntimeError(
            "HF_TOKEN is missing. Set your Hugging Face token "
            "as a Windows environment variable and restart VS Code."
        )

    try:
        from pyannote.audio import Pipeline

    except ImportError:
        raise RuntimeError(
            "pyannote.audio is not installed. Run: "
            "python -m pip install pyannote.audio"
        )

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1",
        token=token
    )

    if pipeline is None:
        raise RuntimeError(
            "Could not load the speaker model. "
            "Check Hugging Face model access."
        )

    return pipeline


# =========================================================
# CONVERSATION TRANSCRIPTION WITH SPEAKERS
# =========================================================

def analyze_conversation(uploaded_file):

    suffix = Path(uploaded_file.name).suffix.lower()

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=UPLOAD_DIR
        ) as temp_file:

            temp_file.write(
                uploaded_file.getbuffer()
            )

            temp_path = Path(temp_file.name)

        # -----------------------------------------
        # STEP 1: Detect speakers
        # -----------------------------------------

        pipeline = load_speaker_model()

        diarization_result = pipeline(
            str(temp_path)
        )

        if hasattr(
            diarization_result,
            "exclusive_speaker_diarization"
        ):

            diarization = (
                diarization_result.exclusive_speaker_diarization
            )

        else:

            diarization = (
                diarization_result.speaker_diarization
            )

        speaker_map = {}
        speaker_segments = []

        for turn, track, speaker in diarization.itertracks(
            yield_label=True
        ):

            if speaker not in speaker_map:

                speaker_map[speaker] = (
                    f"Person {len(speaker_map) + 1}"
                )

            speaker_segments.append({
                "speaker": speaker_map[speaker],
                "start": turn.start,
                "end": turn.end
            })

        # -----------------------------------------
        # STEP 2: Transcribe complete audio
        # -----------------------------------------

        model = load_model()

        segments_generator, info = model.transcribe(
            str(temp_path),
            task="transcribe",
            beam_size=5,
            vad_filter=False,
            condition_on_previous_text=True
        )

        transcript_segments = list(
            segments_generator
        )

        # -----------------------------------------
        # STEP 3: Match transcript with speakers
        # -----------------------------------------

        final_segments = []

        for segment in transcript_segments:

            middle = (
                segment.start + segment.end
            ) / 2

            speaker_name = "Unknown"

            for speaker in speaker_segments:

                if (
                    speaker["start"] <= middle
                    <= speaker["end"]
                ):

                    speaker_name = speaker["speaker"]
                    break

            if segment.text.strip():

                final_segments.append({
                    "speaker": speaker_name,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })

        return len(speaker_map), final_segments, info

    finally:

        if temp_path and temp_path.exists():
            temp_path.unlink()


# =========================================================
# SAVE SPEAKER CONVERSATION REPORTS
# =========================================================

def save_speaker_reports(
    filename,
    speaker_count,
    results,
    info
):

    now = datetime.now()

    stamp = now.strftime("%Y%m%d_%H%M%S_%f")

    filename_clean = safe_filename(filename)

    report_name = (
        f"{filename_clean}_conversation_{stamp}"
    )

    lines = [
        "MULTILANGUAGE CONVERSATION TRANSCRIPTION",
        "",
        f"File Name: {filename}",
        f"Date: {now.strftime('%d-%m-%Y %H:%M:%S')}",
        f"Detected Language: {info.language}",
        f"Total Speakers: {speaker_count}",
        f"Total Transcript Segments: {len(results)}",
        "",
        "FULL CONVERSATION WITH SPEAKERS AND TIMESTAMPS",
        ""
    ]

    for item in results:

        lines.append(
            f"[{timestamp(item['start'])} - "
            f"{timestamp(item['end'])}] "
            f"{item['speaker']}: {item['text']}"
        )

    report_content = "\n".join(lines)

    txt_path = REPORT_DIR / f"{report_name}.txt"
    pdf_path = REPORT_DIR / f"{report_name}.pdf"

    txt_path.write_text(
        report_content,
        encoding="utf-8"
    )

    create_pdf(
        report_content,
        pdf_path
    )

    return txt_path, pdf_path


# =========================================================
# SONG VOCAL AND BACKGROUND MUSIC SEPARATION
# =========================================================

def separate_song(uploaded_file):

    suffix = Path(uploaded_file.name).suffix.lower()

    temp_path = None

    try:

        ffmpeg_path = shutil.which("ffmpeg")

        if not ffmpeg_path:

            raise RuntimeError(
                "FFmpeg is not installed or not available in PATH. "
                "Install FFmpeg and restart VS Code."
            )

        try:
            import demucs
        except ImportError:
            raise RuntimeError(
                "Demucs is not installed. Run: "
                "python -m pip install demucs"
            )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=UPLOAD_DIR
        ) as temp_file:

            temp_file.write(
                uploaded_file.getbuffer()
            )

            temp_path = Path(temp_file.name)

        command = [
            sys.executable,
            "-m",
            "demucs",
            "-d",
            "cpu",
            "--two-stems=vocals",
            "-n",
            "htdemucs",
            "-o",
            str(SEPARATED_DIR),
            str(temp_path)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            error_text = (
                result.stderr[-3000:]
                if result.stderr
                else result.stdout[-3000:]
            )

            raise RuntimeError(error_text)

        song_folder = (
            SEPARATED_DIR
            / "htdemucs"
            / temp_path.stem
        )

        vocals_path = song_folder / "vocals.wav"

        music_path = song_folder / "no_vocals.wav"

        if not vocals_path.exists():

            raise FileNotFoundError(
                "Vocals output was not created."
            )

        if not music_path.exists():

            raise FileNotFoundError(
                "Background music output was not created."
            )

        return vocals_path, music_path

    finally:

        if temp_path and temp_path.exists():
            temp_path.unlink()


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:

    st.markdown("## 🎙️ VOICE STUDIO")

    st.caption("MULTILANGUAGE TRANSCRIPTION")

    st.divider()

    st.session_state.ui_language = st.selectbox(
        "UI Language",
        ["English", "தமிழ்", "Tanglish"]
    )

    T = UI[st.session_state.ui_language]

    page = st.radio(
        "NAVIGATION",
        [
            T["dashboard"],
            T["upload"],
            T["batch"],
            T["language"],
            T["history"],
            T["reports"],
            T["about"]
        ]
    )

    st.divider()

    st.caption("THEME COLORS")

    st.markdown("🟦 Cyan #00c9ed")
    st.markdown("🟠 Orange #ED4300")
    st.markdown("🟡 Yellow #EDBA00")
    st.markdown("🟣 Purple #8A00ED")
    st.markdown("🟢 Green #00ED24")


# =========================================================
# COMMON UI FUNCTIONS
# =========================================================

def show_header():

    st.markdown(
        f'<div class="main-title">{T["title"]}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<div class="subtitle">{T["subtitle"]}</div>',
        unsafe_allow_html=True
    )


# =========================================================
# PROCESS NORMAL AND BATCH AUDIO FILES
# =========================================================

def process_files(files, language_code):

    if not files:

        st.warning("Please select audio files.")
        return

    progress = st.progress(0)

    for index, uploaded in enumerate(
        files,
        start=1
    ):

        st.info(
            f"Processing {index}/{len(files)}: "
            f"{uploaded.name}"
        )

        try:

            segments, info, transcript = transcribe_audio(
                uploaded,
                language_code
            )

            if not transcript.strip():

                raise RuntimeError(
                    "No speech detected in this audio."
                )

            txt_path, pdf_path = save_reports(
                uploaded.name,
                info,
                segments,
                transcript
            )

            item = {
                "file": uploaded.name,
                "language": info.language,
                "confidence": info.language_probability,
                "transcript": transcript,
                "date": datetime.now().strftime(
                    "%d-%m-%Y %H:%M:%S"
                ),
                "txt": str(txt_path),
                "pdf": str(pdf_path)
            }

            st.session_state.history.insert(
                0,
                item
            )

            st.success(
                f"Completed: {uploaded.name} | "
                f"Language: {info.language} | "
                f"Segments: {len(segments)}"
            )

            with st.expander(
                f"View Full Transcript: {uploaded.name}"
            ):

                st.text_area(
                    "Complete Transcript",
                    transcript,
                    height=350,
                    key=f"transcript_{index}_{safe_filename(uploaded.name)}"
                )

                st.download_button(
                    "Download Full TXT",
                    txt_path.read_bytes(),
                    file_name=txt_path.name,
                    mime="text/plain",
                    key=f"normal_txt_{index}_{safe_filename(uploaded.name)}"
                )

                st.download_button(
                    "Download Full PDF",
                    pdf_path.read_bytes(),
                    file_name=pdf_path.name,
                    mime="application/pdf",
                    key=f"normal_pdf_{index}_{safe_filename(uploaded.name)}"
                )

        except Exception as error:

            st.error(
                f"Error processing {uploaded.name}: {error}"
            )

        progress.progress(
            index / len(files)
        )

    st.success("All files processed!")


# =========================================================
# DASHBOARD
# =========================================================

if page == T["dashboard"]:

    show_header()

    st.markdown("""
    <div class="hero">

    <h2>Welcome to Voice Studio 🎧</h2>

    <p>
    Upload audio files, detect spoken languages,
    convert speech into text and download reports.
    </p>

    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            f'<div class="metric-card">'
            f'<div>Completed Files</div>'
            f'<div class="metric-number">'
            f'{len(st.session_state.history)}'
            f'</div></div>',
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            '<div class="metric-card">'
            '<div>Audio Formats</div>'
            '<div class="metric-number">06</div>'
            '</div>',
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            '<div class="metric-card">'
            '<div>UI Languages</div>'
            '<div class="metric-number">03</div>'
            '</div>',
            unsafe_allow_html=True
        )

    st.subheader("Quick Start")

    st.write("1. Open Audio Upload.")
    st.write("2. Select Auto Detect or a spoken language.")
    st.write("3. Upload your audio.")
    st.write("4. Start transcription.")
    st.write("5. Download the complete TXT or PDF report.")


# =========================================================
# AUDIO UPLOAD
# =========================================================

elif page == T["upload"]:

    show_header()

    language_name = st.selectbox(
        "Select Spoken Language",
        list(LANGUAGES.keys()),
        key="upload_language"
    )

    language_code = LANGUAGES[language_name]

    uploaded = st.file_uploader(
        "Upload Audio or Video File",
        type=SUPPORTED_FORMATS,
        key="single_audio_upload"
    )

    if uploaded:

        st.audio(uploaded)

        st.divider()

        st.subheader("🎙️ Audio Analysis")

        analysis_type = st.radio(
            "Choose Audio Type",
            [
                "Normal Transcription",
                "Conversation - Speaker Detection",
                "Song - Vocals & Music Separation"
            ],
            key="analysis_type"
        )

        # -----------------------------------------
        # NORMAL TRANSCRIPTION
        # -----------------------------------------

        if analysis_type == "Normal Transcription":

            if st.button(
                T["start"],
                use_container_width=True
            ):

                process_files(
                    [uploaded],
                    language_code
                )

        # -----------------------------------------
        # CONVERSATION SPEAKER DETECTION
        # -----------------------------------------

        elif analysis_type == "Conversation - Speaker Detection":

            st.info(
                "Speaker detection labels different voices "
                "as Person 1, Person 2, etc. These labels do not "
                "identify real people or reliably determine gender."
            )

            if st.button(
                "Identify Speakers and Transcribe Full Audio",
                use_container_width=True
            ):

                try:

                    with st.spinner(
                        "Detecting speakers and transcribing the complete audio..."
                    ):

                        speaker_count, results, info = (
                            analyze_conversation(uploaded)
                        )

                    if not results:

                        st.warning(
                            "No speech detected in this audio."
                        )

                    else:

                        st.success(
                            f"Total Speakers Detected: {speaker_count}"
                        )

                        st.success(
                            f"Detected Language: {info.language}"
                        )

                        full_conversation = "\n".join(
                            f"[{timestamp(item['start'])} - "
                            f"{timestamp(item['end'])}] "
                            f"{item['speaker']}: {item['text']}"
                            for item in results
                        )

                        st.subheader(
                            "Complete Conversation"
                        )

                        st.text_area(
                            "Full Transcript",
                            full_conversation,
                            height=450
                        )

                        st.subheader(
                            "Conversation Details"
                        )

                        for item in results:

                            st.markdown(
                                f"**{item['speaker']}**"
                            )

                            st.caption(
                                f"{timestamp(item['start'])} - "
                                f"{timestamp(item['end'])}"
                            )

                            st.write(
                                item["text"]
                            )

                            st.divider()

                        txt_path, pdf_path = save_speaker_reports(
                            uploaded.name,
                            speaker_count,
                            results,
                            info
                        )

                        st.download_button(
                            "Download Full Conversation TXT",
                            txt_path.read_bytes(),
                            file_name=txt_path.name,
                            mime="text/plain"
                        )

                        st.download_button(
                            "Download Full Conversation PDF",
                            pdf_path.read_bytes(),
                            file_name=pdf_path.name,
                            mime="application/pdf"
                        )

                        st.session_state.history.insert(
                            0,
                            {
                                "file": uploaded.name,
                                "language": info.language,
                                "confidence": info.language_probability,
                                "transcript": full_conversation,
                                "date": datetime.now().strftime(
                                    "%d-%m-%Y %H:%M:%S"
                                ),
                                "txt": str(txt_path),
                                "pdf": str(pdf_path)
                            }
                        )

                except Exception as error:

                    st.error(
                        f"Speaker analysis failed: {error}"
                    )

        # -----------------------------------------
        # SONG VOCAL AND MUSIC SEPARATION
        # -----------------------------------------

        elif analysis_type == "Song - Vocals & Music Separation":

            st.info(
                "This option separates vocals from accompaniment. "
                "It does not separate individual male and female singers."
            )

            if st.button(
                "Separate Vocals & Music",
                use_container_width=True
            ):

                try:

                    with st.spinner(
                        "Separating vocals and background music. "
                        "This may take some time..."
                    ):

                        vocals_path, music_path = (
                            separate_song(uploaded)
                        )

                    st.success(
                        "Song separation completed!"
                    )

                    st.subheader("🎤 Vocals")

                    st.audio(
                        str(vocals_path)
                    )

                    st.download_button(
                        "Download Vocals",
                        vocals_path.read_bytes(),
                        file_name="vocals.wav",
                        mime="audio/wav"
                    )

                    st.subheader("🎵 Background Music")

                    st.audio(
                        str(music_path)
                    )

                    st.download_button(
                        "Download Background Music",
                        music_path.read_bytes(),
                        file_name="background_music.wav",
                        mime="audio/wav"
                    )

                except Exception as error:

                    st.error(
                        f"Song separation failed: {error}"
                    )


# =========================================================
# BATCH PROCESSING
# =========================================================

elif page == T["batch"]:

    show_header()

    language_name = st.selectbox(
        "Select Spoken Language",
        list(LANGUAGES.keys()),
        key="batch_language"
    )

    language_code = LANGUAGES[language_name]

    files = st.file_uploader(
        "Upload Multiple Audio Files",
        type=SUPPORTED_FORMATS,
        accept_multiple_files=True,
        key="batch_audio_upload"
    )

    if files:

        st.write(
            f"Selected files: {len(files)}"
        )

        for file in files:

            st.write("•", file.name)

        if st.button(
            "Process All Files",
            use_container_width=True
        ):

            process_files(
                files,
                language_code
            )


# =========================================================
# LANGUAGE SELECTION
# =========================================================

elif page == T["language"]:

    show_header()

    st.subheader("Supported Languages")

    for language in LANGUAGES:

        st.write("🌐", language)

    st.info(
        "Auto Detect allows Whisper to identify "
        "the spoken language automatically."
    )


# =========================================================
# TRANSCRIPTION HISTORY
# =========================================================

elif page == T["history"]:

    show_header()

    if not st.session_state.history:

        st.info(
            "No transcription history available in this session."
        )

    else:

        for index, item in enumerate(
            st.session_state.history
        ):

            with st.expander(
                item["file"]
            ):

                st.write(
                    "Language:",
                    item["language"]
                )

                st.write(
                    "Confidence:",
                    f"{item['confidence']:.1%}"
                )

                st.write(
                    "Date:",
                    item["date"]
                )

                st.text_area(
                    "Complete Transcript",
                    item["transcript"],
                    height=300,
                    key=f"history_{index}"
                )

                txt_file = Path(item["txt"])
                pdf_file = Path(item["pdf"])

                if txt_file.exists():

                    st.download_button(
                        "Download TXT",
                        txt_file.read_bytes(),
                        file_name=txt_file.name,
                        mime="text/plain",
                        key=f"history_txt_{index}"
                    )

                if pdf_file.exists():

                    st.download_button(
                        "Download PDF",
                        pdf_file.read_bytes(),
                        file_name=pdf_file.name,
                        mime="application/pdf",
                        key=f"history_pdf_{index}"
                    )


# =========================================================
# REPORTS
# =========================================================

elif page == T["reports"]:

    show_header()

    st.subheader("Generated TXT / PDF Reports")

    reports = sorted(
        REPORT_DIR.glob("*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True
    )

    reports = [
        report
        for report in reports
        if report.suffix.lower() in [".txt", ".pdf"]
    ]

    if not reports:

        st.info(
            "No reports available. Process an audio file first."
        )

    else:

        for index, report in enumerate(reports):

            st.write(report.name)

            mime = (
                "application/pdf"
                if report.suffix.lower() == ".pdf"
                else "text/plain"
            )

            st.download_button(
                "Download " + report.suffix.upper(),
                report.read_bytes(),
                file_name=report.name,
                mime=mime,
                key=f"report_{index}"
            )

            st.divider()


# =========================================================
# ABOUT PROJECT
# =========================================================

elif page == T["about"]:

    show_header()

    st.subheader("Project Information")

    st.write(
        "Project: Multilanguage Voice-to-Text Agent"
    )

    st.write(
        "Speech Recognition: faster-whisper"
    )

    st.write(
        f"Model Size: {MODEL_SIZE}"
    )

    st.write(
        "Processing: Local CPU / INT8"
    )

    st.write(
        "Speaker Detection: pyannote.audio"
    )

    st.write(
        "Song Separation: Demucs"
    )

    st.write(
        "Formats: MP3, WAV, M4A, MP4, OGG, FLAC"
    )

    st.write(
        "Reports: TXT and PDF"
    )

    st.write(
        "Temporary audio files are stored in uploads "
        "during processing and deleted afterward."
    )

    st.write(
        "Generated reports are saved in the reports folder."
    )

    st.warning(
        "Long audio files may take more time to process. "
        "Transcription quality depends on audio clarity, "
        "language and recording conditions."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Powered by faster-whisper | "
    "pyannote.audio | Demucs | "
    "Multilanguage Voice-to-Text Project"
)