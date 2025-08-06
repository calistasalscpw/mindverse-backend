import sys
import json
import os
import re
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Try to import the actual chatbot with database connection
try:
    from chatbot import MindVerseAI
    HAS_REAL_CHATBOT = True
except ImportError:
    HAS_REAL_CHATBOT = False

def clean_response_text(text):
    """Clean response text from markdown and excessive formatting"""
    if not text:
        return text
    
    # Remove markdown formatting but keep basic structure
    clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold
    clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)  # *italic* -> italic
    clean_text = re.sub(r'#{1,6}\s*', '', clean_text)  # Remove headers
    clean_text = re.sub(r'`([^`]+)`', r'\1', clean_text)  # Remove code formatting
    
    # Keep bullet points but clean them up
    clean_text = re.sub(r'^[\s]*[-*+]\s*', '• ', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'^\s*\d+\.\s*', '• ', clean_text, flags=re.MULTILINE)
    
    # Clean up spacing but preserve paragraph breaks
    clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text)  # Max 2 newlines
    clean_text = re.sub(r'[ \t]+', ' ', clean_text)  # Multiple spaces to single
    clean_text = re.sub(r'^\s+|\s+$', '', clean_text, flags=re.MULTILINE)  # Trim lines
    
    return clean_text.strip()

def initialize_chatbot():
    """Initialize the MindVerse AI chatbot with database connection"""
    if not HAS_REAL_CHATBOT:
        return None, "MindVerseAI module not available"
    
    try:
        # Updated to use OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY', '')
        mongo_uri = os.getenv('MONGO_URI', 'mongodb+srv://Python:K60wVjdLcDruClvl@cluster0.fbol8bw.mongodb.net/')
        
        # Disable verbose mode to avoid JSON parsing issues
        chatbot = MindVerseAI(api_key, mongo_uri, verbose=False)
        return chatbot, None
    except Exception as e:
        return None, str(e)

def handle_chat_request(message, chatbot):
    """Handle chat request with priority on database information"""
    try:
        # Always try database first for any query that might have database info
        if chatbot:
            # Use real chatbot for all queries
            result = chatbot.chat(
                user_query=message,
                max_results_each=10,  # Increased for better results
                include_metadata=True
            )
            
            if isinstance(result, dict):
                answer = result.get("answer", "Cannot process your request.")
                clean_answer = clean_response_text(answer)
                
                return {
                    "success": True,
                    "answer": clean_answer,
                    "sources": result.get("sources", []),
                    "has_context": result.get("has_context", False),
                    "tokens": result.get("tokens", 0),
                    "intent": result.get("intent_detected", "unknown"),
                    "results_count": result.get("results_found", 0),
                    "filters_applied": result.get("filters_applied", {})
                }
            else:
                # Handle string response
                clean_answer = clean_response_text(str(result))
                return {
                    "success": True,
                    "answer": clean_answer,
                    "sources": ["Database"],
                    "has_context": True,
                    "tokens": 0
                }
        
        # Only use fallback if chatbot is completely unavailable
        else:
            return get_fallback_response(message)
            
    except Exception as e:
        # On error, provide helpful error message
        return {
            "success": True,
            "answer": f"Technical issue occurred: {str(e)}. Please try again.",
            "sources": [],
            "has_context": False,
            "tokens": 0,
            "error": str(e)
        }

def get_fallback_response(message):
    """Provide natural fallback responses for non-database queries"""
    message_lower = message.lower()
    
    # Greeting responses
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'halo', 'hai']):
        return {
            "success": True,
            "answer": "Hello! I'm MindVerse AI Assistant. I can help you with information about tasks, team members, forum discussions, and other workspace questions. What can I help you with today?",
            "sources": [],
            "has_context": False,
            "tokens": 25
        }
    
    # Help queries
    elif any(word in message_lower for word in ['help', 'bantuan', 'assist']):
        return {
            "success": True,
            "answer": "I can help you with:\n• Information about tasks and their status\n• Team member details and roles\n• Forum discussions and posts\n• Project progress status\n\nPlease ask me something specific!",
            "sources": [],
            "has_context": False,
            "tokens": 35
        }
    
    # General workspace questions
    elif any(word in message_lower for word in ['workspace', 'dashboard', 'overview']):
        return {
            "success": True,
            "answer": "Your MindVerse workspace contains a personal dashboard with task summaries, forums for team discussions, and collaboration tools. The dashboard displays tasks organized by status (To Do, In Progress, Review, Done) to help you stay organized.",
            "sources": ["Dashboard"],
            "has_context": True,
            "tokens": 40
        }
    
    # Default response for unclear queries
    else:
        return {
            "success": True,
            "answer": f"I understand you're asking about '{message}'. To provide more accurate information, could you be more specific? For example:\n• \"What tasks are currently in progress?\"\n• \"Which user is working on project X?\"\n• \"Recent posts about what?\"\n\nOr type 'help' to see what I can assist with.",
            "sources": [],
            "has_context": False,
            "tokens": 35
        }

def handle_stats_request(chatbot):
    """Handle database statistics request"""
    try:
        if chatbot:
            stats = chatbot.get_stats()
            if "error" not in stats:
                return {
                    "success": True,
                    "comments": stats.get("comments", 0),
                    "posts": stats.get("posts", 0),
                    "tasks": stats.get("tasks", 0),
                    "users": stats.get("users", 0),
                    "total": stats.get("total", 0)
                }
        
        # Return error if can't get real stats
        return {
            "success": False,
            "error": "Cannot retrieve database statistics",
            "comments": 0,
            "posts": 0,
            "tasks": 0,
            "users": 0,
            "total": 0
        }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "comments": 0,
            "posts": 0,
            "tasks": 0,
            "users": 0,
            "total": 0
        }

def handle_health_check(chatbot):
    """Handle health check request"""
    return {
        "success": True,
        "status": "healthy",
        "message": "MindVerse AI Assistant is operational",
        "database_connected": chatbot is not None
    }

def main():
    """Main function to handle requests from Node.js"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "No message provided",
            "answer": "Please provide a message."
        }))
        return

    message = sys.argv[1]
    
    # Initialize chatbot
    chatbot, error = initialize_chatbot()
    
    try:
        # Handle different types of requests
        if message == "__GET_STATS__":
            result = handle_stats_request(chatbot)
        elif message == "__HEALTH_CHECK__":
            result = handle_health_check(chatbot)
        else:
            result = handle_chat_request(message, chatbot)
        
        # Output result as JSON
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "answer": "A system error occurred. Please try again."
        }))
    
    finally:
        try:
            if chatbot:
                chatbot.close()
        except:
            pass

if __name__ == "__main__":
    main()