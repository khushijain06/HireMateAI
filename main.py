import os
import csv
import re
from typing import Optional
import fitz
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
  # PyMuPDF for reading PDFs
import ollama
import shutil
from typing import List
from fastapi import FastAPI,Query,File,UploadFile,Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, String, Text ,text, Float
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, DeclarativeBase
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from fastapi.middleware.cors import CORSMiddleware
#from database import SessionLocal
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./summaries.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


# Base model
class Base(DeclarativeBase):
    pass


# Job Summary Table
class JobSummary(Base):
    __tablename__ = "job_summaries"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_title: Mapped[str] = mapped_column(String)
    job_summary: Mapped[str] = mapped_column(Text)


# CV Summary Table
class CVSummary(Base):
    __tablename__ = "cv_summaries"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cv_filename: Mapped[str] = mapped_column(String)
    cv_name: Mapped[str] = mapped_column(String)
    cv_email: Mapped[str] = mapped_column(String)
    cv_summary: Mapped[str] = mapped_column(Text)

#Similarity Table
class MatchResult(Base):
    __tablename__ = "match_results"
    id: Mapped[int]=mapped_column(primary_key=True,index=True)
    job_title: Mapped[str] = mapped_column(String)
    candidate_name: Mapped[str] = mapped_column(String)
    similarity: Mapped[float]=mapped_column(Float)
    status: Mapped[str] = mapped_column(String)
    candidate_email: Mapped[str] = mapped_column(String)  
Base.metadata.create_all(bind=engine)




# Email config (replace with environment variables in real projects)
SENDER_EMAIL = "hirematejob@gmail.com"
SENDER_PASSWORD = "ecfg yxeh yjaj cudy"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/send-mails", response_model=None)
def send_mails(threshold: float = 0.5, db: Session = Depends(get_db)):
    print('❤️ Called send-mails')

    results = db.query(MatchResult).filter(
        MatchResult.similarity >= threshold,
        MatchResult.status == "selected"
    ).all()

    if not results:
        return JSONResponse(content={"message": "No candidates above threshold."}, status_code=200)

    sender_email = "hirematejob@gmail.com"
    sender_password = "ecfg yxeh yjaj cudy"  # 👈 use environment variable ideally

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        for candidate in results:
            if not candidate.candidate_email or "@" not in candidate.candidate_email:
              print(f"⚠️ Skipping invalid email for {candidate.candidate_name}: {candidate.candidate_email}")
              continue  # Skip invalid emails

            print(f"📧 Sending to {candidate.candidate_email} ➕")
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = candidate.candidate_email
            msg["Subject"] = f"HireMate - You’re Selected for {candidate.job_title}"

            body = f"""Hi {candidate.candidate_name},

            You’ve been selected for the role of '{candidate.job_title}' with a similarity score of {round(float(candidate.similarity) * 100)}%.

            We’ll contact you soon with the next steps.

            Best,
            HireMate Team
            """
            msg.attach(MIMEText(body, "plain"))
            server.sendmail(sender_email, candidate.candidate_email, msg.as_string())

    
        server.quit()
        print('✅ All emails sent successfully.')
        return JSONResponse(content={"message": "Emails sent successfully."}, status_code=200)

    except Exception as e:
        print("❌ Email sending error:", e)
        return JSONResponse(content={"error": str(e)}, status_code=500)


# --------------------- JD Summarizer ---------------------
@app.post("/summarize")
def summarize_job_descriptions(file: UploadFile = File(None)):
    print("🔄 /summarize endpoint called")
    summaries = []
    db = SessionLocal()
    try:
        if file:
            filepath = f"./uploaded_job_description.csv"
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            filepath = "./job_description.csv"  # default file

        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                title = row.get("Job Title", "").strip()
                description = row.get("Job Description", "").strip()
                print(f"📌 Processing: {title}")
                if not description:
                    print("⚠️ Skipped: Empty description")
                    continue

                summary = summarize_job_description(description)

                job_entry = JobSummary(job_title=title, job_summary=summary)
                db.add(job_entry)
                db.commit()
                summaries.append({
                    "Job Title": title,
                    "Summary": summary
                })
                print(f"✅ Done: {title}")
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"message": "CSV file not found. Please ensure 'job_description.csv' exists."}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"An error occurred: {str(e)}"}
        )
    finally:
        db.close()
    return {
        "message": "Job descriptions summarized successfully!",
        "data": summaries
    }


def summarize_job_description(job_description: str) -> str:
    prompt = f"""
    Summarize the following job description into structured fields:

    Job Description:
    {job_description}

    Return the output in the following format:
    - **Required Skills**
    - **Experience**
    - **Qualifications**
    - **Job Responsibilities**
    """

    response = ollama.chat(
        model='llama3.2:1b',
        messages=[{"role": "user", "content": prompt}]
    )
    return response['message']['content']


# --------------------- CV Summarizer --------------------
from fastapi import UploadFile, File, APIRouter
from typing import List
from fastapi.responses import JSONResponse
import os, shutil
from sqlalchemy.orm import Session

# Assume these are imported:
# from database import SessionLocal
# from models import CVSummary
# from utils import extract_text_from_pdf, summarize_cv, parse_summary

