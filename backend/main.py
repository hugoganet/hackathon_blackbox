#!/usr/bin/env python3
"""
Mini program that uses the Blackbox API to answer user questions
with a custom system prompt from agents/agent-mentor.md
Updated to use PydanticAI mentor agent with backward compatibility
"""

import os
import requests
import json
from typing import Optional
from pathlib import Path

def get_agent_path(agent_filename: str) -> str:
    """
    Dynamically resolve agent file paths to work from both root and backend directories
    """
    # Try relative path first (when running from backend directory)
    relative_path = Path(f"../agents/{agent_filename}")
    if relative_path.exists():
        return str(relative_path)
    
    # Try from root directory
    root_path = Path(f"agents/{agent_filename}")
    if root_path.exists():
        return str(root_path)
    
    # If neither exists, return the relative path and let the error handling deal with it
    return str(relative_path)

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Import the new PydanticAI-based adapter
try:
    from agents.mentor_agent.adapter import BlackboxMentorAdapter
    BlackboxMentor = BlackboxMentorAdapter
except ImportError as e:
    print(f"Warning: Could not import PydanticAI adapter ({e}), falling back to original BlackboxMentor")
    # Fallback to original implementation if PydanticAI is not available
    class BlackboxMentor:
        def __init__(self, agent_file: str = None):
            if agent_file is None:
                agent_file = get_agent_path("agent-mentor.md")
            else:
                # If a specific file is provided, resolve it dynamically
                filename = Path(agent_file).name
                agent_file = get_agent_path(filename)
            self.api_url = "https://api.blackbox.ai/chat/completions"
            self.agent_file = agent_file
            self.system_prompt = self._load_system_prompt()
        
        def _load_system_prompt(self) -> str:
            """Load system prompt from specified agent file"""
            prompt_file = Path(self.agent_file)
            
            if not prompt_file.exists():
                raise FileNotFoundError(f"File {prompt_file} not found. Please create this file with the system prompt.")
            
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        raise ValueError(f"File {prompt_file} is empty. Please add a system prompt.")
                    return content
            except Exception as e:
                raise RuntimeError(f"Error reading file {prompt_file}: {e}")
        
        def _get_api_key(self) -> Optional[str]:
            """Get API key from environment variables"""
            return os.getenv('BLACKBOX_API_KEY')
        
        def call_blackbox_api(self, user_prompt: str) -> str:
            """Call Blackbox API with user prompt"""
            api_key = self._get_api_key()
            
            if not api_key:
                return "❌ Error: Blackbox API key not configured. Add BLACKBOX_API_KEY to your environment variables."
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            payload = {
                'model': 'blackboxai/anthropic/claude-sonnet-4',
                'messages': [
                    {
                        'role': 'system',
                        'content': self.system_prompt
                    },
                    {
                        'role': 'user', 
                        'content': user_prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 1000,
                'stream': False
            }
            
            try:
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                else:
                    return "❌ Error: Unexpected response from Blackbox API"
                    
            except requests.exceptions.RequestException as e:
                return f"❌ API connection error: {e}"
            except json.JSONDecodeError as e:
                return f"❌ JSON decoding error: {e}"
            except Exception as e:
                return f"❌ Unexpected error: {e}"

def choose_agent() -> tuple:
    """Allow user to choose which agent to use"""
    print("\n🎯 Choose your mentor agent:")
    print("1. Mentor Agent (gives complete answers)")
    print("2. Strict Mentor Agent (hints only, ideal for juniors)")
    print("3. PydanticAI Mentor Agent (advanced memory-guided mentoring)")
    
    while True:
        try:
            choice = input("\nYour choice (1, 2, or 3): ").strip()
            if choice == "1":
                return ("blackbox", get_agent_path("agent-mentor.md"))
            elif choice == "2":
                return ("blackbox", get_agent_path("agent-mentor-strict.md"))
            elif choice == "3":
                return ("pydantic", None)
            else:
                print("⚠️  Please enter 1, 2, or 3")
        except KeyboardInterrupt:
            print("\n\n👋 Program interrupted. Goodbye!")
            exit(0)

def main():
    """Main program function"""
    # Load environment variables from .env
    load_env_file()
    
    print("🤖 Mentor Agent AI - Powered by Blackbox")
    print("=" * 50)
    
    # Choose the agent
    agent_type, agent_file = choose_agent()
    
    try:
        if agent_type == "blackbox":
            mentor = BlackboxMentor(agent_file)
        elif agent_type == "pydantic":
            try:
                from agents.mentor_agent import BlackboxMentorAdapter
                mentor = BlackboxMentorAdapter()
                agent_name = "PydanticAI Mentor Agent"
            except ImportError as e:
                print(f"❌ PydanticAI mentor agent not available: {e}")
                print("⚠️  Falling back to Blackbox Strict Mentor")
                mentor = BlackboxMentor(get_agent_path("agent-mentor-strict.md"))
                agent_name = "Strict Mentor Agent (Fallback)"
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        if agent_type == "blackbox":
            agent_name = "Mentor Agent" if "strict" not in agent_file else "Strict Mentor Agent"
        print(f"✅ {agent_name} loaded successfully from {agent_file}")
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return 1
    
    print("Type 'quit' or 'exit' to exit the program\n")
    
    while True:
        try:
            user_input = input("👤 Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Happy programming!")
                break
            
            if not user_input:
                print("⚠️  Please enter a question.\n")
                continue
            
            print("\n🤔 Mentor Agent is thinking...")
            response = mentor.call_blackbox_api(user_input)
            
            print(f"\n🤖 Mentor Agent:\n{response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\n👋 Program interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}\n")

if __name__ == "__main__":
    main()