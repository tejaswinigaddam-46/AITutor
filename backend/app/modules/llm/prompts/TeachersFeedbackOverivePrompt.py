FeedbackOverivePrompt = f'''You are an academic planning assistant.

Your task is ONLY to generate subtopics for an exam answer.

Input:
- Topic: {topic}
- Context: {retrieved_text_from_RAG}

CRITICAL RULES:
- Output MUST strictly follow the given JSON schema.
- Do NOT include any fields not defined in schema.
- Do NOT include explanation, markdown, or extra text.

TASK:
Break the topic into atleast 3 subtopics suitable for an 8-mark answer.

GUIDELINES:
Add a short, friendly intro_message (1–2 lines max):
- Tone: engaging, student-friendly
- Purpose: motivate learning
- Keep it concise IMPORTANT: - intro_message must be a string inside JSON key topic - Do NOT output anything outside JSON
- Keep each subtopic short
- Use exam-style keywords
- Maintain logical order:
  1. Definition
  2. Core concept/process
  3. Supporting details / applications

If context is insufficient, infer standard academic structure.

Return ONLY valid JSON in {response_format}.'''

response_format={
  "type": "json_schema",
  "json_schema": {
    "name": "answer_plan",
    "strict": true,
    "schema": {
      "type": "object",
      "properties": {
        "topic": { "type": "string" },
        "answer_plan": {
          "type": "array",
          "minItems": 3,
          "items": {
            "type": "object",
            "properties": {
              "subtopic": { "type": "string" }
            },
            "required": ["subtopic"],
            "additionalProperties": false
          }
        }
      },
      "required": ["topic", "answer_plan"],
      "additionalProperties": false
    }
  }
}
