import { Router } from 'express';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const router = Router();

// Get current directory for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to Python chatbot script
const CHATBOT_SCRIPT_PATH = path.join(__dirname, '..', 'chatbot', 'chatbot_api.py');

// Function to call Python chatbot
const callPythonChatbot = (message) => {
    return new Promise((resolve, reject) => {
        const python = spawn('python', [CHATBOT_SCRIPT_PATH, message]);
        
        let dataString = '';
        let errorString = '';

        python.stdout.on('data', (data) => {
            dataString += data.toString();
        });

        python.stderr.on('data', (data) => {
            errorString += data.toString();
            console.error('Python stderr:', data.toString()); // Debug logging
        });

        python.on('close', (code) => {
            console.log(`Python script exited with code: ${code}`); // Debug logging
            console.log('Python stdout:', dataString); // Debug logging
            
            if (code === 0) {
                try {
                    const result = JSON.parse(dataString.trim());
                    console.log('Parsed Python result:', result); // Debug logging
                    resolve(result);
                } catch (parseError) {
                    console.error('Parse error:', parseError); // Debug logging
                    reject(new Error(`Failed to parse Python response: ${parseError.message}`));
                }
            } else {
                reject(new Error(`Python script exited with code ${code}: ${errorString}`));
            }
        });

        python.on('error', (error) => {
            console.error('Python process error:', error); // Debug logging
            reject(new Error(`Failed to start Python process: ${error.message}`));
        });
    });
};

// POST /chatbot/chat - Main chat endpoint
router.post('/chat', async (req, res) => {
    try {
        const { message } = req.body;
        console.log('Received message:', message); // Debug logging

        if (!message || typeof message !== 'string' || message.trim().length === 0) {
            return res.status(400).json({
                success: false,
                error: 'Message is required and must be a non-empty string'
            });
        }

        // Call Python chatbot
        const result = await callPythonChatbot(message.trim());
        console.log('Final result to send:', result); // Debug logging

        // Send response matching your frontend expectations
        res.json({
            success: result.success || true,
            reply: result.answer || result.reply || 'Sorry, I could not process your request.',
            answer: result.answer || result.reply || 'Sorry, I could not process your request.',
            sources: result.sources || [],
            has_context: result.has_context || false,
            tokens: result.tokens || 0,
            intent: result.intent || 'unknown',
            results_count: result.results_count || 0,
            filters_applied: result.filters_applied || {}
        });

    } catch (error) {
        console.error('Chatbot error:', error);
        res.status(500).json({
            success: false,
            error: 'I\'m having trouble processing your request right now. Please try again.',
            reply: 'Technical error occurred. Please try again.',
            answer: 'Technical error occurred. Please try again.',
            sources: [],
            has_context: false,
            tokens: 0,
            details: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
});

// GET /chatbot/stats - Database statistics
router.get('/stats', async (req, res) => {
    try {
        // Call Python chatbot for stats
        const result = await callPythonChatbot('__GET_STATS__');

        res.json({
            success: true,
            data: {
                comments: result.comments || 0,
                posts: result.posts || 0,
                tasks: result.tasks || 0,
                users: result.users || 0,
                total: result.total || 0
            }
        });

    } catch (error) {
        console.error('Stats error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to get database statistics',
            details: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
});

// GET /chatbot/health - Health check
router.get('/health', async (req, res) => {
    try {
        // Test if Python chatbot is working
        const result = await callPythonChatbot('__HEALTH_CHECK__');
        
        res.json({
            success: true,
            status: 'healthy',
            chatbot_ready: true,
            message: 'MindVerse AI Chatbot is operational',
            timestamp: new Date().toISOString(),
            database_connected: result.database_connected || false
        });

    } catch (error) {
        console.error('Health check error:', error);
        res.status(503).json({
            success: false,
            status: 'unhealthy',
            chatbot_ready: false,
            message: 'MindVerse AI Chatbot is not responding',
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

export default router;