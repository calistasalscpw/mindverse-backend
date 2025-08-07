import {Router} from 'express';
// import Post from '../models/posts.model.js';
import Comment from '../models/comments.model.js';

const router = Router({ mergeParams: true });

// Middleware untuk mengambil postId dari parent router
router.use((req, res, next) => {
    // postId dari parent router (misal: /forum/:postId/comments)
    req.postId = req.params.postId;
    next();
});

// POST /forum/:postId/comments
router.post('/', async (req, res) => {
    try {
        const { name, email, body } = req.body;
        const postId = req.postId;

        if (!name || !email || !body) {
            return res.status(400).json({ message: 'All fields (name, email, body) are required.' });
        }
        if (!postId) {
            return res.status(400).json({ message: 'postId param is required.' });
        }

        const newComment = new Comment({
            name,
            email,
            body,
            postId
        });

        const savedComment = await newComment.save();
        res.status(201).json(savedComment);
    } catch (error) {
        console.error('Error creating comment:', error);
        res.status(500).json({ message: 'Server error', error: error.message });
    }
});

// GET /forum/:postId/comments
router.get('/', async (req, res) => {
    try {
        const postId = req.postId;
        let comments;
        if (postId) {
            comments = await Comment.find({ postId: postId });
        } else {
            comments = await Comment.find();
        }

        res.status(200).json(comments);
    } catch (error) {
        console.error('Error fetching comments:', error);
        res.status(500).json({ message: 'Server error', error: error.message });
    }
});

export default router;