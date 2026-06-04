# prompts.py

RESUME_ANALYSIS_PROMPT = """
You are a senior technical recruiter with 10+ years hiring engineers at top tech companies.

Analyze the resume below. Return ONLY a valid JSON object.
No explanation. No markdown. No code fences. Pure JSON only.

Required structure:
{{
    "score": <integer 0-100>,
    "verdict": "<Hire | Strong Maybe | Maybe | No Hire>",
    "summary": "<2-3 sentence overall assessment>",
    "strengths": [
        "<specific, evidence-based strength 1>",
        "<specific, evidence-based strength 2>",
        "<specific, evidence-based strength 3>"
    ],
    "weaknesses": [
        "<specific weakness 1>",
        "<specific weakness 2>",
        "<specific weakness 3>"
    ],
    "improvements": [
        "<actionable improvement tip 1>",
        "<actionable improvement tip 2>",
        "<actionable improvement tip 3>",
        "<actionable improvement tip 4>"
    ],
    "missing_sections": ["<e.g. GitHub links>", "<e.g. certifications>"],
    "skills_found": ["<skill 1>", "<skill 2>", "<skill 3>"],
    "ats_issues": [
        "<e.g. Uses tables which ATS cannot parse>",
        "<e.g. Missing quantified achievements>"
    ]
}}

RESUME TEXT:
{resume_text}
"""

ATS_MATCH_PROMPT = """
You are an ATS (Applicant Tracking System) scanner.

Compare the resume and job description below.
Return ONLY valid JSON. No markdown. No explanation.

{{
    "ats_score": <integer 0-100>,
    "matched_keywords": ["<keyword found in both>"],
    "missing_keywords": ["<important JD keyword absent from resume>"],
    "match_summary": "<2 sentence summary of fit>",
    "recommendation": "<Tailor resume | Good match | Strong match>"
}}

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""

BULLET_REWRITE_PROMPT = """
You are an expert resume writer.
Rewrite the bullet point below into 3 stronger versions.
Rules: strong action verb, quantified impact where possible, under 20 words each.

Return ONLY valid JSON:
{{
    "rewrites": [
        "<stronger version 1>",
        "<stronger version 2>",
        "<stronger version 3>"
    ]
}}

BULLET: {bullet}
"""