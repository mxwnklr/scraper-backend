from fastapi import APIRouter, HTTPException, Request
import os
import openai

router = APIRouter()

openai.api_key = os.getenv("OPENAI_API_KEY")

@router.post("/api/openai")
async def get_openai_response(request: Request):
    data = await request.json()
    userPrompt = data.get("userPrompt", "")
    outputFile = data.get("outputFile", "")

    # Debug statement to confirm file inclusion
    print(f"Debug: Sending to OpenAI - File: {outputFile}, Prompt: {userPrompt}")

    try:
        response = openai.Completion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"File: {outputFile}\nPrompt: {userPrompt}"},
            ],
            store=True,
        )
        message = response.choices[0].message.content
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))