import requests
import json
from pymongo import MongoClient
from datetime import datetime
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MindVerseAI:
    def __init__(self, openai_api_key=None, mongo_uri=None, verbose=False):
        # Read from .env file if not provided
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.verbose = verbose
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY in .env file or pass it as parameter.")
        
        # MongoDB Atlas connection
        if mongo_uri is None:
            mongo_uri = os.getenv('MONGO_URL')
            
        if not mongo_uri:
            raise ValueError("MongoDB URI is required. Please set MONGO_URL in .env file or pass it as parameter.")
        
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
        
        # OpenAI API URL
        self.openai_url = "https://api.openai.com/v1/chat/completions"

    def get_stats(self):
        """Get database statistics"""
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
        query_lower = query.lower()
        intent = {
            "type": "general",
            "filters": {},
            "specific_search": False
        }
        
        # Check for specific keywords in forum posts first
        # This will help catch questions that might have answers in the forum
        forum_keywords = ['pompia', 'tutorial', 'wifi', 'maintenance', 'lunch', 'team']
        if any(keyword in query_lower for keyword in forum_keywords):
            intent["type"] = "posts"
            intent["specific_search"] = True
        
        # Task-specific intents with context mapping
        elif any(word in query_lower for word in ['task', 'tugas', 'pekerjaan', 'kerja']):
            intent["type"] = "tasks"
            
            # Map different ways to ask about "In Progress" status
            if any(word in query_lower for word in [
                'in progress', 'sedang berjalan', 'progress', 'sedang dikerjakan', 
                'lagi dikerjakan', 'ongoing', 'berlangsung'
            ]):
                intent["filters"]["progressStatus"] = "In Progress"
                intent["specific_search"] = True
                
            # Map different ways to ask about "ToDo" status  
            elif any(word in query_lower for word in [
                'todo', 'to do', 'belum', 'harus dikerjakan', 'perlu dikerjakan',
                'belum selesai', 'belum mulai', 'belum dikerjakan', 'pending',
                'need to be done', 'not started', 'waiting'
            ]):
                intent["filters"]["progressStatus"] = "ToDo"
                intent["specific_search"] = True
                
            # Map different ways to ask about "Done" status
            elif any(word in query_lower for word in [
                'done', 'selesai', 'completed', 'finished', 'sudah selesai',
                'sudah dikerjakan', 'complete', 'telah selesai'
            ]):
                intent["filters"]["progressStatus"] = "Done"
                intent["specific_search"] = True
                
            # Map different ways to ask about "Review" status
            elif any(word in query_lower for word in [
                'review', 'checking', 'perlu review', 'sedang direview',
                'butuh review', 'for review', 'under review'
            ]):
                intent["filters"]["progressStatus"] = "Review"
                intent["specific_search"] = True
                
        # User-specific intents
        elif any(word in query_lower for word in ['user', 'member', 'team', 'orang', 'people']):
            intent["type"] = "users"
            
        # Post-specific intents
        elif any(word in query_lower for word in ['post', 'discussion', 'forum', 'diskusi']):
            intent["type"] = "posts"
            
        # Comment-specific intents
        elif any(word in query_lower for word in ['comment', 'komentar']):
            intent["type"] = "comments"
            
        return intent

    def search_with_intent(self, query, intent, max_results=10):
        try:
            # Always search posts first for any query that might have forum content
            all_results = []
            
            # Priority 1: Search posts first (forum is important!)
            post_results = self.search_posts(query, max_results // 2)
            all_results.extend(post_results)
            
            if intent["type"] == "tasks":
                task_results = self.search_tasks_enhanced(query, intent["filters"], max_results)
                all_results.extend(task_results)
            elif intent["type"] == "users":
                user_results = self.search_users(query, max_results)
                all_results.extend(user_results)
            elif intent["type"] == "posts":
                # Already searched above, but get more results
                additional_posts = self.search_posts(query, max_results)
                all_results = additional_posts  # Replace with more comprehensive search
            elif intent["type"] == "comments":
                comment_results = self.search_comments(query, max_results)
                all_results.extend(comment_results)
            else:
                # General search - comprehensive across all collections with posts priority
                all_results.extend(self.search_tasks_enhanced(query, {}, 2))
                all_results.extend(self.search_comments(query, 2))
                all_results.extend(self.search_users(query, 2))
            
            if self.verbose:
                print(f"Total search results found: {len(all_results)}")
                for result in all_results:
                    print(f"  - {result.get('type', 'unknown')}: {result.get('title', result.get('name', 'N/A'))}")
            
            return all_results[:max_results]
                
        except Exception as e:
            if self.verbose:
                print(f"Search error: {e}")
            return []

    def search_tasks_enhanced(self, query, additional_filters={}, max_results=10):
        """Enhanced task search with correct field names and specific filters"""
        try:
            # If we have specific status filter, use it
            if additional_filters:
                search_filter = additional_filters
                if self.verbose:
                    print(f"Searching tasks with filter: {search_filter}")
            else:
                # General text search using correct field names
                search_filter = {
                    "$or": [
                        {"name": {"$regex": query, "$options": "i"}},
                        {"description": {"$regex": query, "$options": "i"}}
                    ]
                }
            
            results = list(self.tasks_collection.find(search_filter).limit(max_results))
            
            if self.verbose:
                print(f"Found {len(results)} tasks")
                for task in results:
                    print(f"  - {task.get('name', 'N/A')}: '{task.get('progressStatus', 'N/A')}'")
            
            formatted_results = []
            for item in results:
                # Handle assignTo field safely - look up actual user names if possible
                assignee_names = []
                if item.get('assignTo'):
                    for assignee_id in item.get('assignTo', []):
                        if assignee_id:
                            # Try to find user name from users collection
                            try:
                                user = self.users_collection.find_one({"_id": assignee_id})
                                if user:
                                    assignee_names.append(user.get('username', user.get('name', 'Unknown User')))
                                else:
                                    assignee_names.append('Unknown User')
                            except:
                                assignee_names.append('Unknown User')
                
                formatted_result = {
                    "type": "task",
                    "name": item.get('name', 'Untitled Task'),
                    "progressStatus": item.get('progressStatus', 'No status'),
                    "description": item.get('description', ''),
                    "assignee": ', '.join(assignee_names) if assignee_names else 'Unassigned',
                    "due_date": item.get('dueDate', 'No deadline'),
                    "created_at": item.get('createdAt', ''),
                    "updated_at": item.get('updatedAt', '')
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            if self.verbose:
                print(f"Task search error: {e}")
            return []

    def format_context_from_results(self, results, query_type="general"):
        if not results:
            return ""
        
        context = ""
        source_info = []
        
        if query_type == "tasks":
            context = "Task Information:\n"
            for item in results:
                if item.get("type") == "task":
                    task_name = item['name']
                    status = item['progressStatus']
                    assignee = item.get('assignee', 'Unassigned')
                    description = item.get('description', '').strip()
                    
                    # Build task line with source info
                    task_line = f"• {task_name} ({status})"
                    if assignee != 'Unassigned':
                        task_line += f" - assigned to {assignee}"
                    
                    # Add meaningful description only
                    if (description and 
                        description not in ['N/A', 'This is a test task.', 'This is a test task. Hello', 'just test', ''] and
                        len(description) > 5):
                        clean_desc = description.replace('Team needs to tidy up documentation of the project code', 'Team needs to tidy up project code docs')
                        if len(clean_desc) > 50:
                            clean_desc = clean_desc[:50] + "..."
                        task_line += f" - {clean_desc}"
                    
                    context += task_line + "\n"
                    source_info.append("Tasks Database")
                    
        elif query_type == "posts":
            context = "Forum Posts:\n"
            for item in results:
                if item.get("type") == "post":
                    title = item.get('title', 'Untitled Post')
                    author = item.get('author', 'Unknown')
                    content = item.get('content', '')[:100] + "..." if len(item.get('content', '')) > 100 else item.get('content', '')
                    
                    context += f"• Post '{title}' by {author}\n"
                    if content.strip():
                        context += f"  Content: {content}\n"
                    source_info.append(f"Forum by {author}")
                    
        elif query_type == "users":
            context = "Team Members:\n"
            for item in results:
                if item.get("type") == "user":
                    name = item.get('name', 'Unknown')
                    role = item.get('role', 'No role specified')
                    email = item.get('email', '')
                    
                    context += f"• {name}"
                    if role and role != 'No role specified':
                        context += f" ({role})"
                    if email:
                        context += f" - {email}"
                    context += "\n"
                    source_info.append("User Directory")
                    
        else:
            # General formatting for mixed results
            for item in results:
                if item.get("type") == "task":
                    context += f"• Task: {item['name']} ({item['progressStatus']})\n"
                    source_info.append("Tasks Database")
                elif item.get("type") == "post":
                    author = item.get('author', 'Unknown')
                    context += f"• Forum Post: {item.get('title', 'No Title')} by {author}\n"
                    source_info.append(f"Forum by {author}")
                elif item.get("type") == "comment":
                    author = item.get('author', 'Unknown')
                    content = item.get('content', 'No content')
                    if len(content) > 40:
                        content = content[:40] + "..."
                    context += f"• Comment by {author}: {content}\n"
                    source_info.append(f"Comments by {author}")
                elif item.get("type") == "user":
                    context += f"• Team Member: {item.get('name', 'No name')}\n"
                    source_info.append("User Directory")
        
        # Return both context and source info
        return context.strip(), list(set(source_info)) 

    def search_comments(self, query, max_results=5):
        try:
            search_filter = {
                "$or": [
                    {"body": {"$regex": query, "$options": "i"}},
                    {"name": {"$regex": query, "$options": "i"}}
                ]
            }
            
            results = list(self.comments_collection.find(search_filter).limit(max_results))
            
            formatted_results = []
            for item in results:
                formatted_result = {
                    "type": "comment",
                    "content": item.get('body', 'No content'),
                    "author": item.get('name', 'Unknown'),
                    "email": item.get('email', '')
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception:
            return []

    def search_posts(self, query, max_results=5):
        try:
            # Enhanced search for posts with better field matching
            search_filter = {
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"body": {"$regex": query, "$options": "i"}}
                ]
            }
            
            results = list(self.posts_collection.find(search_filter).limit(max_results))
            
            if self.verbose:
                print(f"Found {len(results)} posts for query: {query}")
            
            formatted_results = []
            for item in results:
                # Get author information
                author_info = item.get('author', 'Unknown')
                
                # If author is ObjectId, try to get username from users collection
                if hasattr(author_info, '__str__') and len(str(author_info)) > 20:
                    try:
                        from bson import ObjectId
                        if isinstance(author_info, ObjectId):
                            user = self.users_collection.find_one({"_id": author_info})
                            if user:
                                author_info = user.get('username', user.get('name', 'Unknown User'))
                            else:
                                author_info = 'Unknown User'
                    except:
                        author_info = 'Unknown User'
                
                formatted_result = {
                    "type": "post",
                    "title": item.get('title', 'No Title'),
                    "content": item.get('body', ''),
                    "author": str(author_info),
                    "created_at": item.get('createdAt', ''),
                    "raw_data": item  # Keep raw data for debugging
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            if self.verbose:
                print(f"Post search error: {e}")
            return []

    def search_users(self, query, max_results=5):
        try:
            search_filter = {
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}}
                ]
            }
            
            results = list(self.users_collection.find(search_filter).limit(max_results))
            
            formatted_results = []
            for item in results:
                formatted_result = {
                    "type": "user",
                    "name": item.get('name', 'User'),
                    "email": item.get('email', ''),
                    "role": item.get('role', 'No Role')
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception:
            return []

    def chat(self, user_query, max_results_each=10, include_metadata=False):
        try:
            # Analyze query intent
            intent = self.analyze_query_intent(user_query)
            
            if self.verbose:
                print(f"Intent detected: {intent}")
            
            # Search based on intent
            search_results = self.search_with_intent(user_query, intent, max_results_each)
            
            # Format context and get source information
            context_result = self.format_context_from_results(search_results, intent["type"])
            if isinstance(context_result, tuple):
                context, detailed_sources = context_result
            else:
                context = context_result
                detailed_sources = []
            
            # Enhanced system message with natural conversation style and source attribution
            system_message = """You are MindVerse AI Assistant, a knowledgeable and friendly AI that helps users with their workspace questions. Be conversational, professional, and natural in your responses.

RESPONSE GUIDELINES:
- If you find relevant data in the workspace, start with clear source attribution
- If no workspace data is found, directly provide helpful general information without apologizing
- Never start with "I'm sorry, but I couldn't find..." - just be helpful
- Use natural phrases like "Based on your forum posts...", "Looking at your task database..." when you have data
- Be specific about sources when possible (e.g., "According to Fitra's forum post...")
- After providing information, feel free to add helpful context
- Keep responses professional but friendly and conversational
- Use proper formatting with line breaks between different sections

WHEN YOU HAVE WORKSPACE DATA:
- "Based on your task database, I can see that..."
- "Looking at the forum posts, I found that Fitra mentioned..."  
- "According to your team directory..."
- "From your project discussions..."

WHEN YOU DON'T HAVE WORKSPACE DATA:
- Just provide helpful general information directly
- You can mention it's general knowledge if relevant
- Be naturally helpful without mentioning database limitations

RESPONSE STRUCTURE:
1. Lead with the most relevant information (workspace or general)
2. Present information clearly and naturally
3. Add helpful context or suggestions if relevant
4. Keep it conversational and engaging

Be helpful and engaging while maintaining professionalism."""

            if context:
                system_message += f"\n\nDATA FROM YOUR WORKSPACE:\n{context}\n\nDetailed Sources: {', '.join(detailed_sources) if detailed_sources else 'Internal Database'}"
            else:
                system_message += f"\n\nNo specific workspace data found for this query. Provide helpful general information directly without mentioning database limitations."
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_query}
            ]
            
            # Call OpenAI API
            response = requests.post(
                self.openai_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",  # Using GPT-4
                    "messages": messages,
                    "max_tokens": 1500,
                    "temperature": 0.3  # Lower temperature for more consistent responses
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            answer = result['choices'][0]['message']['content']
            
            # Determine sources used with more detail
            sources_used = []
            if search_results:
                for item in search_results:
                    item_type = item.get("type", "unknown")
                    if item_type == "task":
                        sources_used.append("Tasks Database")
                    elif item_type == "post":
                        author = item.get('author', 'Unknown')
                        sources_used.append(f"Forum Posts by {author}")
                    elif item_type == "comment":
                        author = item.get('author', 'Unknown')
                        sources_used.append(f"Comments by {author}")
                    elif item_type == "user":
                        sources_used.append("Team Directory")
                
                # Remove duplicates while preserving order
                sources_used = list(dict.fromkeys(sources_used))
            
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
            error_msg = "I'm experiencing technical difficulties. Please try again."
            if self.verbose:
                error_msg += f" Error: {str(e)}"
            
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

    def interactive_chat(self):
        """Interactive mode for testing"""
        print("MindVerse AI Assistant")
        print("Type 'quit' to exit, 'stats' for database info")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                elif user_input.lower() == 'stats':
                    stats = self.get_stats()
                    print(f"\nDatabase Stats:")
                    print(f"Comments: {stats.get('comments', 0)}")
                    print(f"Posts: {stats.get('posts', 0)}")
                    print(f"Tasks: {stats.get('tasks', 0)}")
                    print(f"Users: {stats.get('users', 0)}")
                    print(f"Total: {stats.get('total', 0)}")
                    continue
                
                elif not user_input:
                    continue
                
                # Get response with metadata for testing
                result = self.chat(user_input, include_metadata=True)
                
                print(f"\nAssistant: {result['answer']}")
                
                if self.verbose:
                    print(f"\n[Debug Info]")
                    print(f"Intent: {result.get('intent_detected', 'unknown')}")
                    print(f"Results found: {result.get('results_found', 0)}")
                    print(f"Sources: {', '.join(result.get('sources', []))}")
                    print(f"Filters applied: {result.get('filters_applied', {})}")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    def close(self):
        """Close database connection"""
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()

def main():
    # Read from .env file automatically
    try:
        chatbot = MindVerseAI(verbose=True)
        chatbot.interactive_chat()
        
    except Exception as e:
        print(f"Failed to initialize: {e}")
        print("Make sure your .env file contains OPENAI_API_KEY and MONGO_URL")
    finally:
        try:
            chatbot.close()
        except:
            pass

if __name__ == "__main__":
    main()