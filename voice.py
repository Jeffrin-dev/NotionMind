import os
import speech_recognition as sr
from rich.console import Console

console = Console()

# ── detect internet connection ─────────────────────────────────────────────────
def is_online() -> bool:
    try:
        import httpx
        httpx.get("https://www.google.com", timeout=3)
        return True
    except:
        return False

# ── online voice: Edge TTS (neural, ChatGPT-quality) ─────────────────────────
def speak_gtts(text: str):
    try:
        import asyncio
        import edge_tts
        import tempfile
        import pygame

        async def _speak():
            tts = edge_tts.Communicate(text, voice='en-US-JennyNeural')
            import tempfile
            tmpdir = tempfile.gettempdir()
            tmpfile = os.path.join(tmpdir, 'notionmind_tts.mp3')
            await tts.save(tmpfile)
            return tmpfile

        tmpfile = asyncio.run(_speak())

        pygame.mixer.init()
        pygame.mixer.music.load(tmpfile)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.quit()
        os.unlink(tmpfile)

    except Exception as e:
        console.print(f"[yellow]Edge TTS failed: {e}. Falling back to espeak.[/]")
        speak_espeak(text)

# ── offline voice: espeak + mbrola ───────────────────────────────────────────
def speak_espeak(text: str):
    clean = (text
        .replace("*", "").replace("#", "")
        .replace("`", "").replace("[", "")
        .replace("]", "").replace("→", "")
        .replace("✓", "good").replace("•", "")
        .replace('"', "").replace("'", ""))
    os.system(f'espeak -v mb-en1 -s 140 -p 40 "{clean}"')

# ── smart speak: auto picks online/offline ────────────────────────────────────
def speak(text: str):
    # clean text for speech
    clean = (text
        .replace("*", "").replace("#", "")
        .replace("`", "").replace("[", "")
        .replace("]", "").replace("→", "")
        .replace("✓", "good").replace("•", "")
        .replace('"', "").replace("'", ""))

    if is_online():
        console.print("[dim]🔊 Speaking (online — Edge TTS)...[/]")
        speak_gtts(clean)
    else:
        console.print("[dim]🔊 Speaking (offline — espeak)...[/]")
        speak_espeak(clean)
        
# ── voice input ───────────────────────────────────────────────────────────────
def listen() -> str:
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        console.print("[dim]🎤 Adjusting for background noise...[/]")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        console.print("[bold green]🎤 Listening... speak now![/]")

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            console.print("[dim]Processing...[/]")
            text = recognizer.recognize_google(audio)
            console.print(f"[cyan]You said:[/] {text}")
            return text
        except sr.WaitTimeoutError:
            console.print("[yellow]No speech detected. Try again.[/]")
            return ""
        except sr.UnknownValueError:
            console.print("[yellow]Could not understand. Try again.[/]")
            return ""
        except sr.RequestError:
            console.print("[red]No internet for voice recognition.[/]")
            return ""
