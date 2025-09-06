#!/usr/bin/env python3
"""
Script de test pour vérifier que l'API Blackbox fonctionne correctement
"""

import sys
from main import BlackboxMentor, load_env_file

def test_api():
    """Test simple de l'API Blackbox"""
    print("🔍 Test de l'API Blackbox...")
    
    # Charger les variables d'environnement
    load_env_file()
    
    try:
        # Initialisation du mentor
        mentor = BlackboxMentor()
        print("✅ Agent Mentor initialisé avec succès")
        
        # Test 1: Question simple
        test_question = "Explique-moi en une phrase ce qu'est Python"
        print(f"❓ Test 1: {test_question}")
        
        print("⏳ Appel de l'API Blackbox en cours...")
        response = mentor.call_blackbox_api(test_question)
        
        if response.startswith("❌"):
            print(f"❌ Erreur API: {response}")
            return False
        
        print(f"✅ Réponse reçue ({len(response)} caractères)")
        print(f"📝 Réponse: {response[:200]}{'...' if len(response) > 200 else ''}")
        print()
        
        # Test 2: Question de mentorat en développement
        test_question2 = "Comment bien débuter en développement web ?"
        print(f"❓ Test 2: {test_question2}")
        
        print("⏳ Appel de l'API Blackbox en cours...")
        response2 = mentor.call_blackbox_api(test_question2)
        
        if response2.startswith("❌"):
            print(f"❌ Erreur API: {response2}")
            return False
            
        print(f"✅ Réponse reçue ({len(response2)} caractères)")
        print(f"📝 Réponse: {response2[:300]}{'...' if len(response2) > 300 else ''}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)