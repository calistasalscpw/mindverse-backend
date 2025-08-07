import sys
import json
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class MeetingAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        
    def analyze_task_for_meeting(self, task_data):
        """Analyze task and suggest meeting details"""
        try:
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

            # Call OpenAI
            response = requests.post(
                self.openai_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
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
            
            # Try to parse JSON from AI response
            try:
                # Find JSON in the response
                start = ai_response.find('{')
                end = ai_response.rfind('}') + 1
                json_str = ai_response[start:end]
                analysis = json.loads(json_str)
            except:
                # Fallback if JSON parsing fails
                analysis = self.create_fallback_analysis(task_data)
            
            # Add calculated time suggestions
            analysis.update(self.calculate_time_suggestions(task_data))
            
            return {
                "success": True,
                "analysis": analysis,
                "tokens_used": result.get('usage', {}).get('total_tokens', 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": self.create_fallback_analysis(task_data)
            }
    
    def create_fallback_analysis(self, task_data):
        """Create basic meeting analysis if AI fails"""
        status_config = {
            "ToDo": {
                "title": f"Kickoff Meeting - {task_data['name']}",
                "duration": 45,
                "agenda": [
                    "Project overview and objectives",
                    "Role assignments and responsibilities", 
                    "Timeline and milestone planning",
                    "Resource requirements discussion"
                ],
                "purpose": "Plan and initiate the task execution",
                "recommended_discussion_points": [
                    "Define project scope and deliverables",
                    "Assign roles and responsibilities",
                    "Set up communication channels",
                    "Establish timeline and milestones"
                ]
            },
            "In Progress": {
                "title": f"Progress Review - {task_data['name']}",
                "duration": 30,
                "agenda": [
                    "Current progress status update",
                    "Challenges and blockers discussion",
                    "Resource needs assessment",
                    "Next steps planning"
                ],
                "purpose": "Review progress and resolve issues",
                "recommended_discussion_points": [
                    "Technical challenges and solutions",
                    "Resource availability and constraints",
                    "Timeline adjustments if needed",
                    "Quality checkpoints and testing"
                ]
            },
            "Review": {
                "title": f"Quality Review - {task_data['name']}",
                "duration": 60,
                "agenda": [
                    "Work deliverables presentation",
                    "Quality assessment and feedback",
                    "Revision requirements discussion",
                    "Approval process and timeline"
                ],
                "purpose": "Review work quality and approve deliverables",
                "recommended_discussion_points": [
                    "Deliverable quality assessment",
                    "User feedback and requirements",
                    "Performance and optimization",
                    "Documentation and handover"
                ]
            }
        }
        
        config = status_config.get(task_data['progressStatus'], status_config["In Progress"])
        
        return {
            "suggested_title": config["title"],
            "suggested_duration": config["duration"],
            "urgency": "Medium",
            "best_time_of_day": "10:00 AM - 11:00 AM",
            "best_day_suggestion": "Tuesday or Wednesday",
            "agenda": config["agenda"],
            "meeting_purpose": config["purpose"],
            "preparation_notes": "Review task requirements and current progress",
            "success_metrics": "Clear action items assigned and timeline confirmed",
            "recommended_discussion_points": config["recommended_discussion_points"]
        }
    
    def calculate_time_suggestions(self, task_data):
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

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No task data provided"}))
        return
        
    try:
        task_data = json.loads(sys.argv[1])
        analyzer = MeetingAnalyzer()
        result = analyzer.analyze_task_for_meeting(task_data)
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            "success": False, 
            "error": str(e),
            "analysis": {
                "suggested_title": "Team Meeting",
                "suggested_duration": 30,
                "urgency": "Medium"
            }
        }))

if __name__ == "__main__":
    main()