import pandas as pd
import json
import re
import os

# Re-running the script logic directly to ensure it works in this environment
def parse_markdown_table(file_path):
    records = []
    if not os.path.exists(file_path):
        return records
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        if '|' in line and '---' not in line and 'Year' not in line:
            parts = [p.strip() for p in line.split('|')]
            # Filter out empty strings from split if they are at the ends
            if parts[0] == '': parts = parts[1:]
            if parts[-1] == '': parts = parts[:-1]
            
            if len(parts) >= 3: # Minimum: Year, Title, DOI/URL
                try:
                    # Try to detect format based on column count
                    if len(parts) >= 5: # Detailed: #, Year, Title, Authors, DOI, URL
                        year = parts[1]
                        title = parts[2]
                        authors = parts[3]
                        doi = parts[4]
                        url = parts[5] if len(parts) > 5 else ""
                    else: # Summary: #, Year, Title, DOI
                        year = parts[1]
                        title = parts[2]
                        authors = "Unknown"
                        doi = parts[3]
                        url = ""
                    
                    if title and year and len(year) == 4:
                        records.append({
                            'year': year,
                            'title': title,
                            'authors': authors,
                            'doi': doi,
                            'url': url,
                            'source': os.path.basename(file_path).replace('.md', '')
                        })
                except:
                    continue
    return records

base_path = r'c:\github\masters\systematic-literatur-review\search_logs'
export_path = r'c:\github\masters\systematic-literatur-review\search_exports'

all_records = []
for src in ['arxiv.md', 'openalex.md', 'crossref.md']:
    all_records.extend(parse_markdown_table(os.path.join(base_path, src)))

df = pd.DataFrame(all_records)
initial = len(df)

# Deduplicate
df['doi_norm'] = df['doi'].str.lower().str.strip()
df['title_norm'] = df['title'].str.lower().str.replace(r'[^a-z0-9]', '', regex=True)

# Keep first occurrence
df_final = df.drop_duplicates(subset=['doi_norm'], keep='first')
df_final = df_final.drop_duplicates(subset=['title_norm', 'year'], keep='first')
final = len(df_final)

# Save
df_final[['year', 'title', 'authors', 'doi', 'url', 'source']].to_csv(os.path.join(export_path, 'records.csv'), index=False)

summary = {
    'initial_records': initial,
    'final_records': final,
    'duplicates_removed': initial - final,
    'sources': {
        'arxiv': len([r for r in all_records if r['source'] == 'arxiv']),
        'openalex': len([r for r in all_records if r['source'] == 'openalex']),
        'crossref': len([r for r in all_records if r['source'] == 'crossref'])
    }
}
with open(os.path.join(export_path, 'dedup_summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)

# BibTeX
with open(os.path.join(export_path, 'citations.bib'), 'w', encoding='utf-8') as f:
    for i, row in df_final.iterrows():
        cite_key = f"ref_{i}"
        f.write(f"@article{{{cite_key},\n")
        f.write(f"  title = {{{row['title']}}},\n")
        f.write(f"  author = {{{row['authors']}}},\n")
        f.write(f"  year = {{{row['year']}}},\n")
        if row['doi']: f.write(f"  doi = {{{row['doi']}}},\n")
        if row['url']: f.write(f"  url = {{{row['url']}}},\n")
        f.write(f"  note = {{Source: {row['source']}}}\n")
        f.write(f"}}\n\n")

print(f"Deduplication complete. {final} records saved.")
