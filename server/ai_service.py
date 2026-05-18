from g4f.client import Client
from g4f.Provider import PollinationsAI

client = Client()

def get_ai_response(prompt):
    try:
        response = client.chat.completions.create(
            model="openai",
            provider=PollinationsAI,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful, polite, and extremely friendly AI assistant inside NexusChat (a modern chat application built by Smit). Chat naturally and perfectly like a human. Keep your answers concise, engaging, and friendly."
                },
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Oops, something went wrong connecting to the AI brain: {str(e)}"


