# How Job Recommendations Work in JobMatch

This guide explains how JobMatch recommends jobs to you in simple, plain language.

---

## 1. What You See on Your Screen

When you open your recommendations feed, you see a list of open job postings sorted for you. Each card shows:
- **The Job Details**: Job title, hiring company, and location.
- **The Match Score**: A percentage score (0% to full match) that shows how many required skills you share with the job.
- **Green Skill Chips**: The skills you have that the employer asked for.
- **Orange Skill Chips**: The skills the employer asked for that are not yet listed on your profile.

### Important Note About the Score vs. the Order
The percentage shown on each card is strictly your **skill match score** (for example, having 3 out of 4 skills shows 75%). However, the **order of the jobs from top to bottom** is decided by a combined score that includes both your skills (70%) and the general meaning of your profile text (30%). This means a job with a 75% skill match can sometimes appear higher than an 80% skill match if its general description is a much closer fit for your target career role.

---

## 2. How the Order is Decided (in 3 Simple Steps)

The system compares your profile to active job postings:

### Step 1: Count Your Matching Skills (70% of the ranking score)
The system checks how many of the required skills you have. It recognizes common nicknames (for example, it knows that "React.js" and "ReactJS" mean the same thing).

### Step 2: Read the Meaning of the Job (30% of the ranking score)
The system reads the text of your profile (your preferred job role, education, and skills) and compares it with the text of the job ad. It looks at the overall meaning rather than just exact keywords.

### Step 3: Combine and Sort
The system combines the two parts. Jobs with the highest combined score appear first. If two jobs have the exact same score, the system breaks the tie using the job's ID number.

### Worked Example (illustrative, values invented):
> **Example**:
> Suppose an employer is hiring for a Flutter Developer and asks for 4 skills: Flutter, Dart, REST API, and Git.
> - **Your Skills**: You have Flutter, Dart, and REST API (3 out of 4 skills).
> - **Step 1 (Skill Score)**: 3 ÷ 4 = **0.75** (shows as 75% on the card).
> - **Step 2 (Meaning Score)**: The system reads your preferred role and scores general relevance at **0.80**.
> - **Step 3 (Combined Ranking Score)**:
>   $$\text{Final Score} = (0.70 \times 0.75) + (0.30 \times 0.80) = 0.525 + 0.240 = \mathbf{0.765}$$
> This final number (0.765) decides where this job sits on your list.

---

## 3. What the Score Means

- The score is **only a sorting tool** to put relevant jobs near the top of your feed.
- It is **NOT** your chance of being hired.
- It is **NOT** a judgment of your ability, intelligence, or worth as a person.
- A job with a lower score might still be a great job for you to apply to.

---

## 4. What Information is Used (and What is NOT Used)

### Information Used:
- **Your skills**: The skills you select on your profile.
- **Your preferred role**: The job title you want to work as.
- **Your education**: The degree or school level listed on your profile.

### Information NOT Used:
Our recommendation system does **not** look at:
- Age
- Gender
- Ethnicity or nationality
- Profile photos
- Location or address
- Years of experience

---

## 5. How to Get Better Matches

1. **Add all your real skills**: If you know a tool or language, add it to your profile.
2. **Write a clear target role**: Use clear titles like "Junior Web Developer" or "Accountant".
3. **Keep your profile updated**: When you learn a new tool or finish a course, update your profile.

---

## 6. Limits in Plain Words

- **Jobs with no listed skills**: When an employer lists no skills, the system scores the job on text meaning alone (`ranking = semantic`). This means a job without skills can rank higher than a job where you have only half the skills (for example, scoring 0.70 vs 0.56 for 50% skill coverage). However, if you filter by minimum skill match above 0%, jobs with no skills are hidden.
- **Unusual spelling**: If a skill is spelled in a very rare way that our system does not recognize, it may not match.
- **Khmer text**: The system reads Khmer script, but the AI model was trained mostly on other languages and has been tested on only 15 Khmer jobs in our test set. Those postings also contained English skill words.
- **Always read the full ad**: Recommendations are automated suggestions. Always read the employer's full job description before applying.

---

## 7. Privacy and Your Data

Recommendation calculations run on our own server. The engine does not send candidate profile data to external AI services. The embedding model is downloaded from Hugging Face on first start. This is a design description, not a security or legal guarantee.

---

## 8. Frequently Asked Questions (FAQ)

### Why is a job I like ranked low?
If the employer listed several technical skills that you have not added to your profile, the skill match portion of the score drops. Adding those skills to your profile will lift the job higher.

### Why does a job show skills I already have as missing?
This usually happens if the employer wrote a skill using an unusual name that is not yet in our dictionary, or if you have not checked that skill on your profile page.

### Can I change the order?
The order is set automatically by the system formula (70% skill match and 30% text meaning). You can filter the list by setting a minimum match percentage.
