import { Router } from 'express';
import Post from '../models/posts.model.js';
import User from '../models/users.model.js';
import Comment from '../models/comments.model.js';
import commentRouter from './comment.js';

const router = Router();

router.use('/:postId/comments', commentRouter); 
router.get('/:postId', async (req, res) => {
    try {
        const results = await Post.findById(req.params.postId).populate('author', 'username');
        if (!results){
            return res.status(404).json({error: 'Post not found'});
        }
        res.json(results);
    } catch (err){
        res.status(500).json({message: err.message})
    }
})

// router.use('/:postId/comments', commentRouter); 

//TODO ADD ISUSERVALIDATOR
router.post('/', async(req, res) => {
    try {
        const {title, body} = req.body;
        const createdPost = await Post.create({
            title,
            body,
            author: req.user._id
        })
        await User.findByIdAndUpdate(req.user._id, {
            $push: {posts: createdPost._id}
        })
        res.status(201).json(createdPost);
    } catch (err){
        res.status(400).json({message: err.message});
    }
})

// TODO ADD ISSAMEUSERVALIDATOR
router.put('/:postId', async (req, res)=> {
    try {
        const postId = req.params.postId;
        const {title, body} = req.body;

        const updatedPost = await Post.findByIdAndUpdate(postId, {
            title,
            body
        }, {
            returnDocument: "after"
        })
        if (!updatedPost) {
            return res.status(404).json({error: 'Post not found'});
        }
        res.json(updatedPost);
    } catch (err){
        res.status(400).json({message: err.message});
    }
})

// TODO ADD ISSAMEUSERVALIDATOR
router.delete("/:postId", async (req, res)=> {
   try {
        const deletedPost = await Post.findByIdAndDelete(req.params.postId);
        if (!deletedPost){
            return res.status(404).json({error: 'Post not found'});
        }
        
        await User.findByIdAndUpdate(deletedPost.author, {
            $pull: {
                posts: req.params.postId
            }
        })


        //also delete all comments related to this post
        await Comment.deleteMany({post: req.params.postId});

        res.status(204).send();
    } catch (err) {
        console.error("Delete post error:", err);
        res.status(500).json({
            success: false,
            message: 'Internal server error',
            error: err.message
        });
    }
})

export default router;