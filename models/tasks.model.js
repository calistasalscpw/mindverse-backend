import mongoose from "mongoose";

const taskSchema = new mongoose.Schema(
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

export default mongoose.model("Task", taskSchema);
