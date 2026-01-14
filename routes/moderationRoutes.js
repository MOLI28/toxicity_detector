const express = require('express');
const router = express.Router();
const moderationController = require('../controllers/moderationController');
const fileUpload = require('express-fileupload'); // Multer ki jagah ise use karein
const UserBehaviour = require('../models/UserBehaviour');

// 1. Middleware: Multer hata kar fileUpload lagayein taaki audio aur frame dono mil sakein
router.use(fileUpload());

// 2. Route: process (Jo AI aur Strikes dono handle karega)
router.post('/process', moderationController.processModeration);

// 3. Route: Sabhi users ka data nikalne ke liye
router.get('/users', async (req, res) => {
    try {
        const users = await UserBehaviour.find().sort({ lastViolation: -1 }); 
        res.json(users);
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// 4. Sabse aakhri mein export karein
module.exports = router;