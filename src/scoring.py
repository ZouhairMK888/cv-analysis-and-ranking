def final_score(experience_years, skills_count, job_match_score, jd_provided):
    """
    Compute final score.
    If job description is NOT provided, ignore job match.
    """

    score = 0

    # Experience (max 40)
    score += min(experience_years * 5, 30)

    # Skills (max 30)
    score += min(skills_count * 5, 20)

    # Job description relevance ONLY if provided
    if jd_provided:
        score += (job_match_score / 100) * 350

    return round(score, 2)
