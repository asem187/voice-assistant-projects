"""
Main application for the Realtime Voice Assistant.
Production-ready voice assistant with OpenAI Realtime API integration.
"""

import asyncio
import logging
import signal
import sys
import uuid
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

# Application imports
from config import settings, logging_config
from database import initialize_database, cleanup_database, db_manager
from audio_manager import audio_manager, test_audio_system
from openai_client import realtime_api, SessionConfig
from tools import tool_registry


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=logging_config.log_format,
    datefmt=logging_config.date_format
)
logger = logging.getLogger(__name__)


class VoiceAssistant:
    """Main voice assistant application."""
    
    def __init__(self):
        self.user_id = str(uuid.uuid4())  # Default user ID
        self.session_id = None
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
    async def initialize(self) -> bool:
        """Initialize the voice assistant components."""
        try:
            logger.info("Initializing Realtime Voice Assistant...")
            
            # Initialize database
            logger.info("Initializing database...")
            await initialize_database()
            
            # Test audio system
            logger.info("Testing audio system...")
            audio_test = await test_audio_system()
            if not audio_test.get("microphone", False):
                logger.warning("Microphone test failed - voice input may not work")
            if not audio_test.get("speaker", False):
                logger.warning("Speaker test failed - voice output may not work")
            
            # Configure session for OpenAI Realtime API
            session_config = SessionConfig(
                instructions=self._get_system_instructions(),
                voice="alloy",
                temperature=0.8,
                tools=tool_registry.get_tool_definitions(),
                turn_detection={
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 1000
                }
            )
            
            # Initialize OpenAI Realtime API
            logger.info("Connecting to OpenAI Realtime API...")
            success = await realtime_api.initialize(session_config)
            if not success:
                logger.error("Failed to initialize OpenAI Realtime API")
                return False
            
            # Register tool handlers
            self._register_tool_handlers()
            
            # Register event handlers
            self._register_event_handlers()
            
            logger.info("Voice Assistant initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Voice Assistant: {e}")
            return False
    
    def _get_system_instructions(self) -> str:
        """Get system instructions for the AI assistant."""
        return f"""You are an intelligent voice assistant with advanced capabilities. Your name is "Assistant" and you're helping a user with various tasks through voice interaction.

Current context:
- User ID: {self.user_id}
- Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- System: {settings.app_name} v{settings.app_version}

Your capabilities:
1. **Memory Management**: Store and retrieve information using create_memory, get_memory, search_memories
2. **Task Management**: Create, update, and track tasks with create_task, list_tasks, update_task
3. **File Operations**: Read and write files with read_file, write_file, list_directory
4. **System Operations**: Execute safe commands with execute_command, get system info
5. **VS Code Integration**: Open files and projects with open_vscode
6. **Time/Date**: Get current time and date information

Guidelines:
- Be conversational and helpful
- Use tools when appropriate to accomplish user requests
- Store important information in memory for future reference
- Create tasks when the user mentions things they need to do
- Be proactive in suggesting useful actions
- Always prioritize user privacy and security
- Confirm destructive actions before executing them

When the user asks you to remember something, use create_memory. When they ask about something from the past, search your memories first.

Respond naturally and concisely. You can hear the user and they can hear you."""
    
    def _register_tool_handlers(self):
        """Register tool handlers with the API manager."""
        for tool_name, tool_function in tool_registry.tools.items():
            realtime_api.register_tool(
                tool_name, 
                self._create_tool_wrapper(tool_function),
                tool_registry.tool_definitions[tool_name]
            )
    
    def _create_tool_wrapper(self, tool_function):
        """Create a wrapper for tool functions to inject user_id."""
        async def wrapper(**kwargs):
            # Inject user_id for tools that need it
            if 'user_id' in tool_function.__code__.co_varnames:
                kwargs['user_id'] = self.user_id
            
            try:
                if asyncio.iscoroutinefunction(tool_function):
                    result = await tool_function(**kwargs)
                else:
                    result = tool_function(**kwargs)
                
                logger.info(f"Tool {tool_function.__name__} executed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_function.__name__}: {e}")
                return {"success": False, "error": str(e)}
        
        return wrapper
    
    def _register_event_handlers(self):
        """Register event handlers for the realtime API."""
        if realtime_api.client:
            realtime_api.client.on("audio_response_complete", self._handle_audio_response)
            realtime_api.client.on("text_complete", self._handle_text_response)
            realtime_api.client.on("error", self._handle_api_error)
    
    async def _handle_audio_response(self, audio_data: bytes):
        """Handle audio responses from the API."""
        try:
            if audio_data:
                # Play the audio response
                await audio_manager.play_response_audio(audio_data)
                logger.debug(f"Played audio response: {len(audio_data)} bytes")
        except Exception as e:
            logger.error(f"Error playing audio response: {e}")
    
    async def _handle_text_response(self, text: str):
        """Handle text responses from the API."""
        logger.info(f"Assistant response: {text}")
        # Text responses are handled automatically by audio in realtime mode
    
    async def _handle_api_error(self, error_data: dict):
        """Handle API errors."""
        logger.error(f"OpenAI API error: {error_data}")
    
    async def run_voice_interaction(self):
        """Run the main voice interaction loop."""
        try:
            self.is_running = True
            logger.info("Starting voice interaction...")
            logger.info("Say something to the assistant, or press Ctrl+C to exit")
            
            while self.is_running and not self.shutdown_event.is_set():
                try:
                    # Record voice input with voice activity detection
                    logger.debug("Listening for voice input...")
                    voice_result = await audio_manager.record_voice_input(use_vad=True)
                    
                    if voice_result:
                        audio_data, filepath = voice_result
                        logger.info("Voice input detected, processing...")
                        
                        # Convert audio to the correct format for OpenAI
                        formatted_audio = audio_manager.convert_to_realtime_format(audio_data)
                        
                        # Send to OpenAI Realtime API
                        await realtime_api.send_voice_input(formatted_audio)
                        
                        # Brief pause to allow processing
                        await asyncio.sleep(0.1)
                    
                    else:
                        # No voice detected, short pause
                        await asyncio.sleep(0.5)
                
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
                    break
                except Exception as e:
                    logger.error(f"Error in voice interaction loop: {e}")
                    await asyncio.sleep(1)  # Prevent rapid error loops
            
        except Exception as e:
            logger.error(f"Fatal error in voice interaction: {e}")
        finally:
            self.is_running = False
    
    async def run_text_interaction(self):
        """Run text-based interaction for testing/fallback."""
        try:
            self.is_running = True
            logger.info("Starting text interaction mode...")
            logger.info("Type messages to the assistant, or 'quit' to exit")
            
            while self.is_running and not self.shutdown_event.is_set():
                try:
                    # Get user input
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, "You: "
                    )
                    
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        break
                    
                    if user_input.strip():
                        # Send to OpenAI Realtime API
                        await realtime_api.send_text_input(user_input)
                        
                        # Brief pause to allow processing
                        await asyncio.sleep(0.1)
                
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received")
                    break
                except Exception as e:
                    logger.error(f"Error in text interaction: {e}")
                    await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Fatal error in text interaction: {e}")
        finally:
            self.is_running = False
    
    async def shutdown(self):
        """Shutdown the voice assistant gracefully."""
        try:
            logger.info("Shutting down Voice Assistant...")
            self.is_running = False
            self.shutdown_event.set()
            
            # Cleanup components
            await realtime_api.cleanup()
            await audio_manager.cleanup_temp_files()
            await cleanup_database()
            
            logger.info("Voice Assistant shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


async def main():
    """Main application entry point."""
    assistant = VoiceAssistant()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(assistant.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize the assistant
        success = await assistant.initialize()
        if not success:
            logger.error("Failed to initialize assistant")
            return 1
        
        # Choose interaction mode based on audio availability
        logger.info("Checking interaction mode...")
        audio_test = await test_audio_system()
        
        if audio_test.get("microphone", False):
            logger.info("Audio system available - starting voice interaction")
            await assistant.run_voice_interaction()
        else:
            logger.info("Audio system not available - starting text interaction")
            await assistant.run_text_interaction()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    try:
        # Run the application
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Application terminated")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal application error: {e}")
        sys.exit(1)
