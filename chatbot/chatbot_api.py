import sys
import json
import os
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

class MindVerseAI:
    def __init__(self, openai_api_key=None, mongo_uri=None, verbose=False):
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.verbose = verbose
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY in .env file.")
        
        mongo_uri = mongo_uri or os.getenv('MONGO_URL')
        if not mongo_uri:
            raise ValueError("MongoDB URI is required. Please set MONGO_URL in .env file.")
        
        try:
            self.mongo_client = MongoClient(mongo_uri)
            self.mongo_client.admin.command('ping')
            if self.verbose:
                print("Connected to MongoDB Atlas")
        except Exception as e:
            if self.verbose:
                print(f"Failed to connect to MongoDB: {e}")
            raise
        
        # Connect to database and collections
        self.db = self.mongo_client['mindverse']
        self.comments_collection = self.db['comments']
        self.posts_collection = self.db['posts']
        self.tasks_collection = self.db['tasks']
        self.users_collection = self.db['users']
        
        self.openai_url = "https://api.openai.com/v1/chat/completions"

    def get_stats(self):
        try:
            stats = {
                "comments": self.comments_collection.count_documents({}),
                "posts": self.posts_collection.count_documents({}),
                "tasks": self.tasks_collection.count_documents({}),
                "users": self.users_collection.count_documents({})
            }
            stats["total"] = sum(stats.values())
            return stats
        except Exception as e:
            return {"error": str(e)}

    def analyze_query_intent(self, query):
        """Simplified intent analysis"""
        query_lower = query.lower()
        
        # Define keyword groups
        task_keywords = ['task', 'tugas', 'assigned', 'endpoint', 'api', 'authentication', 'auth', 'development', 'develop', 'figma', 'frontend', 'backend', 'integration', 'coding', 'review', 'onboarding']
        user_keywords = ['user', 'member', 'team', 'who', 'role', 'lead', 'hr', 'florence', 'eris', 'amelya', 'aroliani', 'python', 'calista', 'faisal', 'lyne', 'idon', 'carol']
        forum_keywords = ['post', 'discussion', 'forum', 'diskusi', 'pompia', 'tutorial', 'wifi', 'maintenance', 'lunch']
        
        # Status filters (only if explicitly mentioned)
        status_map = {
            "In Progress": ['progress', 'sedang', 'ongoing', 'berlangsung'],
            "ToDo": ['todo', 'to do', 'belum', 'pending', 'waiting'],
            "Done": ['done', 'selesai', 'completed', 'finished', 'complete'],
            "Review": ['review', 'checking', 'direview']
        }
        
        intent = {"type": "general", "filters": {}}
        
        # Determine primary intent
        if any(k in query_lower for k in task_keywords):
            intent["type"] = "tasks"
            # Check for status filters
            for status, keywords in status_map.items():
                if any(k in query_lower for k in keywords):
                    intent["filters"]["progressStatus"] = status
                    break
        elif any(k in query_lower for k in user_keywords):
            intent["type"] = "users"
        elif any(k in query_lower for k in forum_keywords):
            intent["type"] = "posts"
        elif any(word in query_lower for word in ['comment', 'komentar']):
            intent["type"] = "comments"
            
        return intent

    def search_database(self, query, intent, max_results=10):
        """Unified search function"""
        try:
            results = []
            
            if intent["type"] == "tasks":
                results = self.search_tasks(query, intent["filters"], max_results)
            elif intent["type"] == "users":
                results.extend(self.search_users(query, max_results//2))
                results.extend(self.search_tasks(query, {}, max_results//2))  # Also search related tasks
            elif intent["type"] == "posts":
                results = self.search_posts(query, max_results)
            elif intent["type"] == "comments":
                results = self.search_comments(query, max_results)
            else:
                # General search - search all types
                results.extend(self.search_tasks(query, {}, max_results//3))
                results.extend(self.search_users(query, max_results//3))
                results.extend(self.search_posts(query, max_results//3))
            
            return results[:max_results]
        except Exception as e:
            if self.verbose:
                print(f"Search error: {e}")
            return []

    def search_tasks(self, query, filters={}, max_results=10):
        try:
            # Build search filter
            if filters:
                match_filter = filters
            else:
                # Flexible text search with synonyms
                search_terms = [
                    {"name": {"$regex": re.escape(query), "$options": "i"}},
                    {"description": {"$regex": re.escape(query), "$options": "i"}}
                ]
                
                # Add synonym matching
                query_lower = query.lower()
                if 'auth' in query_lower:
                    search_terms.append({"name": {"$regex": "auth|login|user", "$options": "i"}})
                if 'endpoint' in query_lower or 'api' in query_lower:
                    search_terms.append({"description": {"$regex": "endpoint|api|login", "$options": "i"}})
                if 'figma' in query_lower:
                    search_terms.append({"name": {"$regex": "figma|edit", "$options": "i"}})
                
                match_filter = {"$or": search_terms}
            
            # MongoDB aggregation with user lookup
            pipeline = [
                {"$match": match_filter},
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "assignTo", 
                        "foreignField": "_id",
                        "as": "assignedUsers"
                    }
                },
                {"$limit": max_results}
            ]
            
            results = list(self.tasks_collection.aggregate(pipeline))
            
            # Format results
            formatted = []
            for item in results:
                assignees = [user.get('username', user.get('name', 'Unknown')) for user in item.get('assignedUsers', [])]
                formatted.append({
                    "type": "task",
                    "name": item.get('name', 'Untitled Task'),
                    "progressStatus": item.get('progressStatus', 'No status'),
                    "description": item.get('description', ''),
                    "assignee": ', '.join(assignees) if assignees else 'Unassigned',
                    "due_date": item.get('dueDate', 'No deadline')
                })
            
            return formatted
        except Exception as e:
            if self.verbose:
                print(f"Task search error: {e}")
            return []

    def search_users(self, query, max_results=10):
        try:
            # Flexible user search
            if not query or query.lower() in ['user', 'users', 'member', 'team', 'all']:
                search_filter = {}
            else:
                search_filter = {
                    "$or": [
                        {"name": {"$regex": re.escape(query), "$options": "i"}},
                        {"username": {"$regex": re.escape(query), "$options": "i"}},
                        {"email": {"$regex": re.escape(query), "$options": "i"}}
                    ]
                }
            
            results = list(self.users_collection.find(search_filter).limit(max_results))
            
            # Format results
            formatted = []
            for item in results:
                role = "Lead" if item.get('isLead') else "HR" if item.get('isHR') else "Member"
                formatted.append({
                    "type": "user",
                    "name": item.get('username', item.get('name', 'User')),
                    "email": item.get('email', ''),
                    "role": role
                })
            
            return formatted
        except Exception as e:
            if self.verbose:
                print(f"User search error: {e}")
            return []

    def search_posts(self, query, max_results=5):
        try:
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"title": {"$regex": re.escape(query), "$options": "i"}},
                            {"body": {"$regex": re.escape(query), "$options": "i"}}
                        ]
                    }
                },
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "author",
                        "foreignField": "_id", 
                        "as": "authorData"
                    }
                },
                {"$limit": max_results}
            ]
            
            results = list(self.posts_collection.aggregate(pipeline))
            
            formatted = []
            for item in results:
                author = 'Unknown User'
                if item.get('authorData'):
                    author_data = item['authorData'][0]
                    author = author_data.get('username', author_data.get('name', 'Unknown User'))
                
                formatted.append({
                    "type": "post",
                    "title": item.get('title', 'No Title'),
                    "content": item.get('body', ''),
                    "author": author
                })
            
            return formatted
        except Exception as e:
            if self.verbose:
                print(f"Post search error: {e}")
            return []

    def search_comments(self, query, max_results=5):
        try:
            search_filter = {
                "$or": [
                    {"body": {"$regex": re.escape(query), "$options": "i"}},
                    {"name": {"$regex": re.escape(query), "$options": "i"}}
                ]
            }
            
            results = list(self.comments_collection.find(search_filter).limit(max_results))
            
            return [{
                "type": "comment",
                "content": item.get('body', 'No content'),
                "author": item.get('name', 'Unknown')
            } for item in results]
        except Exception as e:
            if self.verbose:
                print(f"Comment search error: {e}")
            return []

    def format_context(self, results, query_type="general"):
        """Format search results into context for RAG"""
        if not results:
            return "", []
        
        context = ""
        sources = []
        
        for item in results:
            item_type = item.get("type")
            
            if item_type == "task":
                context += f"• Task: {item['name']} ({item['progressStatus']})"
                if item.get('assignee') != 'Unassigned':
                    context += f" - assigned to {item['assignee']}"
                context += "\n"
                sources.append("Tasks Database")
                
            elif item_type == "user":
                context += f"• Team Member: {item.get('name', 'Unknown')} ({item.get('role', 'Member')})"
                if item.get('email'):
                    context += f" - {item.get('email')}"
                context += "\n"
                sources.append("User Directory")
                
            elif item_type == "post":
                context += f"• Forum Post: '{item.get('title', 'No Title')}' by {item.get('author', 'Unknown')}\n"
                sources.append(f"Forum by {item.get('author', 'Unknown')}")
                
            elif item_type == "comment":
                context += f"• Comment by {item.get('author', 'Unknown')}\n"
                sources.append(f"Comments by {item.get('author', 'Unknown')}")
        
        return context.strip(), list(set(sources))

    def chat(self, user_query, max_results_each=10, include_metadata=False):
        """Main chat function with integrated RAG"""
        try:
            # Analyze query and search
            intent = self.analyze_query_intent(user_query)
            search_results = self.search_database(user_query, intent, max_results_each)
            context, sources = self.format_context(search_results, intent["type"])
            
            # Build system message
            system_message = """You are MindVerse AI Assistant, a helpful AI for workspace questions.

GUIDELINES:
- Use workspace data directly when provided
- Be specific with names, roles, and details
- Start responses with "Based on your workspace data..." when relevant
- Use natural, conversational language
"""
            
            if context:
                system_message += f"\n\nWORKSPACE DATA:\n{context}\n\nSources: {', '.join(sources)}\n\nUse this data to answer the user's question."
            else:
                system_message += "\n\nNo workspace data found. Provide general guidance."
            
            # Call OpenAI
            response = requests.post(
                self.openai_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-turbo",
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_query}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.3
                }
            )
            
            response.raise_for_status()
            result = response.json()
            answer = result['choices'][0]['message']['content']
            
            # Determine sources used
            sources_used = []
            for item in search_results:
                item_type = item.get("type")
                if item_type == "task":
                    sources_used.append("Tasks Database")
                elif item_type == "user":
                    sources_used.append("Team Directory")
                elif item_type == "post":
                    sources_used.append(f"Forum Posts by {item.get('author', 'Unknown')}")
                elif item_type == "comment":
                    sources_used.append(f"Comments by {item.get('author', 'Unknown')}")
            
            sources_used = list(dict.fromkeys(sources_used))  # Remove duplicates
            
            if include_metadata:
                return {
                    "answer": answer,
                    "sources": sources_used,
                    "has_context": bool(context),
                    "tokens": result.get('usage', {}).get('total_tokens', 0),
                    "intent_detected": intent["type"],
                    "results_found": len(search_results),
                    "filters_applied": intent.get("filters", {})
                }
            else:
                return answer
                
        except Exception as e:
            error_msg = f"Technical issue occurred: {str(e)}. Please try again."
            
            if include_metadata:
                return {
                    "answer": error_msg,
                    "sources": [],
                    "has_context": False,
                    "tokens": 0,
                    "error": str(e)
                }
            else:
                return error_msg

    def close(self):
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()


