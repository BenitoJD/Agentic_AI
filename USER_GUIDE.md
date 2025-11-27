# Performance Bottleneck Analyzer - User Guide

## Overview

The Performance Bottleneck Analyzer helps performance engineers quickly identify application bottlenecks by analyzing logs and metrics data using AI. Instead of manually sifting through thousands of log lines, the AI automatically detects performance issues and provides actionable recommendations.

---

## Getting Started

### 1. Access the Application

- Open your web browser
- Navigate to: `http://localhost:5173`
- You'll see a chat interface similar to ChatGPT

### 2. First Time Setup

When you first open the application, you'll see a welcome message explaining:
- What types of files you can upload
- How to ask questions
- What the system can analyze

---

## Step-by-Step Usage

### Step 1: Upload Your Logs or Metrics Files

**Supported File Types:**
- **Log Files**: `.log`, `.txt` (application logs, error logs, access logs)
- **Metrics Files**: `.json` (Prometheus, custom JSON metrics), `.csv`, `.tsv` (time-series data)
- **Other Formats**: `.pdf`, `.docx`, `.xlsx` (for reports or documentation)

**How to Upload:**
1. Click the **"Upload logs/metrics"** button (usually in the menu or header)
2. Select your file(s) from your computer
3. Wait for the upload confirmation message
   - You'll see: "Processed X chunks from filename.log"
   - The system automatically processes and indexes your files

**What Happens Behind the Scenes:**
- Files are parsed and split into searchable chunks
- Content is converted to embeddings for semantic search
- Files are stored in a vector database for quick retrieval

---

### Step 2: Ask Questions About Performance

Once files are uploaded, you can ask questions in natural language. The AI will search through your uploaded files and analyze them.

**Example Questions:**

**General Analysis:**
- "What bottlenecks do you see in the logs?"
- "Analyze the performance issues"
- "What's causing slow performance?"
- "Identify all performance problems"

**Specific Bottleneck Types:**
- "Are there any CPU bottlenecks?"
- "Check for memory leaks"
- "Find network-related issues"
- "Identify database performance problems"
- "Look for disk I/O bottlenecks"

**Time-Based Queries:**
- "What happened between 2pm and 3pm?"
- "Show me errors from the last hour"
- "Analyze performance during peak hours"

**Specific Components:**
- "Why is the API endpoint /users slow?"
- "What's wrong with the payment service?"
- "Analyze the database connection pool"

---

### Step 3: Review the Analysis Results

The AI will provide:

**1. Executive Summary** (Always at the start)
- High-level overview of the analysis (2-3 sentences)
- Total number of bottlenecks found
- Most critical issues identified (top 2-3)
- Overall system health assessment
- Key recommendations at a glance

**2. Detailed Analysis**
- A detailed explanation of what it found
- Context about the performance issues
- Breakdown of each problem identified

**2. Structured Bottleneck Reports** (when available)
Each bottleneck is displayed as a card showing:

- **Type Icon**: Visual indicator (CPU, Memory, Network, Database, Disk I/O)
- **Severity Badge**: 
  - 🔴 **Critical** - Immediate action required
  - 🟠 **High** - Significant impact, should be addressed soon
  - 🟡 **Medium** - Moderate impact, plan to fix
  - 🔵 **Low** - Minor issue, monitor
- **Description**: What the bottleneck is
- **Evidence**: Specific log lines or metrics that support the finding
- **Recommendations**: Actionable steps to resolve the issue

**3. Source Files**
- List of files that were analyzed
- Clickable references to the original data

**4. Confidence Level**
- **High**: AI is very confident in the analysis
- **Medium**: Reasonable confidence, but may need verification
- **Low**: AI suggests follow-up questions to clarify

---

## Example Workflow

### Scenario: Analyzing Application Slowdown

**1. Upload Files:**
```
User uploads:
- app.log (5000 lines)
- error.log (200 lines)
- metrics.json (Prometheus metrics)
```

**2. Ask Question:**
```
"What's causing the application to be slow?"
```

**3. AI Response:**

**## Executive Summary**
"I've analyzed your application logs and identified 2 critical bottlenecks affecting system performance. The primary issue is a memory bottleneck causing OutOfMemoryErrors, combined with slow database queries that are exhausting the connection pool. Overall system health is poor with 95% memory utilization and query response times exceeding 15 seconds. Immediate actions required: increase JVM heap size and optimize database queries."

**Detailed Analysis:**

**Bottleneck Cards:**

**🔴 Critical - Memory Bottleneck**
- **Evidence:**
  - "OutOfMemoryError at 2024-11-27 14:23:15"
  - "Memory usage: 95% at line 1234"
  - "GC overhead exceeded 98%"
- **Recommendations:**
  - Increase JVM heap size from 2GB to 4GB
  - Check for memory leaks in the user session handler
  - Review object retention in cache layer

**🟠 High - Database Bottleneck**
- **Evidence:**
  - "Query execution time: 15.3s at line 567"
  - "Connection pool exhausted at 14:30:00"
  - "Slow query detected: SELECT * FROM users WHERE..."
