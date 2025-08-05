import requests
import json
from pymongo import MongoClient
from datetime import datetime
import re

class MindVerseAI:
    def __init__(self, deepseek_api_key, mongo_uri=None, verbose=False):
        self.api_key = deepseek_api_key
        self.verbose = verbose
        
        # MongoDB Atlas connection
        if mongo_uri is None:
            mongo_uri = "mongodb+srv://Python:K60wVjdLcDruClvl@cluster0.fbol8bw.mongodb.net/"
        
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
        
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"

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
        
        # Task-specific intents with context mapping
        if any(word in query_lower for word in ['task', 'tugas', 'pekerjaan', 'kerja']):
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
                # Use exact match for "ToDo" (without space based on database structure)
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
            if intent["type"] == "tasks":
                return self.search_tasks_enhanced(query, intent["filters"], max_results)
            elif intent["type"] == "users":
                return self.search_users(query, max_results)
            elif intent["type"] == "posts":
                return self.search_posts(query, max_results)
            elif intent["type"] == "comments":
                return self.search_comments(query, max_results)
            else:
                # General search across all collections
                results = []
                results.extend(self.search_tasks_enhanced(query, {}, 3))
                results.extend(self.search_posts(query, 2))
                results.extend(self.search_comments(query, 2))
                return results[:max_results]
                
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
        
        if query_type == "tasks":
            context = "Task List:\n"
            for item in results:
                if item.get("type") == "task":
                    task_name = item['name']
                    status = item['progressStatus']
                    description = item.get('description', '').strip()
                    
                    # Start with basic format
                    task_line = f"• {task_name} ({status})"
                    
                    # Add meaningful description only
                    if (description and 
                        description not in ['N/A', 'This is a test task.', 'This is a test task. Hello', 'just test', ''] and
                        len(description) > 5):
                        # Clean and shorten description
                        clean_desc = description.replace('Team needs to tidy up documentation of the project code', 'Team needs to tidy up project code docs')
                        clean_desc = clean_desc.replace("Don't forget to register diploy", "Don't forget to register diploy")
                        
                        if len(clean_desc) > 50:
                            clean_desc = clean_desc[:50] + "..."
                        task_line += f" - {clean_desc}"
                    
                    context += task_line + "\n"
        else:
            # General formatting for mixed results
            for item in results:
                if item.get("type") == "task":
                    context += f"• {item['name']} ({item['progressStatus']})\n"
                elif item.get("type") == "post":
                    context += f"• Post: {item.get('title', 'No Title')}\n"
                elif item.get("type") == "comment":
                    content = item.get('content', 'No content')
                    if len(content) > 40:
                        content = content[:40] + "..."
                    context += f"• Comment: {content}\n"
                elif item.get("type") == "user":
                    context += f"• User: {item.get('name', 'No name')}\n"
        
        return context.strip() 

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
            search_filter = {
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"body": {"$regex": query, "$options": "i"}}
                ]
            }
            
            results = list(self.posts_collection.find(search_filter).limit(max_results))
            
            formatted_results = []
            for item in results:
                author_info = item.get('author', 'Unknown')
                
                if hasattr(author_info, '__str__') and len(str(author_info)) > 20:
                    try:
                        user = self.users_collection.find_one({"_id": author_info})
                        if user:
                            author_info = user.get('username', user.get('name', 'Unknown'))
                        else:
                            author_info = 'Unknown'
                    except:
                        author_info = 'Unknown'
                
                formatted_result = {
                    "type": "post",
                    "title": item.get('title', 'No Title'),
                    "content": item.get('body', ''),
                    "author": str(author_info)
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
            
            # Format context
            context = self.format_context_from_results(search_results, intent["type"])
            
            # Enhanced system message with natural conversation style
            system_message = """You are MindVerse AI Assistant, a friendly and helpful AI that assists users with their workspace. Be conversational, natural, and helpful.

IMPORTANT RESPONSE STYLE:
- Write in a natural, conversational tone
- Don't sound robotic or overly formal
- Be helpful and friendly
- Keep responses concise but informative
- Use casual language when appropriate

For FORUM/POST questions:
- When user asks about posts like "dev jokes" or "monday activity"
- Give a natural response like: "I found a post called 'Dev Jokes' by Mr. Python! It's got a funny JavaScript joke about broken promises."
- Include the actual content/joke if it's short and relevant
- Be enthusiastic about sharing interesting content

For TASK questions:  
- Use natural language: "Here are the tasks currently in progress:" followed by clean bullet points
- Add friendly touches like "Let me know if you need more details!"

For ASSIGNMENT questions:
- Answer directly: "The Register Deploy task is being handled by John Smith" 
- Or: "Looks like no one is assigned to that task yet"

FORMATTING:
- Use proper line breaks (\n) between bullet points
- Keep it clean but conversational
- Add helpful context or suggestions when relevant

Be human-like in your responses while staying professional and helpful."""

            if context:
                system_message += f"\n\nDatabase data (use this data to answer):\n{context}"
            else:
                system_message += "\n\nNo specific data found in the database for this query."
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_query}
            ]
            
            # Call DeepSeek API
            response = requests.post(
                self.deepseek_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "max_tokens": 1500,
                    "temperature": 0.3  # Lower temperature for more consistent responses
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            answer = result['choices'][0]['message']['content']
            
            # Determine sources used
            sources_used = []
            if search_results:
                result_types = set(item.get("type", "unknown") for item in search_results)
                if "task" in result_types:
                    sources_used.append("Tasks")
                if "post" in result_types:
                    sources_used.append("Posts")
                if "comment" in result_types:
                    sources_used.append("Comments")
                if "user" in result_types:
                    sources_used.append("Users")
            
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
    DEEPSEEK_API_KEY = "sk-91d6a95371124300b4d9d1c26969718e"
    
    try:
        chatbot = MindVerseAI(DEEPSEEK_API_KEY, verbose=True)
        chatbot.interactive_chat()
        
    except Exception as e:
        print(f"Failed to initialize: {e}")
    finally:
        try:
            chatbot.close()
        except:
            pass

if __name__ == "__main__":
    main()