@app.post("/summarize-cvs")
def summarize_cvs(files: List[UploadFile] = File(None)):
    print("📁 /summarize-cvs endpoint called")

    uploaded_folder = "./temp_cvs"
    default_folder = "./CVs1"
    db = SessionLocal()
    summaries = []

    # Ensure folders exist
    os.makedirs(uploaded_folder, exist_ok=True)
    os.makedirs(default_folder, exist_ok=True)

    try:
        if files:
            print("📂 Uploaded CVs received.")
            filepaths = []

            for uploaded_file in files:
                # Save file preserving relative path if available
                relative_path = uploaded_file.filename  # May include folder path
                save_path = os.path.join(uploaded_folder, relative_path)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                with open(save_path, "wb") as buffer:
                    shutil.copyfileobj(uploaded_file.file, buffer)

                filepaths.append(save_path)
        else:
            print("📂 No files uploaded. Using default ./CVs1 folder.")
            filepaths = [
                os.path.join(default_folder, f)
                for f in os.listdir(default_folder)
                if f.endswith('.pdf')
            ]

        if not filepaths:
            return JSONResponse(status_code=404, content={"message": "No PDF resumes found."})

        for filepath in filepaths:
            filename = os.path.basename(filepath)
            print(f"📄 Processing: {filename}")

            text = extract_text_from_pdf(filepath)
            summary_text = summarize_cv(text)
            name, email, structured_summary = parse_summary(summary_text)

            entry = CVSummary(
                cv_filename=filename,
                cv_name=name,
                cv_email=email,
                cv_summary=structured_summary
            )
            db.add(entry)
            db.commit()

            summaries.append({
                "filename": filename,
                "name": name,
                "email": email,
                "summary": structured_summary
            })
            print(f"✅ CV Summarized: {filename}")

    except Exception as e:
        print("❌ Error:", str(e))
        return JSONResponse(status_code=500, content={"message": f"An error occurred: {str(e)}"})

    finally:
        db.close()

    return {
        "message": "CVs summarized successfully!",
        "data": summaries
    }



def extract_text_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def summarize_cv(cv_text: str) -> str:
    prompt = f"""
    Summarize the following CV into structured fields:

    CV Content:
    {cv_text}

    Return the output in the following markdown format:
    - **Name**: [name]
    - **Email**: [email]
    - **Skills**: [skills]
    - **Education**: [education]
    - **Experience**: [experience]
    """
    response = ollama.chat(
        model='llama3.2:1b',
        messages=[{"role": "user", "content": prompt}]
    )
    return response['message']['content']




def parse_summary(summary: str):
    # Extract fields from markdown response
    name = extract_field(summary, r"\*\*Name\*\*: (.+)")
    email = extract_field(summary, r"\*\*Email\*\*: (.+)")

    # Remove name and email lines from summary to keep only Skills, Education, Experience
    structured_summary = "\n".join(
        line for line in summary.splitlines()
        if not line.startswith("- **Name**") and not line.startswith("- **Email**")
    )

    return name or "Unknown", email or "Not found", structured_summary.strip()


def extract_field(text: str, pattern: str):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


# Load the model  # import your SQLAlchemy model


@app.get('/cosine')
def cosine(threshold: float = Query(0.5)):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    engine = create_engine('sqlite:///./summaries.db')
    connection = engine.connect()
    db = SessionLocal()

    # Fetch job summaries
    job_results = connection.execute(text("SELECT id, job_title, job_summary FROM job_summaries")).fetchall()
    jobs = [{"id": r[0], "title": r[1], "summary": r[2]} for r in job_results]

    # Fetch CV summaries with name and email
    cv_results = connection.execute(text("SELECT id, cv_filename, cv_name, cv_email, cv_summary FROM cv_summaries")).fetchall()
    cvs = [{"id": r[0], "filename": r[1], "name": r[2], "email": r[3], "summary": r[4]} for r in cv_results]

    # Encode summaries
    job_texts = [job["summary"] for job in jobs]
    cv_texts = [cv["summary"] for cv in cvs]

    job_embeddings = model.encode(job_texts)
    cv_embeddings = model.encode(cv_texts)

    # Calculate similarity matrix
    similarity_matrix = cosine_similarity(job_embeddings, cv_embeddings)

    result = []

    for i, job in enumerate(jobs):
        matches = []
        for j, score in enumerate(similarity_matrix[i]):
            score_float = round(float(score), 2)
            status = "selected" if score >= threshold else "not selected"

            # ✅ Save match result with candidate email
            match = MatchResult(
                job_title=job["title"],
                candidate_name=cvs[j]["name"],
                candidate_email=cvs[j]["email"],  # ✅ Include email
                similarity=score_float,
                status=status
            )
            db.add(match)

            if score >= threshold:
                matches.append({
                    "cv_id": cvs[j]["id"],
                    "cv_name": cvs[j]["name"],
                    "cv_email": cvs[j]["email"],  # ✅ Optional: return email
                    "similarity": score_float
                })

        result.append({
            "job_id": job["id"],
            "job_title": job["title"],
            "matches": matches
        })

    db.commit()
    db.close()
    return {"threshold": threshold, "results": result}