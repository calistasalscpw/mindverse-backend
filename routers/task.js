import { Router } from 'express';
import Task from '../models/tasks.model.js';
import User from '../models/users.model.js';
import { isUserValidator, isSameUserValidator } from '../validators/task.validator.js';

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

router.put('/:taskId', async (req, res) => {
    try {
      const { taskId } = req.params;
      const {name, description, progressStatus, dueDate, assignTo} = req.body;

      const updatedTask = await Task.findByIdAndUpdate(taskId, {
        name,
        description,
        progressStatus,
        dueDate,
        assignTo
      }, {
        returnDocument: "after"
      })
      if (!updatedTask) {
        return res.status(404).json({error: "Task not found."})
      }
      res.json(updatedTask);
    } catch (err){
      res.status(400).json({message: err.message});
    }
})

router.delete("/:taskId", async (req, res) => {
  try {
    const deletedTask = await Task.findByIdAndDelete(req.params.taskId);
    if(!deletedTask){
      return res.status(404).json({error: "Task not found"})
    }

    await User.findByIdAndUpdate(deletedTask.author, {
      $pull: {
        tasks: req.params.taskId
      }
    })

    res.status(204).send();
  } catch (err){
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: err.message
    });
  }
})

export default router;