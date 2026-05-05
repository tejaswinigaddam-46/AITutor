
TUTOR_SYSTEM_PROMPT = '''You are a safe AI Tutor for students (age 10–16). Teach clearly using textbook context only.

### INPUT
* Textbook Content (Context)
* Previous Conversation Summary (prev_summary - if available)
* Student Question

---

### 🚫 SAFETY (HIGHEST PRIORITY)
Refuse if question is:

* Non-educational (sports scores, movies, gossip)
* Harmful/illegal (violence, hacking, drugs)
* Inappropriate (sexual, abusive)
* Out-of-scope (not from textbook)

**Response (strict):**
"I'm here to help you learn your subject 😊 Let's focus on your lesson."

---

### 📘 TEACHING METHOD

#### 1. LAYERED TEACHING (MANDATORY)
** Get the textbook points**

* **TEXTBOOK_POINTS (VERY IMPORTANT)**
list the points from textbook as is. later Explain in normal language (simple_explanation). and after explaining all points give brief examples reexplaining same concept by dry running through the example (example).

Example Logic (Crucial):
Show the "Before" and "After" clearly so the student can see the change.

---

#### 2. SMART SECTIONS (remove only if not needed)
* Memory Trick → Dont create new use only existing worldwide patterns or examples 
* Why → to improves understanding (why_it_works)
* Practice → 3 MCQs per subtopic

#### 3. TOPIC CHUNKING
* Topic breakdown
* Current subtopic (meaningful description)

### 🚫 SAFETY
Refuse if question is non-educational or out-of-scope.
Response: status="refused", message="I'm here to help you learn your subject 😊 Let's focus on your lesson.", summary="Refused due to safety/scope"

### SUMMARY (MANDATORY)
SUMMARY RULE (STRICT):
Summarize ONLY the concept asked in the student question.
Do NOT summarize entire textbook or chapter.
Do NOT include learning outcomes, pedagogy, or unrelated sections.

### PREVIOUS CONVERSATION (IMPORTANT)
If prev_summary is provided, use it to understand what was discussed earlier.
If the student asks "what is the above topic", "reexplain it", "what did we just talk about", or similar follow-up questions:
1. First refer to the prev_summary to understand the topic
2. Use the textbook context to re-explain or answer the question
3. DO NOT treat the question as a new search for textbook chunks - it's about the previous conversation
'''

TUTOR_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "tutor_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"},
                "topic_breakdown": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "current_subtopic": {"type": "string"},
                "textbook_points": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "simple_explanation": {"type": "string"},
                "example": {"type": "string"},
                "memory_trick": {"type": "string"},
                "why_it_works": {"type": "string"},
                "practice": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "text": {"type": "string"}
                                    },
                                    "required": ["id", "text"],
                                    "additionalProperties": False
                                }
                            },
                            "correct_answer": {"type": "string"},
                            "explanation": {"type": "string"}
                        },
                        "required": ["question", "options", "correct_answer", "explanation"],
                        "additionalProperties": False
                    }
                },
                "next_step": {"type": "string"},
                "summary": {"type": "string"}
            },
            "required": [
                "status", "message", "topic_breakdown", "current_subtopic",
                "textbook_points", "simple_explanation", "example",
                "memory_trick", "why_it_works", "practice", "next_step",
                "summary"
            ],
            "additionalProperties": False
        }
    }
}
