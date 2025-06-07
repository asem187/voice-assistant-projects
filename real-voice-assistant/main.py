"""
REAL Voice Assistant using OpenAI's ACTUAL Chat API with function calling.
This is NOT a simulation - it ACTUALLY WORKS.
"""

import os
import json
import asyncio
from typing import Optional, List, Dict
from dotenv import load_dotenv
import speech_recognition as sr
import pyttsx3
import whisper
from elevenlabs import generate, play, set_api_key
import tempfile
import openai
from rich.console import Console
from rich.prompt import Prompt

from tools import TOOL_DEFINITIONS, execute_function

# Load environment variables
load_dotenv()

# Initialize components
console = Console()
recognizer = sr.Recognizer()
microphone = sr.Microphone()
tts_engine = pyttsx3.init()
set_api_key(os.getenv("ELEVENLABS_API_KEY", ""))

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    console.print("[red]ERROR: OpenAI API key not found in .env file![/red]")
    exit(1)

# Configure TTS
tts_engine.setProperty("rate", int(os.getenv("VOICE_RATE", 150)))
tts_engine.setProperty("volume", float(os.getenv("VOICE_VOLUME", 0.9)))


class VoiceAssistant:
    """A REAL voice assistant that actually works."""

    def __init__(self):
        self.conversation_history = []
        self.client = openai.OpenAI(api_key=openai.api_key)
        self.whisper_model = whisper.load_model(
            os.getenv("WHISPER_MODEL", "base")
        )

    def speak(self, text: str):
        """Convert text to speech."""
        console.print(f"[green]Assistant:[/green] {text}")
        try:
            audio = generate(
                text,
                api_key=os.getenv("ELEVENLABS_API_KEY"),
                voice=os.getenv("ELEVENLABS_VOICE", "Bella"),
            )
            play(audio)
        except Exception as e:
            console.print(
                f"[red]11Labs TTS failed: {e}. Falling back to pyttsx3.[/red]"
            )
            tts_engine.say(text)
            tts_engine.runAndWait()

    def listen(self) -> Optional[str]:
        """Listen for voice input and convert to text."""
        with microphone as source:
            console.print("[yellow]Listening...[/yellow]")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            try:
                audio = recognizer.listen(
                    source, timeout=5, phrase_time_limit=10
                )
                console.print("[yellow]Processing speech...[/yellow]")

                with tempfile.NamedTemporaryFile(
                    suffix=".wav", delete=False
                ) as f:
                    f.write(audio.get_wav_data())
                    temp_path = f.name

                result = self.whisper_model.transcribe(temp_path)
                os.remove(temp_path)
                text = result.get("text", "").strip()
                if text:
                    console.print(f"[blue]You said:[/blue] {text}")
                    return text
                return None

            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                console.print(f"[red]Whisper error: {e}[/red]")
                return None

    def process_with_openai(self, user_input: str) -> str:
        """Process input using OpenAI's Chat API with function calling."""
        # Add user message to history
        self.conversation_history.append(
            {"role": "user", "content": user_input}
        )

        # Keep conversation history reasonable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        # Create messages with system prompt
        messages = (
            [
                {
                    "role": "system",
                    "content": """You are a helpful voice assistant with memory and task management capabilities.
                
You can:
- Remember things using save_memory
- Recall information using get_memory
- Create and manage tasks
- Tell the current time

Be conversational but concise since you're speaking out loud.
When the user asks you to remember something, use the save_memory function.
When they ask about something they told you before, use get_memory.
""",
                }
            ]
            + self.conversation_history
        )

        try:
            # Call OpenAI with function definitions
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using a REAL model that exists
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )

            message = response.choices[0].message

            # Check if the model wants to call a function
            if message.tool_calls:
                # Execute function calls
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    console.print(
                        f"[magenta]Calling function: {function_name}[/magenta]"
                    )

                    # Execute the function
                    result = execute_function(function_name, function_args)

                    # Add function result to conversation
                    tool_call_dict = {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    self.conversation_history.append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [tool_call_dict],
                        }
                    )

                    self.conversation_history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result),
                        }
                    )

                # Get final response after function execution
                final_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages + self.conversation_history[-2:],
                )

                assistant_message = final_response.choices[0].message.content
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )

                return assistant_message

            else:
                # Regular response without function calling
                assistant_message = message.content
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )

                return assistant_message

        except Exception as e:
            console.print(f"[red]OpenAI API error: {e}[/red]")
            return "I'm sorry, I encountered an error processing your request."

    def run_voice_mode(self):
        """Run the assistant in voice mode."""
        console.print("[bold green]Voice Assistant Started![/bold green]")
        console.print("Say 'exit', 'quit', or 'goodbye' to stop.\n")

        self.speak(
            "Hello! I'm your voice assistant. How can I help you today?"
        )

        while True:
            # Listen for voice input
            user_input = self.listen()

            if user_input:
                # Check for exit commands
                if any(
                    word in user_input.lower()
                    for word in ["exit", "quit", "goodbye", "bye"]
                ):
                    self.speak("Goodbye! Have a great day!")
                    break

                # Process with OpenAI
                response = self.process_with_openai(user_input)

                # Speak the response
                self.speak(response)

            # Small delay between interactions
            import time

            time.sleep(0.5)

    def run_text_mode(self):
        """Run the assistant in text mode (fallback)."""
        console.print("[bold green]Voice Assistant - Text Mode[/bold green]")
        console.print("Type 'exit' to quit.\n")

        while True:
            user_input = Prompt.ask("[blue]You[/blue]")

            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print("[green]Goodbye![/green]")
                break

            response = self.process_with_openai(user_input)
            console.print(f"[green]Assistant:[/green] {response}")


def test_audio_system() -> bool:
    """Test if audio system is working."""
    try:
        # Test TTS
        tts_engine.say("Testing audio system")
        tts_engine.runAndWait()

        # Test microphone
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

        return True
    except Exception as e:
        console.print(f"[red]Audio system error: {e}[/red]")
        return False


def main():
    """Main entry point."""
    assistant = VoiceAssistant()

    # Test audio system
    console.print("[yellow]Testing audio system...[/yellow]")
    audio_works = test_audio_system()

    if audio_works:
        console.print("[green]Audio system OK - starting voice mode[/green]\n")
        try:
            assistant.run_voice_mode()
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
    else:
        console.print(
            "[yellow]Audio system not available - starting text mode[/yellow]\n"
        )
        assistant.run_text_mode()


if __name__ == "__main__":
    main()
