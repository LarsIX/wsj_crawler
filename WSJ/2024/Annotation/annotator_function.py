import pandas as pd
from IPython.display import display
import os
from IPython.display import Markdown

def annotate_articles_with_hype(df, min_words=30, save_path=None):
    """
    Interactive function to annotate news articles for AI relevance and hype level.
    Optimized for Jupyter Notebooks using Markdown display.

    Parameters:
    ----------
    df : pd.DataFrame
        DataFrame containing at least the columns:
        'article_id', 'title', 'sub_title', 'corpus'

    min_words : int
        Minimum number of words required in an article to be shown

    save_path : str or None
        If provided, annotations are autosaved to this path after each step

    Returns:
    -------
    pd.DataFrame
        Updated DataFrame with 'label_ai_related' and 'hype_level' columns
    """
    # import necessary libraries
    from IPython.display import display, Markdown   
    
    # Add annotation columns if they don't exist
    if 'label_ai_related' not in df.columns:
        df['label_ai_related'] = None
    if 'hype_level' not in df.columns:
        df['hype_level'] = None

    for i, row in df.iterrows():
        # Skip already labeled entries
        if pd.notnull(row['label_ai_related']):
            continue

        # Skip articles with too few words
        word_count = len(str(row['corpus']).split())
        if word_count < min_words:
            print(f"\n⏭️ Skipping short article ({word_count} words)...")
            continue

        # Display article metadata and cleaned text in Markdown format
        display(Markdown(f"""
---
### 📄 Article {i+1}/{len(df)} — ID: `{row['article_id']}`  
**📰 Title:** {row['title']}  
**📝 Sub-title:** {row['sub_title'] if pd.notnull(row['sub_title']) else "*[No subtitle]*"}  
**📏 Length:** {word_count} words  

---

#### 📚 Cleaned Text:
{row['corpus']}
"""))

        # Prompt user for AI relevance
        label = input("🤖 Is this article related to AI? (y = yes / n = no / s = skip / q = quit): ").strip().lower()

        if label == 'y':
            df.loc[i, 'label_ai_related'] = 1

            # Prompt for hype level only if AI-related
            print("""
📈 HYPE LEVEL (based on tone and framing):
  0 = Low / No hype (technical, neutral, skeptical)
  1 = Moderate hype (optimistic or moderately fearful)
  2 = High hype (bold claims, euphoric or fear-driven urgency)
""")
            hype = input("🔥 What is the AI hype level? (0 / 1 / 2): ").strip()
            if hype in ['0', '1', '2']:
                df.loc[i, 'hype_level'] = int(hype)
            else:
                print("⚠️ Invalid hype input. Marking as missing.")
                df.loc[i, 'hype_level'] = None

        elif label == 'n':
            df.loc[i, 'label_ai_related'] = 0
            df.loc[i, 'hype_level'] = None

        elif label == 's':
            # Skip this entry without annotating
            continue

        elif label == 'q':
            print("⏹️ Annotation manually stopped.")
            break

        else:
            print("⚠️ Invalid input — skipping this article.")
            continue

        # Autosave after every annotation if path is provided
        if save_path:
            try:
                df.to_csv(save_path, index=False)
                print(f"💾 Autosaved to: {os.path.basename(save_path)}")
            except Exception as e:
                print("⚠️ Error while saving:", e)

        print(f"✅ Done. Total labeled: {df['label_ai_related'].notnull().sum()} / {len(df)}")

    print("\n🎉 Annotation session completed.")
    return df[['article_id', 'title', 'sub_title', 'corpus', 'label_ai_related', 'hype_level']]