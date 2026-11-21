# Spec Delta

## ADDED Requirements

### Requirement: Gold comes from people only
The answer key SHALL hold only human codings, stored under anonymous slots (person letter and pass digit), and SHALL NOT
contain any AI output.

#### Scenario: A name is refused
- **WHEN** a coding with a coder name instead of a slot is appended
- **THEN** it is refused and nothing is written

### Requirement: Blind coding in the desk
A blind item SHALL show only the material being coded and SHALL NOT show the AI's verdict, AI coding, confidence,
quotes, an earlier pass's answers or a link to the event page.

#### Scenario: A behavioural item hides the verdict
- **WHEN** the owner opens a behavioural blind item
- **THEN** it shows the event's headlines and the concept, and no AI result

### Requirement: Same-coder consistency
With one expert, agreement SHALL be measured between two blind passes of the same coder, the second opening no earlier
than 14 days after its packet is made, and reports SHALL name it same-coder consistency.

#### Scenario: The second pass is locked
- **WHEN** the owner opens a second-pass packet before its opening date
- **THEN** the desk shows the date and no items

### Requirement: Safe import
Importing a desk export SHALL refuse the whole file, naming the review key, when any blind review names an unknown
packet or item or carries an unknown value.

#### Scenario: An old export
- **WHEN** an export holds an item that is not in its packet
- **THEN** nothing is imported and the error names that review

### Requirement: Usable only when consistent
A field SHALL be used for measurement, examples or training only when alpha is at least 0.67 on at least 30 items
coded twice.

#### Scenario: Too few items
- **WHEN** 29 items are coded twice
- **THEN** the report says "not usable yet"

### Requirement: No leakage
Few-shot examples and cross-validation folds SHALL never share an event with the items they are tested on.

#### Scenario: Examples from other events
- **WHEN** review tasks are built for a batch
- **THEN** no example comes from an event in that batch
