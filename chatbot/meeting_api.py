import sys
import json
import os
import requests
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

def calculate_time_suggestions(task_data):
    """Calculate optimal meeting times based on deadline"""
    suggestions = {}
    
    if task_data.get('dueDate'):
        try:
            due_date = datetime.fromisoformat(task_data['dueDate'].replace('Z', '+00:00'))
            now = datetime.now()
            days_until_due = (due_date - now).days
            
            if days_until_due <= 3:
                suggestions["urgency"] = "High"
                suggestions["suggested_date"] = (now + timedelta(days=1)).strftime('%Y-%m-%d')
            elif days_until_due <= 7:
                suggestions["urgency"] = "Medium" 
                suggestions["suggested_date"] = (now + timedelta(days=2)).strftime('%Y-%m-%d')
            else:
                suggestions["urgency"] = "Low"
                suggestions["suggested_date"] = (now + timedelta(days=3)).strftime('%Y-%m-%d')
                
        except:
            suggestions["suggested_date"] = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    else:
        suggestions["suggested_date"] = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        
    return suggestions

def analyze_task_for_meeting(task_data):
    """Analyze task and suggest meeting details using OpenAI API"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise Exception("OPENAI_API_KEY not found in .env file")
    
    openai_url = "https://api.openai.com/v1/chat/completions"
    
    # Prepare system message for meeting analysis
    system_message = f"""You are a smart meeting scheduler AI. Based on the task information provided, suggest optimal meeting details.

TASK INFORMATION:
- Task Name: {task_data['name']}
- Description: {task_data.get('description', 'No description')}
- Current Status: {task_data['progressStatus']}
- Due Date: {task_data.get('dueDate', 'No deadline')}
- Assignees: {len(task_data.get('assignees', []))} people

ANALYSIS REQUIREMENTS:
1. Suggest meeting title (professional, task-focused)
2. Estimate meeting duration (15-120 minutes)
3. Suggest optimal meeting time (consider urgency)
4. Create focused agenda (3-5 key points)
5. Determine meeting urgency (High/Medium/Low)
6. Suggest best day of week for meeting
7. Recommend specific discussion points based on task content
8. Suggest preparation requirements

RESPONSE FORMAT (JSON only):
{{
    "suggested_title": "Clear, professional meeting title",
    "suggested_duration": 60,
    "urgency": "Medium",
    "best_time_of_day": "10:00 AM - 11:00 AM",
    "best_day_suggestion": "Tuesday or Wednesday",
    "agenda": [
        "Review current task progress",
        "Identify blockers and challenges", 
        "Assign specific action items",
        "Set next milestone dates"
    ],
    "meeting_purpose": "Brief description of why this meeting is needed",
    "preparation_notes": "What participants should prepare",
    "success_metrics": "How to measure if meeting was successful",
    "recommended_discussion_points": [
        "Specific technical point relevant to task",
        "Resource allocation discussion",
        "Timeline and milestone review",
        "Quality assurance checkpoints"
    ]
}}

Based on the task status '{task_data['progressStatus']}', tailor your suggestions appropriately:
- ToDo: Planning and kickoff focused, discuss requirements, scope, timeline
- In Progress: Status review and problem solving, blockers, resource needs
- Review: Quality check and approval process, deliverables assessment

For task '{task_data['name']}' with description '{task_data.get('description', 'No description')}', provide specific discussion points that would be most valuable for the team to address."""

    # Call OpenAI API
    response = requests.post(
        openai_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": "Please analyze this task and provide meeting suggestions."}
            ],
            "max_tokens": 800,
            "temperature": 0.3
        }
    )
    
    response.raise_for_status()
    result = response.json()
    
    # Extract and parse the JSON response
    ai_response = result['choices'][0]['message']['content']
    
    # Find JSON in the response
    start = ai_response.find('{')
    end = ai_response.rfind('}') + 1
    json_str = ai_response[start:end]
    analysis = json.loads(json_str)
    
    # Add calculated time suggestions
    analysis.update(calculate_time_suggestions(task_data))
    
    return {
        "success": True,
        "analysis": analysis,
        "tokens_used": result.get('usage', {}).get('total_tokens', 0)
    }

def handle_analysis_request(task_data):
    """Handle meeting analysis request"""
    try:
        result = analyze_task_for_meeting(task_data)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analysis": {}
        }

def main():
    """Main function to handle requests from Node.js"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "No task data provided",
            "analysis": {}
        }))
        return

    try:
        # Parse task data from command line argument
        task_data = json.loads(sys.argv[1])
        
        # Handle analysis request
        result = handle_analysis_request(task_data)
        
        # Output result as JSON
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "analysis": {}
        }))

if __name__ == "__main__":
    main()