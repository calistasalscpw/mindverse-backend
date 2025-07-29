import mongoose, {Schema} from "mongoose";

const CommentSchema = new Schema({
    name: {
        type: String,
        required: true
    },
    email: {
        type: String,
        required: true
    },
    body: {
        type: String,
        required: true
    },
    post: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Post'
    }

})

const Comment = mongoose.model("Comment", CommentSchema);
export default Comment;