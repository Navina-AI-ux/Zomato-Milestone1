# Project Context: AI-Powered Restaurant Recommendation System

> Source: [Docs/problemStatement.txt](Docs/problemStatement.txt)  
> Use case inspired by **Zomato**

## Overview

Build an **AI-powered restaurant recommendation service** that intelligently suggests restaurants based on user preferences by combining **structured restaurant data** with a **Large Language Model (LLM)**.

## Objective

Design and implement an application that:

1. Takes user preferences (location, budget, cuisine, ratings, and more)
2. Uses a real-world dataset of restaurants
3. Leverages an LLM to generate personalized, human-like recommendations
4. Displays clear and useful results to the user

## Data Source

| Item | Detail |
|------|--------|
| Dataset | Zomato restaurant dataset on Hugging Face |
| URL | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |

### Relevant Fields (from dataset)

Extract and use fields such as:

- Restaurant name
- Location
- Cuisine
- Cost
- Rating
- (Other applicable fields from the dataset)

## User Input

Collect the following preferences from the user:

| Preference | Examples / Notes |
|------------|------------------|
| **Location** | Delhi, Bangalore |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional preferences** | family-friendly, quick service, etc. |

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract relevant fields (name, location, cuisine, cost, rating, etc.)

### 2. User Input

- Collect user preferences as listed above

### 3. Integration Layer

- Filter and prepare relevant restaurant data based on user input
- Pass structured results into an LLM prompt
- Design a prompt that helps the LLM **reason** and **rank** options

### 4. Recommendation Engine

Use the LLM to:

- Rank restaurants
- Provide explanations (why each recommendation fits the user)
- Optionally summarize choices

### 5. Output Display

Present top recommendations in a user-friendly format. Each recommendation should include:

| Field | Description |
|-------|-------------|
| **Restaurant Name** | Name of the restaurant |
| **Cuisine** | Type of cuisine |
| **Rating** | Restaurant rating |
| **Estimated Cost** | Cost estimate for the user |
| **AI-generated explanation** | Why this restaurant was recommended |

## Architecture Summary

```
User Preferences
      │
      ▼
┌─────────────────┐     ┌──────────────────┐
│  Data Ingestion │────▶│  Filtered Data   │
│  (Hugging Face) │     │  (by preferences)│
└─────────────────┘     └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ Integration Layer│
                        │ (prompt + context)│
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ Recommendation   │
                        │ Engine (LLM)     │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ Output Display   │
                        │ (ranked results) │
                        └──────────────────┘
```

## Key Requirements Checklist

- [ ] Load Zomato dataset from Hugging Face
- [ ] Preprocess and extract structured restaurant fields
- [ ] Accept user preferences (location, budget, cuisine, rating, extras)
- [ ] Filter dataset based on user input
- [ ] Build LLM prompt with filtered structured data
- [ ] Use LLM to rank, explain, and optionally summarize recommendations
- [ ] Display top results with name, cuisine, rating, cost, and AI explanation

## Out of Scope (not specified in problem statement)

- Specific tech stack (language, framework, UI)
- LLM provider or model choice
- Authentication or user accounts
- Deployment target

These decisions are left to the implementation phase unless specified elsewhere.
