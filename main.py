from ai_client import ask_ai
from db import db
import sys

def main():
    # Check for debug flag in command line arguments
    debug = "--debug" in sys.argv or "-d" in sys.argv
    
    print("=== AI Notes + Calendar + Tasks MVP ===")
    print("You can ask about your events, todos, goals, and notes.")
    print("The AI will fetch relevant data as needed.")
    print("Commands:")
    print("  'quit' or 'exit' - Exit the application")
    print("  'debug' - Toggle debug mode (shows AI reasoning)")
    print("  'clear history' - Clear conversation history (for unrelated topics)")
    if debug:
        print("\n[DEBUG MODE ENABLED]")
    print("\nType 'quit' to exit.\n")

    conversation_history = []  # Maintain conversation context across messages

    while True:
        user_input = input("> ").strip()
        
        if user_input.lower() in ["quit", "exit"]:
            break
        
        if user_input.lower() == "debug":
            debug = not debug
            status = "ENABLED" if debug else "DISABLED"
            print(f"Debug mode {status}\n")
            continue
        
        if user_input.lower() == "clear history":
            conversation_history = []
            print("Conversation history cleared.\n")
            continue
        
        if not user_input:
            continue

        try:
            ai_message, usage = ask_ai(user_input, debug=debug, messages_history=conversation_history)
            print(f"\n{ai_message}")
            print(f"\n(Tokens used: {usage})\n")
            
            # Add this exchange to conversation history for context
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": ai_message})
            
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    main()

