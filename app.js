import express from 'express';
import cors from 'cors';
import passport from 'passport';
import dotenv from 'dotenv';
import cookieParser from 'cookie-parser';

import userRouter from './routers/user.js';
import taskRouter from './routers/task.js'; // Import the task router

const app = express();
app.use(cookieParser());
app.use(cors());
app.use(express.json());
app.use(express.static("public"))
app.use(express.urlencoded({extended: true}))

app.use((req, res, next) => {
    if(!req.cookies['token']) {
        return next();
    }
    passport.authenticate(
        "jwt",
        {session: false}
    )(req, res, next)
})

app.use('/auth', userRouter); 
app.use('/tasks', taskRouter); // add this line to use the task router

app.use((err, req, res, next) => {
    console.error(err.stack);
    return res.status(500).json({message: 'An error occured!'});
});

export default app;