def clean_response_text(text):
    """Clean response text from markdown formatting"""
    if not text:
        return text
    
    clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)  # *italic*
    clean_text = re.sub(r'#{1,6}\s*', '', clean_text)  # headers
    clean_text = re.sub(r'`([^`]+)`', r'\1', clean_text)  # code
    clean_text = re.sub(r'^[\s]*[-*+]\s*', '• ', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'^\s*\d+\.\s*', '• ', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_text)
    clean_text = re.sub(r'[ \t]+', ' ', clean_text)
    clean_text = re.sub(r'^\s+|\s+$', '', clean_text, flags=re.MULTILINE)
    
    return clean_text.strip()


def initialize_chatbot():
    """Initialize the MindVerse AI chatbot"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        mongo_uri = os.getenv('MONGO_URL')
        
        if not api_key:
            return None, "OPENAI_API_KEY not found in .env file"
        if not mongo_uri:
            return None, "MONGO_URL not found in .env file"
        
        chatbot = MindVerseAI(api_key, mongo_uri, verbose=False)
        return chatbot, None
    except Exception as e:
        return None, str(e)


def handle_chat_request(message, chatbot):
    """Handle chat request using integrated RAG system"""
    try:
        if not chatbot:
            return {
                "success": False,
                "answer": "Chatbot initialization failed. Please check configuration.",
                "sources": [],
                "has_context": False,
                "tokens": 0,
                "error": "No chatbot available"
            }
        
        result = chatbot.chat(
            user_query=message,
            max_results_each=10,
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
            clean_answer = clean_response_text(str(result))
            return {
                "success": True,
                "answer": clean_answer,
                "sources": ["Database"],
                "has_context": True,
                "tokens": 0
            }
            
    except Exception as e:
        return {
            "success": True,
            "answer": f"Technical issue occurred: {str(e)}. Please try again.",
            "sources": [],
            "has_context": False,
            "tokens": 0,
            "error": str(e)
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
    chatbot, error = initialize_chatbot()
    
    try:
        if message == "__GET_STATS__":
            result = handle_stats_request(chatbot)
        elif message == "__HEALTH_CHECK__":
            result = handle_health_check(chatbot)
        else:
            result = handle_chat_request(message, chatbot)
        
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