# Citation Format Reference

Quick reference for supported citation formats in validate-citations.

---

## APA 7th Edition

**In-text:** (Author, Year) or Author (Year)

**Examples:**
- Single author: (Smith, 2023)
- Two authors: (Smith & Jones, 2023)
- 3+ authors: (Smith et al., 2023)
- Direct quote: (Smith, 2023, p. 45)
- Multiple works: (Smith, 2023; Jones, 2022)

**Reference list:**
```
Author, A. A. (Year). Title of work: Capital letter also for subtitle. Publisher.
Author, A. A., & Author, B. B. (Year). Title of article. Journal Name, volume(issue), page-page. https://doi.org/xxx
```

**Common errors:**
- Missing year in parentheses
- Using "&" in text (should be "and")
- Using "and" in parentheses (should be "&")
- Not using "et al." for 3+ authors

---

## IEEE

**In-text:** [1], [2], [3-5]

**Examples:**
- Single reference: [1]
- Multiple: [1], [3]
- Range: [1]-[5]
- Combined: [1], [3]-[5], [7]

**Reference list:**
```
[1] A. Author, "Title of article," Journal Name, vol. X, no. Y, pp. 1-10, Month Year.
[2] A. Author and B. Author, Title of Book. City: Publisher, Year.
```

**Common errors:**
- Inconsistent numbering order
- Missing volume/issue numbers
- Wrong bracket style (use square brackets)

---

## Chicago (Author-Date)

**In-text:** (Author Year) or (Author Year, page)

**Examples:**
- Basic: (Smith 2023)
- With page: (Smith 2023, 45)
- Multiple works: (Smith 2023; Jones 2022)

**Reference list:**
```
Author, First. Year. "Title of Article." Journal Name volume (issue): pages.
Author, First. Year. Title of Book. Place: Publisher.
```

**Common errors:**
- Adding comma between author and year
- Missing period after year in reference list

---

## Vancouver

**In-text:** (1), (2), (1-5)

**Examples:**
- Single: (1)
- Multiple: (1,3)
- Range: (1-5)
- Combined: (1,3-5,7)

**Reference list:**
```
1. Author AA, Author BB. Title of article. Journal Name. Year;volume(issue):pages.
2. Author AA. Title of book. Edition. Place: Publisher; Year.
```

**Common errors:**
- Wrong numeral style (should be parentheses, not brackets)
- Missing semicolon in journal citations
- Author names not abbreviated

---

## Format Detection Heuristics

The skill auto-detects format by:

1. **Check parenthetical patterns:**
   - `(Author, Year)` → APA
   - `(Author Year)` → Chicago
   - `[N]` square brackets → IEEE
   - `(N)` numeric parentheses → Vancouver

2. **Check reference list format:**
   - Numbered with brackets → IEEE
   - Numbered without brackets → Vancouver
   - Alphabetical with year after author → APA/Chicago

3. **If ambiguous:** Prompt user to confirm format

---

## Cross-Reference Table

| Feature | APA | IEEE | Chicago | Vancouver |
|---------|-----|------|---------|-----------|
| In-text style | (Author, Year) | [N] | (Author Year) | (N) |
| Numbering | No | Yes | No | Yes |
| Order | Alphabetical | Citation order | Alphabetical | Citation order |
| Et al. threshold | 3+ authors | 3+ authors | 4+ authors | 3+ authors |
| DOI required | Yes | Recommended | Recommended | Recommended |

---

*Last updated: 2026-01-18*
