import sys
import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Try to import the actual meeting analyzer
try:
    from meeting_analyzer import MeetingAnalyzer
    HAS_REAL_ANALYZER = True
except ImportError:
    HAS_REAL_ANALYZER = False

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

def initialize_analyzer():
    """Initialize the Meeting Analyzer with OpenAI connection"""
    if not HAS_REAL_ANALYZER:
        return None, "MeetingAnalyzer module not available"
    
    try:
        # Read from .env file
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            return None, "OPENAI_API_KEY not found in .env file"
        
        # Initialize analyzer
        analyzer = MeetingAnalyzer()
        return analyzer, None
    except Exception as e:
        return None, str(e)

def handle_analysis_request(task_data, analyzer):
    """Handle meeting analysis request"""
    try:
        # Always try real analyzer first if available
        if analyzer:
            # Use real analyzer
            result = analyzer.analyze_task_for_meeting(task_data)
            
            if result.get('success'):
                analysis = result.get('analysis', {})
                
                return {
                    "success": True,
                    "analysis": analysis,
                    "tokens_used": result.get("tokens_used", 0),
                    "source": "openai"
                }
            else:
                # AI failed, use enhanced fallback
                return get_enhanced_fallback_analysis(task_data, result.get('error', 'Unknown error'))
        
        # No analyzer available, use fallback
        else:
            return get_enhanced_fallback_analysis(task_data, "OpenAI API not available")
            
    except Exception as e:
        # On error, provide enhanced fallback
        return get_enhanced_fallback_analysis(task_data, str(e))

def get_enhanced_fallback_analysis(task_data, error_msg):
    """Provide enhanced fallback analysis for different task types"""
    task_name = task_data.get('name', 'Task')
    task_status = task_data.get('progressStatus', 'In Progress')
    task_description = task_data.get('description', '')
    
    # Status-based configuration
    status_config = {
        "ToDo": {
            "title": f"Kickoff Meeting - {task_name}",
            "duration": 45,
            "agenda": [
                "Project overview and objectives",
                "Requirements clarification and scope",
                "Role assignments and responsibilities",
                "Timeline and milestone planning",
                "Resource allocation discussion"
            ],
            "purpose": f"Plan and initiate the execution of {task_name}",
            "discussion_points": [
                f"Define clear requirements for {task_name}",
                "Establish project scope and boundaries",
                "Assign team roles and responsibilities",
                "Set up development and communication workflow",
                "Plan testing and quality assurance approach"
            ]
        },
        "In Progress": {
            "title": f"Progress Review - {task_name}",
            "duration": 30,
            "agenda": [
                "Current progress status update",
                "Technical challenges and blockers",
                "Resource needs and availability",
                "Timeline review and adjustments",
                "Next sprint planning"
            ],
            "purpose": f"Review progress and resolve issues for {task_name}",
            "discussion_points": [
                f"Technical implementation progress of {task_name}",
                "Performance metrics and quality indicators",
                "Resource constraints and optimization",
                "Risk mitigation and contingency planning",
                "User feedback integration and iteration"
            ]
        },
        "Review": {
            "title": f"Quality Review - {task_name}",
            "duration": 60,
            "agenda": [
                "Deliverable presentation and demo",
                "Quality assessment and testing results",
                "Code review and technical evaluation",
                "User acceptance criteria verification",
                "Deployment and go-live planning"
            ],
            "purpose": f"Review and approve deliverables for {task_name}",
            "discussion_points": [
                f"Quality assessment of {task_name} deliverables",
                "User experience and interface evaluation",
                "Performance benchmarks and optimization",
                "Documentation completeness and accuracy",
                "Deployment strategy and rollback procedures"
            ]
        }
    }
    
    config = status_config.get(task_status, status_config["In Progress"])
    
    # Enhance discussion points based on task description
    enhanced_points = config["discussion_points"].copy()
    if task_description and len(task_description) > 10:
        if "ai" in task_description.lower() or "artificial intelligence" in task_description.lower():
            enhanced_points.append("AI model training and optimization strategies")
            enhanced_points.append("Data quality and algorithm performance metrics")
        elif "ui" in task_description.lower() or "interface" in task_description.lower():
            enhanced_points.append("User interface design and usability testing")
            enhanced_points.append("Responsive design and accessibility compliance")
        elif "api" in task_description.lower():
            enhanced_points.append("API design patterns and integration testing")
            enhanced_points.append("Authentication and security implementation")
    
    # Calculate urgency based on due date
    urgency = "Medium"
    if task_data.get('dueDate'):
        # Simple urgency calculation
        urgency = "High"  # If there's a due date, consider it high priority
    
    return {
        "success": True,
        "analysis": {
            "suggested_title": config["title"],
            "suggested_duration": config["duration"],
            "urgency": urgency,
            "best_time_of_day": "10:00 AM - 11:00 AM",
            "best_day_suggestion": "Tuesday or Wednesday",
            "agenda": config["agenda"],
            "meeting_purpose": config["purpose"],
            "preparation_notes": f"Review {task_name} requirements and prepare status updates",
            "success_metrics": "Clear action items assigned with timeline and responsibilities",
            "recommended_discussion_points": enhanced_points
        },
        "source": "enhanced_fallback",
        "fallback_reason": error_msg,
        "tokens_used": 0
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
        
        # Initialize analyzer
        analyzer, error = initialize_analyzer()
        
        if error:
            print(f"Analyzer initialization warning: {error}", file=sys.stderr)
        
        # Handle analysis request
        result = handle_analysis_request(task_data, analyzer)
        
        # Output result as JSON
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "analysis": {
                "suggested_title": "Team Meeting",
                "suggested_duration": 30,
                "urgency": "Medium",
                "meeting_purpose": "Coordinate team activities"
            }
        }))
    
    finally:
        try:
            if 'analyzer' in locals() and analyzer:
                # Close any connections if needed
                pass
        except:
            pass

if __name__ == "__main__":
    main()