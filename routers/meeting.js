import { Router } from 'express';
import { spawn } from 'child_process';
import path from 'path';
import nodemailer from 'nodemailer';
import Task from '../models/tasks.model.js';
import User from '../models/users.model.js';

const router = Router();

// Middleware to restrict access to Lead/HR only
function requireLeadOrHR(req, res, next) {
  if (!req.user || (!req.user.isLead && !req.user.isHR)) {
    return res.status(403).json({ message: 'Only Lead or HR can schedule meetings.' });
  }
  next();
}

// Call Python script for AI meeting analysis
const callMeetingAnalysis = (taskData) => {
  return new Promise((resolve, reject) => {
    const python = spawn('python', [
      path.join(process.cwd(), 'chatbot', 'meeting_api.py'),
      JSON.stringify(taskData)
    ]);
    
    let dataString = '';
    let errorString = '';

    python.stdout.on('data', (data) => {
      dataString += data.toString();
    });

    python.stderr.on('data', (data) => {
      errorString += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(dataString.trim());
          
          // Validate response structure
          if (result && result.success && result.analysis) {
            resolve(result);
          } else {
            reject(new Error('Invalid Python response structure'));
          }
        } catch (parseError) {
          reject(new Error(`Failed to parse Python response: ${parseError.message}`));
        }
      } else {
        reject(new Error(`Python script exited with code ${code}: ${errorString}`));
      }
    });

    python.on('error', (error) => {
      reject(new Error(`Failed to start Python process: ${error.message}`));
    });
  });
};

// Email transporter configuration
const transporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: "calistasalsa.cpw@gmail.com",
    pass: process.env.GOOGLE_APP_PASSWORD
  }
});

// POST /meetings/analyze-task - Analyze task for AI meeting suggestions
router.post('/analyze-task', requireLeadOrHR, async (req, res) => {
  try {
    const { taskId } = req.body;
    
    // Validate required fields
    if (!taskId) {
      return res.status(400).json({ 
        success: false,
        message: 'Task ID is required' 
      });
    }
    
    // Fetch task with assigned users
    const task = await Task.findById(taskId)
      .populate('assignTo', 'username email')
      .exec();
    
    if (!task) {
      return res.status(404).json({ 
        success: false,
        message: 'Task not found' 
      });
    }

    // Skip analysis for completed tasks
    if (task.progressStatus === 'Done') {
      return res.status(400).json({ 
        success: false,
        message: 'Cannot schedule meeting for completed tasks' 
      });
    }

    // Prepare task data for AI analysis
    const taskData = {
      name: task.name,
      description: task.description || '',
      progressStatus: task.progressStatus,
      dueDate: task.dueDate,
      assignees: task.assignTo.map(user => ({
        username: user.username,
        email: user.email
      }))
    };

    // Call Python AI analysis
    const pythonResult = await callMeetingAnalysis(taskData);
    
    // Prepare response with proper structure
    const response = {
      success: true,
      analysis: pythonResult.analysis,
      source: pythonResult.source || 'openai',
      tokens_used: pythonResult.tokens_used || 0,
      task: {
        id: task._id,
        name: task.name,
        status: task.progressStatus,
        assignees: task.assignTo.map(user => ({
          username: user.username,
          email: user.email
        }))
      }
    };
    
    res.json(response);

  } catch (error) {
    console.error('Meeting analysis error:', error);
    
    res.status(500).json({
      success: false,
      message: 'Failed to analyze task for meeting',
      error: error.message
    });
  }
});

