# Faithfulness Analysis

## Overview
This repository contains scripts for processing, analyzing, and indexing text data using Pyserini, transformers, and other machine learning techniques.

## File Breakdown

### 1. `combine_caches.py`
- **Purpose**: Merges two dictionaries stored as `.pkl` files and saves the combined dictionary.
- **Inputs**: `dict11.pkl`, `dict12.pkl`
- **Outputs**: `cache_offline.pkl`

### 2. `index_by_max_round.py`
- **Purpose**: Processes a CSV file, converts it into JSONL, and runs Pyserini indexing & encoding.
- **Inputs**: `tommy_data.csv`
- **Outputs**: Indexed JSONL files in `pyserini_output_*` directories

### 3. `new_inference_1.py`
- **Purpose**: Uses `Meta-Llama-3-8B-Instruct` for text inference and updates a CSV file with LLaMa2 based texts.
- **Inputs**: `part_1.csv`
- **Outputs**: Modified CSV with text predictions

### 4. `text_changes_analysis.py`
- **Purpose**: Compares text differences and visualizes them using heatmaps.
- **Inputs**: `bot_followup_*.csv`
- **Outputs**: Analysis results and visualization

### 5. `text_handling_funcs.py`
- **Purpose**: Implements functions for truncating text while maintaining full sentences.
- **Inputs**: Raw text
- **Outputs**: Processed text

### 6. `TrueTeacher.py`
- **Purpose**: Processes feature data and runs Pyserini retrieval with FAISS & Lucene searchers.
- **Inputs**: `feature_data_asrc_new.csv`, `feature_data_asrc_new_F.csv`
- **Outputs**: Enhanced CSVs with faithfulness evaluation metrics

### 7. `TrueTeacher_utils.py`
- **Purpose**: Implements retrieval functions, model initialization, and cache handling.
- **Dependencies**: Requires Pyserini, T5, and FAISS.

## Installation & Usage
```bash
pip install -r requirements.txt
python index_by_max_round.py
python TrueTeacher.py
```

## Dependencies
- `torch`
- `transformers`
- `pyserini`
- `pandas`
- `numpy`
- `tqdm`
- `matplotlib`
