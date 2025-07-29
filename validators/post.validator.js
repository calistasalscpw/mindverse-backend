import Post from "../models/posts.model.js";

export async function isUserValidator(req, res, next) {
  const user = req.user;
  if (!user) {
    return res
      .status(401)
      .json({ message: "You are not authorized. Please login." });
  }
  next();
}

export async function isSameUserValidator(req, res, next) {
  try {
    const user = req.user;

    if (!user) {
      return res
        .status(401)
        .json({ message: "You are not authorized. Please login." });
    }

    const post = await Post.findById(req.params.postId);

    if (!post) {
      return res.status(404).json({ message: "Post not found." });
    }

    if (!post.author.equals(user._id)) {
      return res.status(403).json("Not authorized to modify this post");
    }

    next();
  } catch (err) {
    return res
      .status(500)
      .json({ message: "An error occured during validation" });
  }
}