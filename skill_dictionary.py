"""Canonical skills, aliases, and learning resources for the analyzer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    name: str
    category: str
    aliases: tuple[str, ...]
    resource: str
    exercise: str


SKILLS = (
    Skill("Python", "Programming languages", ("python",), "https://docs.python.org/3/tutorial/", "Write a small command-line utility."),
    Skill("Java", "Programming languages", ("java",), "https://dev.java/learn/", "Build a small object-oriented console application."),
    Skill("C", "Programming languages", ("c", "c language"), "https://en.cppreference.com/w/c", "Implement a basic data structure in C."),
    Skill("C++", "Programming languages", ("c++", "cpp"), "https://en.cppreference.com/w/", "Implement a small program using standard containers."),
    Skill("JavaScript", "Programming languages", ("javascript", "js", "ecmascript"), "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "Build an interactive browser feature."),
    Skill("TypeScript", "Programming languages", ("typescript",), "https://www.typescriptlang.org/docs/", "Add static types to a small JavaScript module."),
    Skill("HTML", "Web development", ("html",), "https://developer.mozilla.org/en-US/docs/Learn/HTML", "Create a semantic page for a small project."),
    Skill("CSS", "Web development", ("css",), "https://developer.mozilla.org/en-US/docs/Learn/CSS", "Style the page responsively."),
    Skill("React", "Web development", ("react", "react.js", "reactjs"), "https://react.dev/learn", "Create a component with local state."),
    Skill("Angular", "Web development", ("angular",), "https://angular.dev/tutorials", "Build a small component-based page."),
    Skill("Node.js", "Web development", ("node.js", "nodejs"), "https://nodejs.org/en/learn", "Create a small HTTP endpoint."),
    Skill("Express.js", "Web development", ("express.js", "expressjs", "express"), "https://expressjs.com/en/starter/installing.html", "Build a small REST endpoint."),
    Skill("REST API", "Web development", ("rest api", "rest apis", "restful api", "restful apis"), "https://www.rfc-editor.org/rfc/rfc9110", "Design and test a resource-based API."),
    Skill("Web development", "Web development", ("web development", "web dev"), "https://developer.mozilla.org/en-US/docs/Learn", "Build and deploy a small accessible web page."),
    Skill("SQL", "Databases", ("sql", "structured query language"), "https://www.postgresql.org/docs/current/tutorial.html", "Write queries that join and aggregate sample data."),
    Skill("MySQL", "Databases", ("mysql",), "https://dev.mysql.com/doc/", "Create a small relational schema and query it."),
    Skill("PostgreSQL", "Databases", ("postgresql", "postgres", "postgre sql"), "https://www.postgresql.org/docs/current/tutorial.html", "Model data and write a few joins."),
    Skill("MongoDB", "Databases", ("mongodb", "mongo db"), "https://www.mongodb.com/docs/manual/", "Store and query a small document collection."),
    Skill("Database management", "Databases", ("database management", "database administration"), "https://www.postgresql.org/docs/current/", "Design a schema with constraints and indexes."),
    Skill("Data analysis", "Data and AI", ("data analysis", "data analytics"), "https://pandas.pydata.org/docs/getting_started/index.html", "Summarize a public dataset and explain findings."),
    Skill("NumPy", "Data and AI", ("numpy",), "https://numpy.org/doc/stable/user/quickstart.html", "Use arrays to calculate descriptive statistics."),
    Skill("Pandas", "Data and AI", ("pandas",), "https://pandas.pydata.org/docs/getting_started/index.html", "Clean and summarize a small CSV dataset."),
    Skill("Machine learning", "Data and AI", ("machine learning", "ml"), "https://scikit-learn.org/stable/getting_started.html", "Train and evaluate a simple baseline classifier."),
    Skill("Deep learning", "Data and AI", ("deep learning", "dl"), "https://pytorch.org/tutorials/beginner/basics/intro.html", "Train a small model on a standard learning dataset."),
    Skill("Natural language processing", "Data and AI", ("natural language processing", "nlp"), "https://huggingface.co/learn/nlp-course/chapter1/1", "Build a basic text classification experiment."),
    Skill("Generative AI", "Data and AI", ("generative ai", "gen ai"), "https://ai.google.dev/gemini-api/docs", "Compare generated answers against a small evaluation set."),
    Skill("Git", "Development tools", ("git",), "https://git-scm.com/doc", "Practice branching, merging, and resolving a small conflict."),
    Skill("GitHub", "Development tools", ("github",), "https://docs.github.com/en/get-started", "Publish a project with a useful README."),
    Skill("Docker", "Development tools", ("docker",), "https://docs.docker.com/get-started/", "Containerize a small application."),
    Skill("Linux", "Development tools", ("linux",), "https://linuxjourney.com/", "Use shell tools to inspect and process files."),
    Skill("Postman", "Development tools", ("postman",), "https://learning.postman.com/docs/introduction/overview/", "Create a collection that tests API responses."),
    Skill("Visual Studio Code", "Development tools", ("visual studio code", "vscode"), "https://code.visualstudio.com/docs", "Configure a project with debugging and formatting."),
    Skill("Data structures and algorithms", "Computer science fundamentals", ("data structures and algorithms", "dsa"), "https://www.cs.usfca.edu/~galles/visualization/Algorithms.html", "Implement and compare a search or sorting algorithm."),
    Skill("Algorithms", "Computer science fundamentals", ("algorithms", "algorithm design"), "https://www.cs.usfca.edu/~galles/visualization/Algorithms.html", "Compare two approaches to the same problem."),
    Skill("Object-oriented programming", "Computer science fundamentals", ("object oriented programming", "oop", "oops", "oop s"), "https://docs.python.org/3/tutorial/classes.html", "Model a small domain with classes and clear responsibilities."),
    Skill("DBMS", "Computer science fundamentals", ("dbms", "database management system", "database management systems"), "https://www.postgresql.org/docs/current/", "Explain normalization and apply it to a small schema."),
    Skill("Operating systems", "Computer science fundamentals", ("operating systems", "operating system", "os concepts"), "https://pages.cs.wisc.edu/~remzi/OSTEP/", "Explore process and scheduling behavior with a small exercise."),
    Skill("Computer networks", "Computer science fundamentals", ("computer networks", "networking"), "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview", "Trace a browser request and describe its protocol steps."),
    Skill("Communication", "Professional skills", ("communication", "communicate"), "https://www.skillsyouneed.com/ips/communication-skills.html", "Practice explaining a technical decision concisely."),
    Skill("Teamwork", "Professional skills", ("teamwork", "team work", "collaboration"), "https://www.skillsyouneed.com/ips/team-working.html", "Use a shared issue and review workflow on a small task."),
    Skill("Problem-solving", "Professional skills", ("problem solving", "problem-solving"), "https://www.skillsyouneed.com/ips/problem-solving.html", "Document how you break down and test a problem."),
    Skill("Leadership", "Professional skills", ("leadership",), "https://www.skillsyouneed.com/lead/leadership-skills.html", "Plan and facilitate a small collaborative task."),
    Skill("AWS", "Cloud and DevOps", ("aws", "amazon web services"), "https://docs.aws.amazon.com/", "Deploy a small sample using an AWS free-tier eligible service."),
    Skill("Microsoft Azure", "Cloud and DevOps", ("microsoft azure", "ms azure", "azure"), "https://learn.microsoft.com/en-us/azure/", "Complete a small cloud deployment tutorial."),
    Skill("Google Cloud", "Cloud and DevOps", ("google cloud", "gcp"), "https://cloud.google.com/docs", "Deploy a small sample using Google Cloud documentation."),
    Skill("CI/CD", "Cloud and DevOps", ("ci cd", "continuous integration", "continuous delivery", "continuous deployment"), "https://docs.github.com/en/actions", "Add a workflow that runs tests on every change."),
    Skill("Kubernetes", "Cloud and DevOps", ("kubernetes", "k8s"), "https://kubernetes.io/docs/tutorials/", "Deploy a sample app to a local cluster."),
)

SKILLS_BY_NAME = {skill.name: skill for skill in SKILLS}