// POST /meetings/schedule - Schedule meeting and send email invitations
router.post('/schedule', requireLeadOrHR, async (req, res) => {
  try {
    const { 
      taskId, 
      meetingTitle, 
      meetingDate, 
      meetingTime, 
      duration, 
      agenda,
      meetingType
    } = req.body;

    // Fetch task with assigned users
    const task = await Task.findById(taskId)
      .populate('assignTo', 'username email')
      .exec();

    if (!task) {
      return res.status(404).json({ 
        success: false,
        message: 'Task not found' 
      });
    }

    // Generate meeting ID and link
    const meetingId = `meeting-${Date.now()}`;
    let meetingLink;
    
    if (meetingType === 'google-meet') {
      meetingLink = `https://meet.google.com/new`;
    } else {
      meetingLink = `${process.env.FRONTEND_URL || 'http://localhost:5173'}/meeting/${meetingId}`;
    }

    // Prepare meeting details
    const meetingDetails = {
      id: meetingId,
      title: meetingTitle,
      date: meetingDate,
      time: meetingTime,
      duration: duration,
      agenda: agenda,
      link: meetingLink,
      taskName: task.name,
      organizer: req.user.username
    };

    // Send email invitations
    let emailStatus = 'Email service unavailable';
    let emailsSent = 0;
    
    try {
      if (process.env.GOOGLE_APP_PASSWORD) {
        const emailPromises = task.assignTo.map(async (assignee) => {
          const emailContent = generateMeetingEmailContent(meetingDetails, assignee.username);
          
          return transporter.sendMail({
            from: `"${req.user.username} - MindVerse" <calistasalsa.cpw@gmail.com>`,
            to: assignee.email,
            subject: `Meeting Scheduled: ${meetingTitle}`,
            html: emailContent
          });
        });

        await Promise.all(emailPromises);
        emailsSent = task.assignTo.length;
        emailStatus = `Emails sent successfully to ${emailsSent} participants`;
        
      } else {
        emailStatus = 'Email configuration missing (GOOGLE_APP_PASSWORD not set)';
      }
      
    } catch (emailError) {
      console.error('Email sending failed:', emailError.message);
      emailStatus = `Email sending failed: ${emailError.message}`;
    }

    res.json({
      success: true,
      message: `Meeting scheduled successfully! ${emailStatus}`,
      meeting: meetingDetails,
      emailStatus: emailStatus,
      assignees: task.assignTo.map(a => ({
        username: a.username,
        email: a.email
      }))
    });

  } catch (error) {
    console.error('Meeting scheduling error:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to schedule meeting',
      error: error.message
    });
  }
});

// Generate HTML email content for meeting invitation
function generateMeetingEmailContent(meeting, recipientName) {
  const isGoogleMeet = meeting.link.includes('meet.google.com');
  
  return `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 20px;">
      <div style="background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h2 style="color: #8F1383; text-align: center; margin-bottom: 10px;">📅 Meeting Invitation</h2>
        
        <p style="font-size: 16px; color: #333;">Hello <strong>${recipientName}</strong>,</p>
        
        <p style="color: #666; line-height: 1.6;">
          You've been invited to a meeting regarding the task: <strong>${meeting.taskName}</strong>
        </p>
        
        <div style="background-color: #f8f9fa; padding: 25px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #8F1383;">
          <h3 style="margin-top: 0; color: #432E54; font-size: 20px;">${meeting.title}</h3>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
            <div>
              <p style="margin: 8px 0;"><strong>📅 Date:</strong> ${new Date(meeting.date).toDateString()}</p>
              <p style="margin: 8px 0;"><strong>⏰ Time:</strong> ${meeting.time}</p>
            </div>
            <div>
              <p style="margin: 8px 0;"><strong>⏱️ Duration:</strong> ${meeting.duration} minutes</p>
              <p style="margin: 8px 0;"><strong>👤 Organizer:</strong> ${meeting.organizer}</p>
            </div>
          </div>
          
          ${meeting.agenda ? `
            <div style="margin-top: 20px;">
              <h4 style="color: #432E54; margin-bottom: 10px;">📋 Agenda:</h4>
              <div style="background-color: white; padding: 15px; border-radius: 6px; white-space: pre-line; line-height: 1.6;">
${meeting.agenda}
              </div>
            </div>
          ` : ''}
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
          <a href="${meeting.link}" 
             style="background: linear-gradient(135deg, #8F1383, #432E54); 
                    color: white; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 25px; 
                    display: inline-block;
                    font-weight: bold;
                    font-size: 16px;
                    box-shadow: 0 4px 15px rgba(143, 19, 131, 0.3);
                    transition: transform 0.2s;">
            ${isGoogleMeet ? '🎥 Join Google Meet' : '📱 Join MindVerse Meeting'}
          </a>
        </div>
        
        <div style="background-color: #f0f9ff; padding: 15px; border-radius: 6px; margin: 20px 0;">
          <p style="margin: 5px 0; color: #374151;"><strong>Meeting Link:</strong></p>
          <p style="margin: 5px 0;">
            <a href="${meeting.link}" style="color: #3B82F6; word-break: break-all;">${meeting.link}</a>
          </p>
          ${isGoogleMeet ? `
            <p style="margin: 10px 0 5px 0; color: #6B7280; font-size: 14px;">
              💡 <strong>Tip:</strong> This will open Google Meet in your browser. Make sure you're logged into your Google account.
            </p>
          ` : ''}
        </div>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        
        <div style="text-align: center;">
          <p style="color: #9CA3AF; font-size: 12px; margin: 5px 0;">
            This meeting was scheduled through MindVerse Task Management System
          </p>
          <p style="color: #9CA3AF; font-size: 12px; margin: 5px 0;">
            Need help? Contact your team administrator
          </p>
        </div>
      </div>
    </div>
  `;
}

export default router;