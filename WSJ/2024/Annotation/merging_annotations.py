from IPython.display import display, Markdown

def resolve_label_disagreements_AI(df_author, df_annotator):
    """
    Compares AI-related labels between author and annotator DataFrames,
    displays disagreements, and interactively allows corrections.

    Parameters:
    - df_author: DataFrame with 'article_id' and 'label_ai_related' from the author.
    - df_annotator: DataFrame with 'article_id', 'label_ai_related', and 'corpus' from the annotator.

    Returns:
    - df_ai_level_merge: A corrected copy of df_annotator with updated labels and tracking columns.
    """

    # Create a copy to apply corrections
    df_ai_level_merge = df_annotator.copy()
    df_ai_level_merge['modified'] = 0
    df_ai_level_merge['hype_level_change'] = 0

    # Merge to find disagreements
    merged = df_author[['article_id', 'label_ai_related']].merge(
        df_annotator[['article_id', 'label_ai_related', 'corpus']],
        on='article_id',
        suffixes=('_author', '_annotator')
    )

    # Filter for label mismatches
    disagreements = merged[merged['label_ai_related_author'] != merged['label_ai_related_annotator']]
    print(f"🔍 Number of disagreements: {disagreements.shape[0]}")

    # Iterate and prompt for corrections
    for i, (_, row) in enumerate(disagreements.iterrows()):
        md_text = f"""
---
### Article {i+1}/{len(disagreements)}

**Article ID:** `{row['article_id']}`  
**Author Label:** `{row['label_ai_related_author']}`  
**Annotator Label:** `{row['label_ai_related_annotator']}`

---

#### Text:

{row['corpus']}

---
"""
        display(Markdown(md_text))

        change_label = input("🔄 Change label (default=annotator) ? (y/n): ").strip().lower()
        if change_label == 'y':
            new_label = 0 if row['label_ai_related_annotator'] == 1 else 1
            df_ai_level_merge.loc[df_ai_level_merge['article_id'] == row['article_id'], 'label_ai_related'] = new_label
            df_ai_level_merge.loc[df_ai_level_merge['article_id'] == row['article_id'], 'modified'] = 1
            print(f"✅ Label changed to: {new_label}")
        else:
            print("❌ Label not changed")

    return df_ai_level_merge

def resolve_hype_disagreements(df_author, df_ai_level_mergen):
    """
    Compares hype_level between author and annotator DataFrames,
    displays disagreements, and interactively allows corrections.

    Parameters:
    - df_author: DataFrame with 'article_id' and 'hype_level' from the author.
    - df_ai_level_mergen: DataFrame with 'article_id', 'hype_level', 'label_ai_related', 'corpus',
                          and tracking columns 'modified' and 'hype_level_change'.

    Returns:
    - df_final: A corrected copy of df_ai_level_mergen with updated hype levels and tracking columns.
    """

    # Create working copy
    df_final = df_ai_level_mergen.copy()
    if 'hype_level_change' not in df_final.columns:
        df_final['hype_level_change'] = 0
    if 'modified' not in df_final.columns:
        df_final['modified'] = 0

    # Merge to find disagreements
    merged = df_author[['article_id', 'hype_level']].merge(
        df_ai_level_mergen[['article_id', 'hype_level', 'label_ai_related', 'modified', 'corpus']],
        on='article_id',
        suffixes=('_author', '_annotator')
    )

    # Filter for mismatches
    disagreements = merged[merged['hype_level_author'] != merged['hype_level_annotator']]
    print(f"🔍 Number of hype level disagreements: {disagreements.shape[0]}")

    for i, (_, row) in enumerate(disagreements.iterrows()):
        md_text = f"""
---
### Article {i+1}/{len(disagreements)}

**Article ID:** `{row['article_id']}`  
**Author Hype Level:** `{row['hype_level_author']}`  
**Annotator Hype Level:** `{row['hype_level_annotator']}`  
**AI-related Label:** `{row['label_ai_related']}`  
**Label changed from annotator's to author's view?:** `{"Yes" if row['modified'] == 1 else "No"}`

---

#### Text:

{row['corpus']}

---
"""
        display(Markdown(md_text))

        change = input("🔄 Change hype level (default=annotator)? (y/n): ").strip().lower()
        if change == 'y':
            while True:
                try:
                    new_value = int(input("Enter new hype level (0 = none, 1 = moderate, 2 = strong): ").strip())
                    if new_value not in [0, 1, 2]:
                        raise ValueError
                    break
                except ValueError:
                    print("❗ Invalid input. Please enter 0, 1, or 2.")

            df_final.loc[df_final['article_id'] == row['article_id'], 'hype_level'] = new_value
            df_final.loc[df_final['article_id'] == row['article_id'], 'hype_level_change'] = 1
            print(f"✅ Hype level updated to: {new_value}")
        else:
            print("❌ Hype level not changed")

    return df_final
