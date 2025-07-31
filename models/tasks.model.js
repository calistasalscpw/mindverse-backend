import mongoose, {Schema} from "mongoose";

const TaskSchema = new Schema(
    {
        name: {
            type: String,
            required: true,
        },
        description: {
            type: String,
        },
        progressStatus: {
            type: String,
            enum: ["ToDo", "In Progress", "Done"],
            required: true,
        },
        index: {
            type: Number,
        },
        dueDate: {
            type: Date,
        },
        assignTo: [
            {
                type: mongoose.Schema.Types.ObjectId,
                ref: "User",
            },
        ],
    },
    {
        timestamps: true,
    }
);

const Task = mongoose.model("Task", TaskSchema)

export default Task;
