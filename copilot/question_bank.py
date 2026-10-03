"""Most-asked interview questions: a curated, offline bank.

BEHAVIORAL questions come up in almost every interview; TECHNICAL is keyed by
the canonical skill names in skills.py, so a JD's top skills map straight to
the questions most often asked about them.
"""

BEHAVIORAL = [
    "Tell me about yourself.",
    "Why do you want to work here, and why this role?",
    "Walk me through the project you're most proud of. What was your specific contribution?",
    "Tell me about a time you disagreed with a teammate or lead. How did you resolve it?",
    "Describe a time you missed a deadline or a project went wrong. What did you learn?",
    "Tell me about a time you had to learn a new technology quickly.",
    "How do you handle unclear or changing requirements?",
    "Describe a time you explained a technical issue to a non-technical stakeholder.",
    "How do you prioritise when you have several urgent tasks at once?",
    "Tell me about a production incident you handled. What did you do first?",
    "How do you approach code reviews — both giving and receiving feedback?",
    "Where do you see yourself in 3–5 years?",
    "What are your salary expectations?",
    "Do you have any questions for us?",
]

TECHNICAL: dict[str, list[str]] = {
    "C#": [
        "What's the difference between a class and a struct (reference vs value types)?",
        "Explain async/await. What happens if you call .Result on a Task?",
        "What's the difference between IEnumerable and IQueryable?",
        "Explain interfaces vs abstract classes — when would you use each?",
        "How does garbage collection work in .NET? What is IDisposable / using for?",
        "What are delegates, events and lambdas?",
    ],
    ".NET": [
        "What's the difference between .NET Framework and .NET (Core / 6 / 8)?",
        "Explain dependency injection and the service lifetimes: transient, scoped, singleton.",
        "How do you handle configuration and secrets across environments?",
        "How would you diagnose a memory leak or high CPU in a .NET app?",
    ],
    "ASP.NET Core": [
        "Explain the ASP.NET Core middleware pipeline. How do you write custom middleware?",
        "How do you implement authentication and authorization (JWT, policies, roles)?",
        "Filters vs middleware — what's the difference and when do you use each?",
        "How do you do global exception handling and model validation in a Web API?",
        "How would you version a Web API?",
    ],
    "Entity Framework": [
        "Code-first vs database-first — and how do migrations work?",
        "What's the N+1 problem? Explain eager, lazy and explicit loading.",
        "How do you improve EF Core query performance (AsNoTracking, projections, compiled queries)?",
        "How does EF Core handle concurrency conflicts?",
    ],
    "LINQ": [
        "What is deferred execution in LINQ?",
        "Difference between First, FirstOrDefault, Single and SingleOrDefault?",
        "How do GroupBy and Join work in LINQ?",
    ],
    "SQL": [
        "Explain the different types of JOINs with an example.",
        "What are indexes? Clustered vs non-clustered — and when can an index hurt?",
        "Write a query to find the second-highest salary (or top N per group).",
        "WHERE vs HAVING? What are window functions (ROW_NUMBER, RANK)?",
        "What is normalisation? When would you denormalise?",
        "Explain transactions, ACID and isolation levels.",
        "How do you find and fix a slow query?",
    ],
    "SQL Server": [
        "Stored procedures vs functions vs views — when do you use each?",
        "How do you read an execution plan? What are table scans vs index seeks?",
        "How do you handle deadlocks?",
        "Temp tables vs table variables vs CTEs?",
    ],
    "PostgreSQL": [
        "How does PostgreSQL's MVCC work, and why does VACUUM matter?",
        "When would you use JSONB columns? How do you index them?",
        "How do you analyse a slow query with EXPLAIN ANALYZE?",
    ],
    "MongoDB": [
        "When would you choose MongoDB over a relational database?",
        "Embedding vs referencing documents — how do you decide?",
        "How do indexes and the aggregation pipeline work?",
    ],
    "Redis": [
        "What would you use Redis for? Explain cache-aside.",
        "How do you handle cache invalidation and expiry?",
        "What are Redis persistence options (RDB vs AOF)?",
    ],
    "APIs": [
        "What makes an API RESTful? Explain HTTP methods and status codes.",
        "PUT vs PATCH vs POST — and what is idempotency?",
        "How do you secure an API (OAuth2, JWT, API keys, rate limiting)?",
        "How do you handle pagination, filtering and errors in an API?",
        "How do you version and document an API (OpenAPI/Swagger)?",
        "How do you handle retries and timeouts when consuming a third-party API?",
    ],
    "REST APIs": [
        "REST vs SOAP vs GraphQL — trade-offs?",
        "How do you design resource URLs and status codes for a REST API?",
        "What is HATEOAS, and do you use it in practice?",
    ],
    "GraphQL": [
        "GraphQL vs REST — when would you choose GraphQL?",
        "How do you avoid the N+1 problem in GraphQL resolvers?",
    ],
    "Microservices": [
        "Monolith vs microservices — when are microservices the wrong choice?",
        "How do services communicate (sync vs async, REST vs messaging)?",
        "How do you handle data consistency across services (sagas, outbox)?",
        "How do you trace and debug a request across multiple services?",
        "What is an API gateway and why use one?",
    ],
    "System Design": [
        "Design a URL shortener.",
        "How would you design a system to handle 10x the current traffic?",
        "Explain caching layers, load balancing and horizontal vs vertical scaling.",
        "How do you design for failure (retries, circuit breakers, idempotency)?",
    ],
    "Docker": [
        "What's the difference between an image and a container?",
        "How do you write a small, secure Dockerfile (multi-stage builds)?",
        "How do containers talk to each other? Explain volumes and networks.",
        "Docker vs a virtual machine?",
    ],
    "Kubernetes": [
        "Explain pods, deployments, services and ingress.",
        "How do rolling updates and rollbacks work?",
        "How do you manage config and secrets in Kubernetes?",
        "What are liveness vs readiness probes?",
    ],
    "CI/CD": [
        "Walk me through a CI/CD pipeline you've built. What stages did it have?",
        "Continuous delivery vs continuous deployment?",
        "How do you do zero-downtime deployments (blue-green, canary)?",
        "How do you handle database migrations in a pipeline?",
        "How do you roll back a bad production release?",
    ],
    "DevOps": [
        "What does DevOps mean to you in day-to-day work?",
        "How do you monitor an application in production? What do you alert on?",
        "What is infrastructure as code and why use it?",
    ],
    "Azure DevOps": [
        "How do you set up build and release pipelines in Azure DevOps (YAML)?",
        "How do you manage environments, approvals and variable groups?",
    ],
    "Git": [
        "Merge vs rebase — when do you use each?",
        "What branching strategy do you prefer (GitFlow, trunk-based) and why?",
        "How do you resolve a merge conflict? How do you undo a bad commit?",
    ],
    "GitLab": [
        "How do you structure a .gitlab-ci.yml pipeline (stages, jobs, artifacts)?",
        "How do merge requests, approvals and protected branches work in your workflow?",
        "How do you manage environments and controlled production releases in GitLab?",
    ],
    "GitHub Actions": [
        "How do you structure a GitHub Actions workflow? Jobs vs steps?",
        "How do you manage secrets and reusable workflows?",
    ],
    "Jenkins": [
        "Declarative vs scripted Jenkins pipelines?",
        "How do you manage credentials and agents in Jenkins?",
    ],
    "Terraform": [
        "How does Terraform state work, and how do you share it safely?",
        "What are modules and workspaces?",
        "How do you handle drift between state and real infrastructure?",
    ],
    "Azure": [
        "Which Azure services have you used, and for what?",
        "App Service vs Azure Functions vs AKS — how do you choose?",
        "How do you manage secrets in Azure (Key Vault, managed identities)?",
        "How do you monitor Azure apps (Application Insights, Log Analytics)?",
        "Service Bus vs Event Grid vs Event Hubs?",
    ],
    "AWS": [
        "Which AWS services have you used, and for what?",
        "EC2 vs Lambda vs ECS/EKS — how do you choose?",
        "Explain IAM roles and policies. How do you apply least privilege?",
        "SQS vs SNS vs EventBridge?",
        "How do you design for high availability on AWS?",
    ],
    "GCP": [
        "Which GCP services have you used, and for what?",
        "Cloud Run vs GKE vs Cloud Functions?",
    ],
    "Python": [
        "List vs tuple vs set vs dict — when do you use each?",
        "What are decorators and generators? Give an example.",
        "Explain the GIL. Threading vs multiprocessing vs asyncio?",
        "How do *args and **kwargs work?",
        "Mutable default arguments — what's the gotcha?",
        "How do you manage dependencies and virtual environments?",
    ],
    "FastAPI": [
        "Why FastAPI over Flask or Django? How does it use Pydantic?",
        "How does dependency injection work in FastAPI?",
        "When do you use async def vs def for endpoints?",
    ],
    "Django": [
        "Explain the Django request/response cycle and middleware.",
        "How do you avoid N+1 queries (select_related, prefetch_related)?",
        "How do Django migrations work?",
    ],
    "Flask": [
        "How do you structure a larger Flask app (blueprints, app factory)?",
        "How do you handle authentication in Flask?",
    ],
    "Java": [
        "Explain OOP principles with Java examples.",
        "HashMap internals — how does it handle collisions?",
        "Checked vs unchecked exceptions?",
        "How does Spring dependency injection work?",
    ],
    "JavaScript": [
        "Explain closures with an example.",
        "var vs let vs const? What is hoisting?",
        "How does the event loop work? Promises vs async/await?",
        "== vs === ? How does `this` work?",
        "What is event delegation?",
    ],
    "TypeScript": [
        "Interfaces vs type aliases?",
        "What are generics? Give a real use case.",
        "What are union types and type narrowing?",
        "unknown vs any vs never?",
    ],
    "React": [
        "Explain the virtual DOM and reconciliation.",
        "useState vs useEffect vs useMemo vs useCallback — when do you use each?",
        "How do you manage state across components (Context, Redux, React Query)?",
        "Why do lists need keys?",
        "How do you find and fix unnecessary re-renders?",
        "Controlled vs uncontrolled components?",
    ],
    "Angular": [
        "Explain components, modules and services in Angular.",
        "How does change detection work? What is OnPush?",
        "Observables vs Promises — how do you use RxJS operators?",
        "How do you handle routing guards and lazy loading?",
    ],
    "Node.js": [
        "How does Node's event loop handle concurrency on a single thread?",
        "How do you handle errors in async Node code?",
        "How would you scale a Node service (cluster, workers, horizontal)?",
    ],
    "Kafka": [
        "Explain topics, partitions and consumer groups.",
        "How do you guarantee ordering and avoid duplicate processing?",
        "Kafka vs a traditional message queue (RabbitMQ, Service Bus)?",
    ],
    "Unit Testing": [
        "How do you decide what to unit test vs integration test?",
        "How do you use mocks/stubs? When is mocking a bad idea?",
        "What is TDD and do you use it?",
    ],
    "Agile": [
        "Describe your team's Scrum process. What worked and what didn't?",
        "How do you estimate stories? What do you do when estimates are wrong?",
    ],
    "Machine Learning": [
        "Explain overfitting and how to prevent it.",
        "Precision vs recall — when do you optimise for each?",
        "How do you deploy and monitor a model in production?",
    ],
    "LLMs": [
        "How do you reduce hallucinations in an LLM application?",
        "How do you evaluate LLM output quality?",
        "Fine-tuning vs RAG vs prompt engineering — when do you use each?",
    ],
    "RAG": [
        "Walk me through a RAG pipeline end to end.",
        "How do you choose chunk size and embedding model?",
        "How do you evaluate retrieval quality?",
    ],
}


def common_questions(skills: list[str], per_skill: int = 5) -> dict:
    """Behavioral questions plus the most-asked technical questions for each
    skill that has a bank entry (in the given order)."""
    return {
        "behavioral": BEHAVIORAL,
        "technical": [{"skill": s, "questions": TECHNICAL[s][:per_skill]}
                      for s in dict.fromkeys(skills) if s in TECHNICAL],
    }


def full_bank() -> dict:
    return {"behavioral": BEHAVIORAL,
            "technical": [{"skill": s, "questions": q} for s, q in sorted(TECHNICAL.items())]}
