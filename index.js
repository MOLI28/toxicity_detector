const express = require("express");
const dotenv = require("dotenv");
const cors = require('cors');
const mongoose = require("mongoose");
const moderationRoutes = require("./routes/moderationRoutes");

dotenv.config();

// 1. Pehle 'app' banayein
const app = express(); 

// 2. Ab 'app' ban gaya hai, toh middlewares add karein
app.use(cors()); 
app.use(express.json({ limit: "10mb" })); 
app.use(express.urlencoded({ extended: true }));

// 3. Routes connect karein
app.use("/api", moderationRoutes);

// MongoDB connection (aapka purana code...)
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log("MongoDB Connected"))
  .catch(err => console.log(err));

const PORT = process.env.PORT || 5001;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));