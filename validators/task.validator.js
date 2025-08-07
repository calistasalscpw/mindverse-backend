import Task from "../models/tasks.model.js"

export async function isUserValidator(req, res, next) {
    const user = req.user;
    if (!user){
        return res
            .status(401)
            .json({message: "You are not authorized. PLease login."})
    }
    next();
}

export async function isSameUserValidator(req, res, next) {
    try {
        const user = req.user;

        if(!user){
            return res
                .status(401)
                .json({message: "You are not authorized. Please login."})
        }

        const task = await Task.findById(req.params.taskId);

        if(!task){
            return res.status(404).json({message: "Task not found"})
        }

        if(!post.author.equals(user._id)){
            return res.status(403).json({message: "Not authorized to modify this task"})
        }

        next();
    } catch (err){
        return res
            .status(500)
            .json({message: "An error occured during validation"})
    }
}