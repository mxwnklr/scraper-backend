from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from script_runner import run_script  # Import your script

app = FastAPI()

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to ["http://localhost:3000"] for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process/")
async def process_script(
    company_url: str = Form(...),
    keywords: str = Form(...),
    include_ratings: str = Form(...)
):
    keywords_list = keywords.split(",")  
    include_ratings_list = list(map(int, include_ratings.split(",")))  

    output_file = run_script(company_url, keywords_list, include_ratings_list)

    if output_file:
        return FileResponse(output_file, filename="scraped_reviews.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        return {"message": "No matching reviews found."}