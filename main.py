#!/usr/bin/env python3
"""
Mini programme qui utilise l'API Blackbox pour répondre aux questions des utilisateurs
avec un prompt system personnalisé depuis agent-mentor.md
"""

import os
import requests
import json
from typing import Optional
from pathlib import Path

def load_env_file():
    """Charge les variables d'environnement depuis le fichier .env"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

class BlackboxMentor:
    def __init__(self, agent_file: str = "agent-mentor.md"):
        self.api_url = "https://api.blackbox.ai/chat/completions"
        self.agent_file = agent_file
        self.system_prompt = self._load_system_prompt()
        
    def _load_system_prompt(self) -> str:
        """Charge le prompt système depuis le fichier agent spécifié"""
        prompt_file = Path(self.agent_file)
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Le fichier {prompt_file} est introuvable. Veuillez créer ce fichier avec le prompt système.")
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    raise ValueError(f"Le fichier {prompt_file} est vide. Veuillez ajouter un prompt système.")
                return content
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la lecture du fichier {prompt_file}: {e}")
    
    def _get_api_key(self) -> Optional[str]:
        """Récupère la clé API depuis les variables d'environnement"""
        return os.getenv('BLACKBOX_API_KEY')
    
    def call_blackbox_api(self, user_prompt: str) -> str:
        """Appelle l'API Blackbox avec le prompt utilisateur"""
        api_key = self._get_api_key()
        
        if not api_key:
            return "❌ Erreur: Clé API Blackbox non configurée. Ajoutez BLACKBOX_API_KEY dans vos variables d'environnement."
        
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
                return "❌ Erreur: Réponse inattendue de l'API Blackbox"
                
        except requests.exceptions.RequestException as e:
            return f"❌ Erreur de connexion à l'API: {e}"
        except json.JSONDecodeError as e:
            return f"❌ Erreur de décodage JSON: {e}"
        except Exception as e:
            return f"❌ Erreur inattendue: {e}"

def choose_agent() -> str:
    """Permet à l'utilisateur de choisir quel agent utiliser"""
    print("\n🎯 Choisissez votre agent mentor :")
    print("1. Agent Mentor (donne des réponses complètes)")
    print("2. Agent Mentor Strict (indices uniquement, idéal pour juniors)")
    
    while True:
        try:
            choice = input("\nVotre choix (1 ou 2): ").strip()
            if choice == "1":
                return "agent-mentor.md"
            elif choice == "2":
                return "agent-mentor-strict.md"
            else:
                print("⚠️  Veuillez saisir 1 ou 2")
        except KeyboardInterrupt:
            print("\n\n👋 Programme interrompu. Au revoir !")
            exit(0)

def main():
    """Fonction principale du programme"""
    # Charger les variables d'environnement depuis .env
    load_env_file()
    
    print("🤖 Agent Mentor AI - Powered by Blackbox")
    print("=" * 50)
    
    # Choisir l'agent
    agent_file = choose_agent()
    
    try:
        mentor = BlackboxMentor(agent_file)
        agent_name = "Agent Mentor" if "strict" not in agent_file else "Agent Mentor Strict"
        print(f"✅ {agent_name} chargé avec succès depuis {agent_file}")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return 1
    
    print("Tapez 'quit' ou 'exit' pour quitter le programme\n")
    
    while True:
        try:
            user_input = input("👤 Votre question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Au revoir ! Bonne programmation !")
                break
            
            if not user_input:
                print("⚠️  Veuillez saisir une question.\n")
                continue
            
            print("\n🤔 Agent Mentor réfléchit...")
            response = mentor.call_blackbox_api(user_input)
            
            print(f"\n🤖 Agent Mentor:\n{response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\n👋 Programme interrompu. Au revoir !")
            break
        except Exception as e:
            print(f"\n❌ Erreur inattendue: {e}\n")

if __name__ == "__main__":
    main()