- **Recommendations:**
  - Add index on users.email column
  - Increase database connection pool size
  - Optimize the SELECT query to use specific columns

**Sources:**
- app.log
- error.log
- metrics.json

---

## Advanced Features

### 1. Follow-up Questions

If the AI's confidence is low or the question is ambiguous, it will suggest follow-up questions like:
- "Which specific service are you concerned about?"
- "What time period should I analyze?"
- "Are you seeing issues with a particular endpoint?"

### 2. Conversation Context

The AI remembers your conversation:
- Previous questions and answers
- Files you've discussed
- Context from earlier analysis

You can ask follow-up questions like:
- "Tell me more about that memory issue"
- "What about the database problem?"
- "How do I fix the CPU bottleneck?"

### 3. Multiple File Analysis

Upload multiple files and the AI will:
- Cross-reference data across files
- Find patterns that span multiple logs
- Correlate metrics with log events

### 4. File Management

Ask the system:
- "What files do I have uploaded?"
- "List my uploaded files"
- The system will show all indexed files

---

## Tips for Best Results

### 1. Upload Relevant Files
- Include error logs, not just info logs
- Upload metrics files alongside logs for better context
- Include files from the time period when issues occurred

### 2. Ask Specific Questions
- ✅ Good: "What's causing slow response times in the API?"
- ❌ Less effective: "What's wrong?"

### 3. Use Follow-up Questions
- Build on previous answers
- Ask for more details about specific bottlenecks
- Request clarification on recommendations

### 4. Review Evidence
- Always check the evidence provided
- Verify the log lines match your understanding
- Cross-reference with your monitoring tools

### 5. Multiple Queries
- Ask different questions to get different perspectives
- Try querying by bottleneck type
- Ask about specific time periods

---

## Understanding the Output

### Confidence Levels

**High Confidence (0.8-1.0)**
- Strong evidence found
- Clear patterns identified
- Recommendations are well-supported

**Medium Confidence (0.5-0.8)**
- Some evidence found
- Patterns may need verification
- Recommendations are reasonable but should be validated

**Low Confidence (<0.5)**
- Limited evidence
- AI suggests follow-up questions
- May need more data or clarification

### Bottleneck Severity

**Critical**
- System failures or crashes
- Complete service unavailability
- Data loss risk

**High**
- Significant performance degradation
- User experience severely impacted
- Requires immediate attention

**Medium**
- Noticeable performance issues
- Some user impact
- Should be addressed in near term

**Low**
- Minor performance impact
- May not be immediately noticeable
- Monitor and plan fixes

---

## Troubleshooting

### "LLM unavailable right now"
- Check that your API keys are configured in `backend/.env`
- Verify Gemini API key is valid
- Check backend logs for errors

### "No files found"
- Make sure you've uploaded files first
- Check file format is supported
- Verify upload was successful

### "Low confidence" responses
- Upload more relevant files
- Ask more specific questions
- Provide context about what you're looking for

### Files not being analyzed
- Check file format is supported
- Verify files contain readable text/data
- Try re-uploading the file

---

## Example Use Cases

### Use Case 1: Production Incident Analysis

**Situation:** Application crashed during peak hours

**Steps:**
1. Upload: `app.log`, `error.log`, `system-metrics.json`
2. Ask: "What caused the application crash at 3pm?"
3. Review: AI identifies memory leak and provides fix recommendations

### Use Case 2: Performance Regression

**Situation:** API response times increased after deployment

**Steps:**
1. Upload: `access.log`, `api-metrics.csv`
2. Ask: "Why are API response times slow after the latest deployment?"
3. Review: AI finds database query issues and suggests optimizations

### Use Case 3: Capacity Planning

**Situation:** Need to understand resource usage patterns

**Steps:**
1. Upload: `metrics.json` (CPU, memory, network data)
2. Ask: "What are the resource bottlenecks under load?"
3. Review: AI identifies CPU as the limiting factor with recommendations

---

## Best Practices

1. **Regular Analysis**: Upload logs regularly, not just during incidents
2. **Historical Comparison**: Keep logs from different time periods for comparison
3. **Comprehensive Data**: Include both logs and metrics for complete picture
4. **Document Findings**: Save important analysis results
5. **Validate Recommendations**: Always verify AI suggestions before implementing

---

## Getting Help

If you encounter issues:
1. Check the browser console for errors
2. Review backend logs
3. Verify API keys are configured
4. Ensure files are in supported formats

---

## Summary

The Performance Bottleneck Analyzer transforms the time-consuming task of log analysis into a quick, AI-powered process. Simply:

1. **Upload** your logs/metrics files
2. **Ask** questions about performance issues
3. **Review** structured bottleneck reports with evidence and recommendations
4. **Act** on the actionable insights provided

The system handles the heavy lifting of parsing, searching, and analyzing, so you can focus on fixing the issues rather than finding them.

