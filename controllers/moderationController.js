const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const UserBehaviour = require('../models/UserBehaviour');

exports.processModeration = async (req, res) => {
    try {
        let { userId, role, text, distance } = req.body;
        const userRole = (role || "STUDENT").trim().toUpperCase(); 
        
        console.log(`--- New Integration Request: ${userId} ---`);

        let visualStatus = "None";
        let aiResult = { toxicityScore: 0.1, transcribedText: text };

        // 1. Python AI Server ko Call karein (API Request)
        try {
            const formData = new FormData();
            
            // Agar image/frame aayi hai toh use bheinjein
            if (req.files && req.files.frame) {
                formData.append('frame', req.files.frame.data, { filename: 'frame.jpg' });
            }
            
            // Flask Server (ai_engine.py) ko request bhejna
            const aiResponse = await axios.post('http://127.0.0.1:5000/detect', formData, {
                headers: { ...formData.getHeaders() }
            });
            
            visualStatus = aiResponse.data.visual_status; // AI Gesture Result
        } catch (aiErr) {
            console.error("AI Server Connection Failed. Check if python ai_engine.py is running.");
        }

        // 2. Authority Exemption
        const isExempt = (userRole === 'TEACHER' || userRole === 'ADMIN');

        // 3. Database Management & Strike Logic
        let user = await UserBehaviour.findOne({ userId });
        if (!user) {
            user = new UserBehaviour({ userId, role: userRole, strikes: 0 });
        }

        // 4. Combined Violation Check (Text + Gestures)
        if (!isExempt) {
            // Agar Gesture mila (Fist/Palm/Point)
            if (visualStatus !== "None") {
                user.strikes = (user.strikes || 0) + 1;
                
                // Strike Levels
                if (user.strikes >= 5) user.isBlocked = true;
                else if (user.strikes >= 3) user.isMuted = true;

                user.violationHistory.push({
                    type: 'VISUAL',
                    reason: visualStatus,
                    timestamp: new Date()
                });
            }
        }

        await user.save();

        res.json({
            success: true,
            visual_status: visualStatus,
            userStatus: { 
                strikes: user.strikes, 
                isMuted: user.isMuted || false, 
                isBlocked: user.isBlocked || false 
            }
        });

    } catch (error) {
        console.error("Controller Error:", error);
        res.status(500).json({ success: false, error: error.message });
    }
};