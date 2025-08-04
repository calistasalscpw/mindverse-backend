import { Router } from 'express';
import Task from '../models/tasks.model.js';
import User from '../models/users.model.js';
import { createMemoryRouter } from 'react-router-dom';
// import { isUserValidator, isSameUserValidator } from '../validators/task.validator.js';

const router = Router();

// --- Middleware to check for HoD/Lead or HR permissions ---
function requireLeadOrHR(req, res, next) {
  if (!req.user || (!req.user.isLead && !req.user.isHR)) {
    return res.status(403).json({ message: 'Only HoD/Lead or HR can perform this action.' });
  }
  next();
}

// --- POST /tasks - Only HoD/HR can create ---
router.post('/', requireLeadOrHR, async (req, res) => {
  try {
    let assignTo = req.body.assignTo;
    if (!assignTo || !Array.isArray(assignTo) || assignTo.length === 0) {
      assignTo = [req.user._id];
    }
    const newTask = new Task({ ...req.body, assignTo });
    const savedTask = await newTask.save();
    res.status(201).json(savedTask);
  } catch (error) {
    res.status(400).json({ message: 'Failed to create task', error: error.message });
  }
});

// --- GET /tasks - All logged-in users can view ---
router.get('/', async (req, res) => {
  try {
    const tasks = await Task.find({});
    res.status(200).json(tasks);
  } catch (error) {
    res.status(500).json({ message: 'Failed to get task' });
  }
});

// --- PATCH /tasks/:taskId/status - All logged-in users can change status (drag-and-drop) ---
router.patch('/:taskId/status', async (req, res) => {
  try {
    const { taskId } = req.params;
    const { progressStatus } = req.body;

    if (!progressStatus) {
      return res.status(400).json({ message: "progressStatus is required." });
    }

    const updatedTask = await Task.findByIdAndUpdate(
      taskId,
      { $set: { progressStatus: progressStatus } },
      { new: true }
    );

    if (!updatedTask) {
      return res.status(404).json({ error: "Task not found." });
    }
    res.json(updatedTask);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

// --- PUT /tasks/:taskId - Only HoD/HR can edit full task data from the modal ---
router.put('/:taskId', requireLeadOrHR, async (req, res) => {
  try {
    const { taskId } = req.params;
    const updatedTask = await Task.findByIdAndUpdate(taskId, req.body, { new: true });
    if (!updatedTask) {
      return res.status(404).json({ error: "Task not found." });
    }
    res.json(updatedTask);
  } catch (err) {
    res.status(400).json({ message: err.message });
  }
});

// --- DELETE /tasks/:taskId - Only HoD/HR can delete ---
router.delete('/:taskId', requireLeadOrHR, async (req, res) => {
  try {
    const deletedTask = await Task.findByIdAndDelete(req.params.taskId);
    if (!deletedTask) {
      return res.status(404).json({ error: 'Task not found' });
    }
    res.status(204).send();
  } catch (err) {
    res.status(500).json({ success: false, message: 'Internal server error', error: err.message });
  }
});

export default router;