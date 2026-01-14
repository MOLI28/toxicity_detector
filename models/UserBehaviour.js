const mongoose = require('mongoose');

const UserBehaviourSchema = new mongoose.Schema({
    userId: { type: String, required: true, unique: true },
    role: { type: String, default: "STUDENT" },
    strikes: { type: Number, default: 0 },
    isMuted: { type: Boolean, default: false },
    isBlocked: { type: Boolean, default: false },
    lastViolation: { type: Date },
    violationHistory: [{
        type: { type: String }, // 'VISUAL' or 'TEXT'
        reason: { type: String },
        timestamp: { type: Date, default: Date.now }
    }]
});

// Static Method: Asli logic jo Controller call karega
UserBehaviourSchema.statics.handleViolation = async function(userId, visualStatus) {
    // 1. User ko dhundein ya naya banayein
    let user = await this.findOne({ userId });
    if (!user) {
        user = new this({ userId });
    }

    let action = "NONE";
    let reason = "Clean";

    // 2. Gesture Violation Check
    // Agar AI ne "None" ke alawa kuch bhi bheja (Fist, Palm, etc.)
    if (visualStatus && visualStatus !== "None") {
        
        // Cooldown Check (e.g., 2 seconds gap) taaki ek hi gesture par 10 strikes na mil jayein
        const now = new Date();
        const timeDiff = user.lastViolation ? (now - user.lastViolation) / 1000 : 10;

        if (timeDiff > 2) {
            user.strikes += 1; // Strike badhayein
            user.lastViolation = now;
            reason = visualStatus;

            // History mein record karein
            user.violationHistory.push({
                type: 'VISUAL',
                reason: visualStatus,
                timestamp: now
            });

            // 3. Penalty Levels Decide Karein
            if (user.strikes >= 5) {
                user.isBlocked = true;
                action = "BLOCK";
            } else if (user.strikes >= 3) {
                user.isMuted = true;
                action = "MUTE";
            } else {
                action = "WARN";
            }
        } else {
            action = "COOLDOWN";
            reason = "Violations too frequent, please wait.";
        }
    }

    await user.save(); // Database update

    return {
        success: true,
        userId: user.userId,
        strikes: user.strikes,
        action: action,
        reason: reason,
        status: {
            isMuted: user.isMuted,
            isBlocked: user.isBlocked
        }
    };
};

module.exports = mongoose.model('UserBehaviour', UserBehaviourSchema);