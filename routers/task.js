import { Router } from 'express';
import Task from '../models/tasks.model.js';

const router = Router();

router.post('/', async (req, res) => {
  try {
    const newTask = new Task({
      name: req.body.name,
      description: req.body.description,
      progressStatus: req.body.progressStatus,
      index: req.body.index,
      dueDate: req.body.dueDate,
      assignTo: req.body.assignTo,
    });

    const savedTask = await newTask.save();

    res.status(201).json(savedTask);

  } catch (error) {
    res.status(400).json({ message: 'Failed to create task', error: error.message });
  }
});

router.get('/', async (req, res) => {
    try {
        const tasks = await Task.find({});
        res.status(200).json(tasks);
    } catch (error) {
        res.status(500).json({ message: 'Failed to get task' });
    }
});

export default router;