"""
Command Line Interface for Mentor Agent

Provides interactive terminal interface for testing and using the mentor agent.
"""

import asyncio
import sys
import uuid
from typing import Optional
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import from the agent module
sys.path.append(str(Path(__file__).parent))

from agent import run_mentor_agent, run_mentor_conversation
from settings import mentor_settings


class MentorCLI:
    """Interactive CLI for the mentor agent."""
    
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id or f"cli-user-{uuid.uuid4().hex[:8]}"
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        
    def display_welcome(self):
        """Display welcome message."""
        print("\n" + "="*60)
        print("🧠 Programming Mentor Agent - Socratic Learning Assistant")
        print("="*60)
        print(f"User ID: {self.user_id}")
        print(f"Session: {self.session_id}")
        print("\nI'm here to guide you through programming problems using the Socratic method.")
        print("I won't give you direct answers, but I'll ask questions to help you discover solutions!")
        print("\nType 'help' for commands, 'quit' to exit.")
        print("-"*60)
    
    def display_help(self):
        """Display help information."""
        print("\n📚 Mentor Agent Commands:")
        print("  help        - Show this help message")
        print("  quit/exit   - Exit the mentor session")
        print("  clear       - Clear conversation history")
        print("  history     - Show conversation history")
        print("  new         - Start a new session")
        print("  debug       - Toggle debug mode")
        print("\n💡 Tips:")
        print("  - Ask specific programming questions")
        print("  - I remember our past conversations")
        print("  - I'll gradually give more hints if you're stuck")
        print("  - Try to work through problems step by step\n")
    
    def display_history(self):
        """Display conversation history."""
        if not self.conversation_history:
            print("\n📝 No conversation history yet.")
            return
        
        print(f"\n📝 Conversation History (Session: {self.session_id}):")
        print("-" * 50)
        for i, msg in enumerate(self.conversation_history, 1):
            role_emoji = "👤" if msg['role'] == 'user' else "🧠"
            print(f"{i}. {role_emoji} {msg['role'].title()}: {msg['content'][:100]}...")
        print("-" * 50)
    
    async def handle_user_input(self, user_input: str) -> bool:
        """
        Handle user input and return whether to continue.
        
        Returns:
            bool: True to continue, False to quit
        """
        user_input = user_input.strip()
        
        # Handle special commands
        if user_input.lower() in ['quit', 'exit']:
            print("\n👋 Thanks for using the Mentor Agent! Keep learning!")
            return False
        
        elif user_input.lower() == 'help':
            self.display_help()
            return True
        
        elif user_input.lower() == 'clear':
            self.conversation_history.clear()
            print("\n🗑️  Conversation history cleared.")
            return True
        
        elif user_input.lower() == 'history':
            self.display_history()
            return True
        
        elif user_input.lower() == 'new':
            self.session_id = str(uuid.uuid4())
            self.conversation_history.clear()
            print(f"\n🆕 Started new session: {self.session_id}")
            return True
        
        elif user_input.lower() == 'debug':
            debug_status = "ON" if mentor_settings.debug else "OFF"
            print(f"\n🐛 Debug mode is currently: {debug_status}")
            return True
        
        # Handle programming questions
        elif user_input:
            try:
                # Add user message to history
                self.conversation_history.append({
                    'role': 'user',
                    'content': user_input
                })
                
                print("\n🤔 Let me think about this...")
                
                # Get mentor response
                if len(self.conversation_history) == 1:
                    # First message in conversation
                    response = await run_mentor_agent(
                        user_input,
                        user_id=self.user_id,
                        session_id=self.session_id
                    )
                else:
                    # Multi-turn conversation
                    response = await run_mentor_conversation(
                        self.conversation_history,
                        user_id=self.user_id,
                        session_id=self.session_id
                    )
                
                # Add mentor response to history
                self.conversation_history.append({
                    'role': 'mentor',
                    'content': response
                })
                
                print(f"\n🧠 Mentor: {response}")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'help' for assistance.")
        
        return True
    
    async def run(self):
        """Run the interactive CLI."""
        self.display_welcome()
        
        try:
            while True:
                try:
                    # Get user input
                    user_input = input(f"\n👤 You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle the input
                    should_continue = await self.handle_user_input(user_input)
                    if not should_continue:
                        break
                        
                except KeyboardInterrupt:
                    print("\n\n👋 Session interrupted. Goodbye!")
                    break
                except EOFError:
                    print("\n\n👋 Session ended. Goodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Unexpected error: {e}")
                    print("Type 'help' for assistance or 'quit' to exit.")


async def run_single_question(question: str, user_id: Optional[str] = None) -> str:
    """
    Run a single question through the mentor agent.
    
    Args:
        question: Programming question to ask
        user_id: Optional user identifier
    
    Returns:
        Mentor's response
    """
    user_id = user_id or f"single-user-{uuid.uuid4().hex[:8]}"
    response = await run_mentor_agent(question, user_id=user_id)
    return response


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Programming Mentor Agent - Socratic Learning Assistant"
    )
    parser.add_argument(
        "--user-id", 
        type=str, 
        help="User identifier for memory tracking"
    )
    parser.add_argument(
        "--question", 
        type=str, 
        help="Ask a single question instead of interactive mode"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Set debug mode if requested
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        mentor_settings.debug = True
    
    try:
        if args.question:
            # Single question mode
            async def run_single():
                response = await run_single_question(args.question, args.user_id)
                print(f"\n🧠 Mentor: {response}")
            
            asyncio.run(run_single())
        else:
            # Interactive CLI mode
            cli = MentorCLI(user_id=args.user_id)
            asyncio.run(cli.run())
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting mentor agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()