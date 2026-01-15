import pandas as pd
import json
import re
import os

def parse_markdown_table(file_path):
    records = []
    if not os.path.exists(file_path):
        return records
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the table start
    table_started = False
    for line in lines:
        if '|' in line and '---' not in line and 'Year' not in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                # parts[0] is empty, parts[1] is #, parts[2] is Year, parts[3] is Title, parts[4] is Authors, parts[5] is DOI, parts[6] is URL
                try:
                    year = parts[2]
                    title = parts[3]
                    authors = parts[4]
                    doi = parts[5]
                    url = parts[6]
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

def deduplicate(records):
    df = pd.DataFrame(records)
    initial_count = len(df)
    
    # Normalize DOI
    df['doi_norm'] = df['doi'].str.lower().str.strip()
    df.loc[df['doi_norm'] == '', 'doi_norm'] = None
    
    # Normalize Title for fuzzy match
    df['title_norm'] = df['title'].str.lower().str.replace(r'[^a-z0-9]', '', regex=True)
    
    # Deduplicate by DOI first
    df_dedup = df.drop_duplicates(subset=['doi_norm'], keep='first')
    
    # Then by Title+Year
    df_dedup = df_dedup.drop_duplicates(subset=['title_norm', 'year'], keep='first')
    
    final_count = len(df_dedup)
    return df_dedup, initial_count, final_count

def main():
    base_path = r'c:\github\masters\systematic-literatur-review\search_logs'
    export_path = r'c:\github\masters\systematic-literatur-review\search_exports'
    
    all_records = []
    sources = ['arxiv.md', 'openalex.md', 'crossref.md']
    
    for src in sources:
        all_records.extend(parse_markdown_table(os.path.join(base_path, src)))
    
    df_final, initial, final = deduplicate(all_records)
    
    # Save CSV
    df_final[['year', 'title', 'authors', 'doi', 'url', 'source']].to_csv(os.path.join(export_path, 'records.csv'), index=False)
    
    # Save Summary
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
    
    # Best-effort BibTeX
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

if __name__ == "__main__":
    main()
