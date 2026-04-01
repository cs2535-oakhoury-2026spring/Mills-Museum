"""Keyword and term analysis — multilingual, frequency, linguistic patterns."""
import pandas as pd
from collections import Counter
import re

df = pd.read_parquet("src/analysis/data_cache/aat_museum_subset.parquet")

print("=" * 60)
print("VARIANT TERMS — MULTILINGUAL ANALYSIS")
print("=" * 60)

variant_lengths = df["variant_terms"].apply(len)
print(f"  Total terms across all entries: {variant_lengths.sum():,}")
print(f"  Avg variant count per entry: {variant_lengths.mean():.1f}")
print(f"  Median: {variant_lengths.median():.0f}")
print(f"  Max variants: {variant_lengths.max()}")
print()

print("Distribution of variant counts:")
bins = [1, 2, 3, 5, 10, 15, 20, 50]
for i in range(len(bins) - 1):
    count = ((variant_lengths >= bins[i]) & (variant_lengths < bins[i + 1])).sum()
    print(f"  {bins[i]:>2d}-{bins[i + 1] - 1:>2d} variants: {count:>6,} terms")
count = (variant_lengths >= 50).sum()
print(f"  50+  variants: {count:>6,} terms")

df["_vcount"] = variant_lengths
print("\n  Top 10 entries by variant count:")
top_variants = df.nlargest(10, "_vcount")
for _, row in top_variants.iterrows():
    vt = row["variant_terms"]
    print(f"    '{row['preferred_term']}' → {len(vt)} variants")
    sample = [str(v) for v in vt[:6]]
    print(f"      Sample: {', '.join(sample)}...")
df.drop(columns=["_vcount"], inplace=True)

print("\n" + "=" * 60)
print("LANGUAGE DETECTION IN VARIANTS")
print("=" * 60)

cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]')
arabic_pattern = re.compile(r'[\u0600-\u06ff]')
cyrillic_pattern = re.compile(r'[\u0400-\u04ff]')
latin_pattern = re.compile(r'^[a-zA-Zàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ\s\-\',\.]+$')

lang_counts = Counter()
total_variants = 0
for variants in df["variant_terms"]:
    for v in variants:
        total_variants += 1
        v_str = str(v)
        if cjk_pattern.search(v_str):
            lang_counts["CJK (Chinese/Japanese/Korean)"] += 1
        elif arabic_pattern.search(v_str):
            lang_counts["Arabic script"] += 1
        elif cyrillic_pattern.search(v_str):
            lang_counts["Cyrillic"] += 1
        else:
            lang_counts["Latin script"] += 1

print(f"  Total variant terms analyzed: {total_variants:,}")
for lang, count in lang_counts.most_common():
    print(f"  {lang:35s} → {count:>7,} ({100 * count / total_variants:.1f}%)")

print("\n" + "=" * 60)
print("PREFERRED TERM — LINGUISTIC PATTERNS")
print("=" * 60)

terms = df["preferred_term"].str.lower()

plural_terms = terms[terms.str.endswith("s") | terms.str.endswith("es")]
print(f"  Terms ending in 's'/'es' (likely plural): {len(plural_terms):,} ({100 * len(plural_terms) / len(terms):.1f}%)")

adjective_terms = terms[terms.str.contains(r'\b(ish|ous|ive|able|ful|less|al|ic|ian|ean|ese)\b', regex=True)]
print(f"  Terms with adjectival suffixes: {len(adjective_terms):,}")

compound_terms = terms[terms.str.contains(r'\(')]
print(f"  Terms with parenthetical qualifiers: {len(compound_terms):,}")
print("  Examples:", list(df.loc[compound_terms.index[:5], "preferred_term"]))

print("\n" + "=" * 60)
print("FACET-SPECIFIC TERM WORD ANALYSIS")
print("=" * 60)

stopwords = {"and", "of", "the", "for", "in", "with", "a", "an", "to", "or", "by", "on", "at", "as", "is", "its"}

for facet_name in df["hierarchy"].value_counts().head(6).index:
    facet_terms = df[df["hierarchy"] == facet_name]["preferred_term"].str.lower()
    word_freq = Counter()
    for t in facet_terms:
        word_freq.update(w for w in t.split() if w not in stopwords and len(w) > 2)
    top_words = word_freq.most_common(10)
    print(f"\n  [{facet_name}] Top words:")
    for w, c in top_words:
        print(f"    {w:25s} → {c:>4,}")

print("\n" + "=" * 60)
print("SCOPE NOTE — TEMPORAL REFERENCES")
print("=" * 60)

scope_notes = df["scope_note"].dropna()

century_pattern = re.compile(r'(\d+)(?:st|nd|rd|th)\s+centur', re.IGNORECASE)
year_pattern = re.compile(r'\b(1[0-9]{3}|20[0-2][0-9])\b')

century_mentions = Counter()
year_mentions = Counter()

for note in scope_notes:
    for match in century_pattern.finditer(note):
        century_mentions[int(match.group(1))] += 1
    for match in year_pattern.finditer(note):
        year_mentions[int(match.group(1))] += 1

print("Century references in scope notes:")
for century in sorted(century_mentions.keys()):
    bar = "█" * max(1, century_mentions[century] // 5)
    print(f"  {century:>2d}th century: {century_mentions[century]:>4d} mentions {bar}")

print(f"\nYear references found: {sum(year_mentions.values()):,} total")
print("Top 20 most referenced years:")
for year, count in year_mentions.most_common(20):
    print(f"  {year}: {count:>3d} mentions")

print("\n" + "=" * 60)
print("SCOPE NOTE — KEY PHRASES & TOPICS")
print("=" * 60)

all_scope_words = Counter()
for note in scope_notes:
    words = re.findall(r'\b[a-z]{4,}\b', note.lower())
    all_scope_words.update(words)

scope_stopwords = {"used", "also", "with", "that", "this", "from", "have", "been", "were", "they",
                   "their", "which", "when", "made", "such", "more", "than", "into", "some", "type",
                   "term", "refers", "refer", "general", "particularly", "often", "various", "other",
                   "usually", "especially", "types", "including", "typically"}

filtered = {w: c for w, c in all_scope_words.items() if w not in scope_stopwords}
print("Top 30 content words in scope notes:")
for w, c in Counter(filtered).most_common(30):
    print(f"  {w:25s} → {c:>5,}")

print("\n" + "=" * 60)
print("GEOGRAPHIC REFERENCES IN SCOPE NOTES")
print("=" * 60)

geo_patterns = {
    "European": re.compile(r'\b(europe|european|french|italian|english|german|spanish|dutch|greek|roman|british|scandinavian)\b', re.I),
    "Asian": re.compile(r'\b(asia|asian|chinese|japanese|indian|korean|persian|thai|vietnamese|indonesian|tibetan)\b', re.I),
    "African": re.compile(r'\b(africa|african|egyptian|north africa|west africa|saharan)\b', re.I),
    "Americas": re.compile(r'\b(america|american|native american|mesoamerican|south american|pre-columbian)\b', re.I),
    "Middle Eastern": re.compile(r'\b(middle east|islamic|ottoman|arab|mesopotamian|babylonian|assyrian)\b', re.I),
}

geo_counts = Counter()
for note in scope_notes:
    for region, pattern in geo_patterns.items():
        if pattern.search(note):
            geo_counts[region] += 1

print("Regional mentions in scope notes:")
for region, count in geo_counts.most_common():
    bar = "█" * max(1, count // 20)
    print(f"  {region:20s} → {count:>5,} notes {bar}")
