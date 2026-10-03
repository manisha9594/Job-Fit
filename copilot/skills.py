"""Shared skill lexicon used by JD intake, fit scoring, and tailoring.

Maps lowercase match variants → canonical display name. Kept deliberately
focused on the Python/AI + full-stack roles this copilot targets; extend it
freely for other tracks.
"""
import re

SKILL_VARIANTS: dict[str, str] = {
    # Languages
    "python": "Python",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "java": "Java",
    "c#": "C#",
    "csharp": "C#",
    ".net": ".NET",
    ".net core": ".NET",
    "dotnet": ".NET",
    "asp.net": "ASP.NET Core",
    "asp.net core": "ASP.NET Core",
    "entity framework": "Entity Framework",
    "ef core": "Entity Framework",
    "linq": "LINQ",
    "golang": "Go",
    "sql": "SQL",
    # AI / ML
    "llm": "LLMs",
    "llms": "LLMs",
    "large language model": "LLMs",
    "rag": "RAG",
    "retrieval-augmented": "RAG",
    "prompt engineering": "Prompt Engineering",
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "langfuse": "LangFuse",
    "pydantic-ai": "Pydantic-AI",
    "ai agent": "AI Agents",
    "ai agents": "AI Agents",
    "agentic": "Agentic AI",
    "multi-agent": "Multi-Agent Systems",
    "multi agent": "Multi-Agent Systems",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "mlflow": "MLflow",
    "vector db": "Vector Databases",
    "vector database": "Vector Databases",
    "faiss": "FAISS",
    "chroma": "Chroma",
    "pinecone": "Pinecone",
    "embeddings": "Embeddings",
    "mcp": "MCP",
    "model context protocol": "MCP",
    "openai": "OpenAI API",
    "anthropic": "Anthropic API",
    "hugging face": "Hugging Face",
    # Backend / APIs
    "fastapi": "FastAPI",
    "pydantic": "Pydantic",
    "django": "Django",
    "flask": "Flask",
    "rest": "REST APIs",
    "restful": "REST APIs",
    "api": "APIs",
    "apis": "APIs",
    "graphql": "GraphQL",
    "microservices": "Microservices",
    # Frontend
    "react": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "vue": "Vue",
    "angular": "Angular",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    # Cloud / infra
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "github actions": "GitHub Actions",
    "gitlab": "GitLab",
    "git": "Git",
    "devops": "DevOps",
    "linux": "Linux",
    "azure devops": "Azure DevOps",
    "jenkins": "Jenkins",
    "unit test": "Unit Testing",
    "unit testing": "Unit Testing",
    "tdd": "Unit Testing",
    "agile": "Agile",
    "scrum": "Agile",
    "system design": "System Design",
    "sql server": "SQL Server",
    "t-sql": "SQL Server",
    # Data
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "relational database": "SQL",
    "relational databases": "SQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "kafka": "Kafka",
    "spark": "Spark",
    "airflow": "Airflow",
    "etl": "ETL",
    "data pipeline": "Data Pipelines",
}

# Canonical ordering for stable output (most relevant first for AI roles).
SKILL_PRIORITY = [
    "Python", "LLMs", "RAG", "Agentic AI", "AI Agents", "LangChain", "LangGraph",
    "Prompt Engineering", "FastAPI", "Pydantic", "React", "TypeScript",
    "AWS", "Azure", "Docker", "SQL", "Machine Learning",
]


def _pattern(variant: str) -> re.Pattern:
    # Bound on alphanumerics rather than \b so "c#", "ci/cd", "next.js" work,
    # and so "rag" doesn't match "leverage" or "vue" match "revenue".
    return re.compile(rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])")


_PATTERNS = [(_pattern(v), c) for v, c in SKILL_VARIANTS.items()]
# "Go" is too common an English word to match case-insensitively.
_GO_RE = re.compile(r"\bGo\b(?!\s+(?:to|for|with|beyond|above)\b)")


def find_skills(text: str) -> list[str]:
    """Return canonical skill names found in text, ordered by priority then name."""
    lowered = text.lower()
    found = {canonical for rx, canonical in _PATTERNS if rx.search(lowered)}
    if _GO_RE.search(text):
        found.add("Go")
    ordered = [s for s in SKILL_PRIORITY if s in found]
    ordered += sorted(s for s in found if s not in ordered)
    return ordered


def rank_skills(text: str) -> list[dict]:
    """Skills in text ranked by how often the posting mentions them.

    A skill named three times across responsibilities and requirements matters
    more than one mentioned once in passing. Ties keep find_skills' order.
    """
    lowered = text.lower()
    counts: dict[str, int] = {}
    for rx, canonical in _PATTERNS:
        n = len(rx.findall(lowered))
        if n:
            counts[canonical] = counts.get(canonical, 0) + n
    go = len(_GO_RE.findall(text))
    if go:
        counts["Go"] = counts.get("Go", 0) + go
    order = {s: i for i, s in enumerate(find_skills(text))}
    ranked = sorted(counts, key=lambda s: (-counts[s], order.get(s, len(order))))
    return [{"skill": s, "mentions": counts[s]} for s in ranked]
