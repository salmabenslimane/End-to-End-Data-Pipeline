Feedback:

- Think about writing with append in the loop; it is always better to prevent data loss if code crashes
- The data quality verification is neat!
- Please add a screenshot of your dashboard to the readmefile


# Dashboard screenshots : 

![alt text](image.png)

![alt text](image-1.png)

![alt text](image-3.png)

# Observations on supporting the new batch :

1. How many changes were required? 
-> Two additions: format detection (CSV vs JSONL) and a deduplication step. The rest of the pipeline was unchanged.

2. Is it a full refresh or implicit? 
-> It's a full refresh; the old processed file is deleted and rewritten from scratch each run.

3. How are duplicates handled? 
-> r_2002 appears twice? the script now explicitly drops duplicates keeping the first occurrence and logs how many were found.

4. What happens to unknown apps? 
-> com.ghost.notes and com.newnote.ai are not in the apps catalog, they are kept in the reviews but app_name will be None, and a warning is printed.