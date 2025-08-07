import express from 'express';
import cors from 'cors';
import passport from 'passport';
import dotenv from 'dotenv';
import cookieParser from 'cookie-parser';

import userRouter from './routers/user.js';
import taskRouter from './routers/task.js'; 
import postRouter from './routers/post.js';
import commentRouter from './routers/comment.js';
import chatbotRouter from './routers/chatbot.js';
import meetingRouter from './routers/meeting.js'; 

const app = express(); 

// Load environment variables
dotenv.config();

// Middleware
app.use(cookieParser());
app.use(cors({
    origin: ['http://localhost:5173', 'http://localhost:3000'],
    credentials: true
}));
app.use(express.json());
app.use(express.static("public"));
app.use(express.urlencoded({extended: true}));

// Authentication middleware
app.use((req, res, next) => {
    if(!req.cookies['token']) {
        return next();
    }
    passport.authenticate(
        "jwt",
        {session: false}
    )(req, res, next)
});

// Mount routes in order of specificity (most specific first)
app.use('/auth', userRouter); 
app.use('/tasks', taskRouter); 
app.use('/meetings', meetingRouter); // Add meetings route
app.use('/chatbot', chatbotRouter);
app.use('/forum', postRouter);  // This includes nested comment routes

// Basic routes
app.get('/', (req, res) => {
    res.json({
        success: true,
        message: 'MindVerse Backend API is running',
        timestamp: new Date().toISOString(),
        endpoints: {
            auth: '/auth/*',
            tasks: '/tasks/*',
            meetings: '/meetings/*', // Add meetings endpoint
            forum: '/forum/*',
            chatbot: '/chatbot/*'
        }
    });
});

app.get('/health', (req, res) => {
    res.json({
        success: true,
        message: 'MindVerse Backend API is healthy',
        timestamp: new Date().toISOString(),
        services: {
            database: 'connected',
            chatbot: 'available'
        }
    });
});

// 404 handler 
app.use('/*splat', (req, res) => {
    res.status(404).json({
        success: false,
        message: 'Endpoint not found',
        path: req.originalUrl,
        availableEndpoints: ['/auth', '/tasks', '/meetings', '/forum', '/chatbot', '/health'] // Add meetings to available endpoints
    });
});

// Error handler
app.use((err, req, res, next) => {
    console.error('Error:', err.stack);
    return res.status(500).json({
        success: false,
        message: 'An internal server error occurred',
        error: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

export default app;