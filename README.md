# Tokopedia User Reviews Insights

This project analyzes 5 years of Tokopedia’s user reviews from the Google Play Store to uncover product issues, recurring feedback themes, sentiment patterns, and emerging complaints. It will also include a semantic search/RAG system to query insights directly from the review corpus.

## Project Status  
Currently, two core stages of the pipeline are completed:

### **Step 0 — Data Scraping**  
The project retrieves large-scale Indonesian user reviews from the Tokopedia app (`com.tokopedia.tkpd`) using the `google-play-scraper` library. Reviews are fetched in batches using continuation tokens and aggregated into a structured dataset containing the review text, score, and timestamp. Google Play only surfaces one review per user, ensuring built-in uniqueness without requiring explicit review IDs.

### **Step 1 — Data Cleaning**  
All raw reviews undergo a comprehensive normalization pipeline using a custom `CleaningPipeline` class. This includes Unicode normalization, lowercase conversion, typo correction, slang normalization, emoji mapping, laughter handling, compound-word splitting, stopword removal, whitespace normalization, and low-information filtering. The result is a standardized, noise-free text corpus
