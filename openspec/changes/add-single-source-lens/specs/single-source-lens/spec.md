# Spec Delta

## Purpose
Shows how far one news outlet's version of the news sits from every other outlet's version of the same stories, so a reader
can see what relying on that single source does to their picture of events.

## ADDED Requirements

### Requirement: Same-story comparison
Every lens measure SHALL compare an outlet only with the other comparison-group outlets on the same stories, as a
Mantel–Haenszel rate ratio stratified by story, with a 95% interval and a Cochran–Mantel–Haenszel p-value.

#### Scenario: A story's own drama is not counted as the outlet's
- **GIVEN** an outlet that covers mostly court stories, where every outlet writes loaded headlines
- **WHEN** its loaded-headline ratio is computed
- **THEN** it is compared only with the other outlets' headlines on those same court stories

### Requirement: Comparison group and lens holders
Only active general-news outlets SHALL be in the comparison group and get a lens: registry type print, tv, web or
online; active on at least 50% of the season's days; not on the owner-editable exclusion list, which names a reason
for each excluded outlet.

#### Scenario: A wire agency has no lens
- **WHEN** the page of an outlet on the exclusion list (for example a wire agency) is opened
- **THEN** it shows no lens section but one sentence giving the listed reason

#### Scenario: A part-season outlet is left out
- **GIVEN** an outlet active on fewer than 50% of the season's days
- **WHEN** the lens is built
- **THEN** that outlet is neither compared against nor given a lens

### Requirement: Stories that count
Official-notice stories SHALL be left out using the same rule as the site's notice pages. Loaded-headline and
headline-versus-lede measures SHALL use political headlines only. First-to-report SHALL ignore headlines timed exactly 00:00.

#### Scenario: A court sale notice is not a missed story
- **WHEN** an event is an official notice by the site's rule
- **THEN** it appears in no lens measure and in no missed-stories list

### Requirement: Skips only for complete feeds
A skip SHALL be counted only for outlets whose feed looks complete (active on at least 50% of days, median at least
20 collected headlines per active day, under 10% of active days at its own maximum daily count), and only when no
headline of that outlet within the story's 48-hour window matches the story's headlines at cosine 0.33 or more.

#### Scenario: A capped feed gets no skip measure
- **GIVEN** an outlet whose collected daily count repeatedly hits the same ceiling
- **WHEN** its lens is shown
- **THEN** it has no skip measure and says its collection may be incomplete

#### Scenario: A clustering miss is not a skip
- **GIVEN** an outlet with a matching headline left outside the story's event
- **WHEN** skips are counted
- **THEN** that story is not counted as skipped

### Requirement: Systematic wording only when unmistakable
A finding SHALL be worded as systematic only when it has at least 20 stories, a rate ratio of at least 2 or at most
0.5, q below 0.01 after Benjamini–Hochberg over all outlet-measure tests, and the same direction with ratio at least
1.5 (or at most 1/1.5) in every month with at least 5 stories, over at least 2 such months.

#### Scenario: A strong, lasting pattern is named
- **WHEN** an outlet meets all four conditions on a measure
- **THEN** the sentence says it does this systematically more (or less) often, describing behaviour and never motive

#### Scenario: Otherwise the number speaks
- **WHEN** any condition fails
- **THEN** the sentence gives the ratio and its 95% interval and no strong wording

### Requirement: Distance from the full picture
Each lens SHALL give a distance per slice: 2 to the power of the mean of |log2 ratio| over measures with at least 20
stories, each ratio clipped to [1/4, 4]; an outlet with fewer than 3 such measures SHALL get no distance.

#### Scenario: Thin data gives no distance
- **WHEN** an outlet has only 2 measures with 20 or more stories in a slice
- **THEN** no distance is shown for that slice

### Requirement: AI findings stay outside the score
AI findings about the outlet SHALL be shown beside the lens as additional insights with the AI imzalı label and SHALL
NOT enter any measure, distance or verdict.

#### Scenario: Rejecting an AI finding leaves the distance unchanged
- **WHEN** the owner rejects an AI finding quoting the outlet
- **THEN** the outlet's distance and verdicts stay the same
