import mongoose, {Schema} from "mongoose";

const PostSchema = new Schema(
    {
        title: { 
            type: String, 
            required: true 
        },
        body: { 
            type: String, 
            required: true 
        },
        author: { 
            type: mongoose.Schema.Types.ObjectId, 
            ref: 'User', 
            required: true,
            index: true
        },
        createdAt: { 
            type: Date, 
            default: Date.now 
        },
        // likes: [
        //     { 
        //         type: mongoose.Schema.Types.ObjectId, ref: 'User' 
        //     }
        // ],

        // TO BE UNCOMMENTED
        // comments: [
        //     {
        //         type: mongoose.Schema.Types.ObjectId,
        //         ref: 'Comment'
        //     }
        // ]
    }
);

const Post = mongoose.model('Post', PostSchema);
export default Post;