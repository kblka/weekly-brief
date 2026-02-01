"""
Phase 3: Text-to-speech and audio file.

Uses Google Cloud Text-to-Speech to convert summary to MP3.
"""

from pathlib import Path

from google.cloud import texttospeech

# Calm voice, good for brief narration
DEFAULT_VOICE = "en-US-Neural2-D"
DEFAULT_LANG = "en-US"


def synthesize_to_file(
    text: str,
    output_path: Path,
    voice_name: str = DEFAULT_VOICE,
    language_code: str = DEFAULT_LANG,
) -> Path:
    """
    Convert text to speech and save as MP3.

    Uses Google Cloud TTS. Credentials: same as Calendar (OAuth token) or
    GOOGLE_APPLICATION_CREDENTIALS for service account.

    Args:
        text: Text to speak
        output_path: Path for output MP3
        voice_name: TTS voice (e.g. en-US-Neural2-D, en-US-Wavenet-D)
        language_code: Language (e.g. en-US)

    Returns:
        Path to saved MP3
    """
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=0.9,  # Slightly slower for calm delivery
        sample_rate_hertz=24000,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.audio_content)
    return output_path
