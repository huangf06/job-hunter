# Take-Home & Technical Prep

## ENPICOM's GitHub Take-Home Assignments

Found on github.com/ENPICOM -- these reveal EXACTLY what they test:

### 1. Senior Engineer Assessment (TypeScript + React + PostgreSQL)
**Repo**: `software-engineer-technical-assessment`
- Build a REST API for storing/searching DNA sequences
- Implement **Levenshtein distance** fuzzy matching
- Build a **React SPA** frontend
- **Must use plain SQL, no ORM** (strong engineering philosophy signal!)
- Open question: "How would you scale for many concurrent users and large data volumes?"
- Evaluated on: clean code, pragmatism, honesty about gaps

### 2. Python Bioinformatics Challenge
**Repo**: `quality-per-position-challenge`
- Parse **FASTQ files** (DNA sequencing data format)
- Calculate per-position quality statistics (min, max, Q1, Q3, median, mean)
- Handle **Phred+33 encoding**, variable-length reads, gzip compression
- Return boxplot-ready data structures

### 3. Intern Assessment
**Repo**: `software-internship-technical-assessment`
- Luhn algorithm in TypeScript using ts-node

## Their Utility Code (Open Source)
- **s3-archive-stream**: NodeJS utility to stream-zip S3 objects (TypeScript, AWS SDK)
- **jira-details-action**: GitHub-to-JIRA integration (TypeScript)
- **docker-manifest-action**: Docker manifest linking (TypeScript)

## What This Tells Us
1. **TypeScript is their primary language** -- every custom repo is TypeScript
2. **Plain SQL over ORM** -- they value understanding your data layer
3. **React for frontend** -- SPA architecture
4. **Bioinformatics = Python** -- separate track for bio-focused work
5. **DNA/sequence data** is their bread and butter
6. **They value honesty** -- "be honest about gaps" in assessment criteria

## Key Technical Concepts to Understand

### Levenshtein Distance
Edit distance between two strings -- minimum number of single-character edits (insertions, deletions, substitutions) to change one string into another. Used for fuzzy DNA sequence matching.

### FASTQ Format
Standard format for storing DNA sequencing output:
```
@SEQ_ID
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
!''*((((***+))%%%++)(%%%%).1***-+*''))**55CCF>>>>>>CCCCCCC65
```
Line 1: Sequence identifier
Line 2: Raw sequence (ACGT bases)
Line 3: "+" separator
Line 4: Quality scores (Phred+33 encoded ASCII)

### Phred+33 Encoding
Quality score = ASCII value - 33. Higher = better quality.
- ASCII '!' (33) = Phred 0 (worst)
- ASCII 'I' (73) = Phred 40 (excellent)

### Immune Repertoire Basics
- **BCR**: B-cell receptor (produces antibodies)
- **TCR**: T-cell receptor (recognizes antigens)
- **CDR3**: Complementarity-determining region 3 -- the most variable part, key for antigen binding
- **Clonotype**: A unique receptor sequence -- used to track immune cell populations
- **Repertoire diversity**: How many different receptor sequences an individual has

## Note
This section is for context only. Jorrit is NOT testing you on Monday. But understanding their domain shows genuine interest and enables deeper conversation.
