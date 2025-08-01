import express from 'express';
import cors from 'cors';
import passport from 'passport';
import dotenv from 'dotenv';
import cookieParser from 'cookie-parser';

import userRouter from './routers/user.js';
import taskRouter from './routers/task.js'; 
import postRouter from './routers/post.js';
import commentRouter from './routers/comment.js';

const app = express(); 

// dotenv.config();
app.use(cookieParser());
app.use(cors({
    origin: 'http://localhost:5173', // Your frontend's address
    credentials: true, // Allow cookies to be sent
}));

app.use(express.json());
app.use(express.static("public"));
app.use(express.urlencoded({extended: true}));

app.use((req, res, next) => {
    if(!req.cookies['token']) {
        return next();
    }
    passport.authenticate(
        "jwt",
        {session: false}
    )(req, res, next)
});

app.use('/auth', userRouter); 
app.use('/tasks', taskRouter); 
app.use('/forum', postRouter);

app.use((err, req, res, next) => {
    console.error(err.stack);
    return res.status(500).json({message: 'An error occured!'});
});

export default app;
