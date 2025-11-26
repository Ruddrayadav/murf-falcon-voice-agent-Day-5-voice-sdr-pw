# 🎤  Voice SDR Agent  
### Built for Day 5 — Murf AI Voice Agents Challenge

This project is a fully functional **Voice-Based SDR (Sales Development Representative) Agent** for **Physics Wallah (PW)**.  
It can answer FAQs, qualify leads, collect user details, summarize the call, and save lead data — all using real-time voice.

The agent is powered by:

- **LiveKit Agents**
- **Murf Falcon TTS**
- **Gemini 2.5 Flash**
- **Deepgram STT**
- **Silero VAD + Turn Detection**

---

## 🚀 Features

### 🔹 1. SDR Persona  
- Greets users warmly  
- Understands what they’re looking for  
- Keeps conversation focused on user needs  

### 🔹 2. FAQ Question Answering  
Uses a custom Physics Wallah FAQ (`pw_content.json`) to answer:

- What is PW?
- Course offerings (NEET/JEE/UPSC etc.)
- Free trials
- Pricing details
- Teacher information

### 🔹 3. Lead Qualification  
The agent collects:

- Name  
- Email  
- Role  
- Exam/course interest  
- Timeline (now / soon / later)

All in a natural conversational flow.

### 🔹 4. End-of-Call Summary  
When the user says *“I’m done”, “That’s all”, “Thank you”*, the agent:

1. Stops the conversation  
2. Generates a summary like:  
   > *“Rudra is interested in NEET and wants to start soon.”*  
3. Calls the `save_lead` tool  
4. Stores data in `pw_leads.json`  

### 🔹 5. Real-Time Voice Pipeline  
- Deepgram Nova-3 STT  
- Murf Falcon TTS (fastest TTS API)  
- LiveKit turn detection  
- Noise cancellation (BVC)

---


