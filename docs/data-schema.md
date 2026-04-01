# Data File Intent

## `config.json`

Global rules and pacing:
- total months
- stat bounds
- failure thresholds
- base living cost
- debt and savings rates
- event odds
- budget stances
- opening paths
- autosave name

## `cities.json`

City archetypes for v1.

Each city defines:
- housing cost multiplier
- living cost multiplier
- transport cost multiplier
- family support bonus
- opportunity text
- pressure text
- career income biases

## `careers.json`

Career-track content.

Each career defines:
- entry path restrictions
- minimum transport access
- education / credential requirements
- optional minimum GPA requirements
- tier ladder

Each tier defines:
- monthly income
- stress / energy profile
- life satisfaction effect
- promotion target
- optional minimum GPA requirement

## `education.json`

Education lanes for v1.

Each program defines:
- monthly cost
- monthly stress / energy effect
- duration
- earned credential
- opening path access
- applicable careers

Runtime education state also tracks:
- academic standing
- college GPA for the college lane
- earned credentials / completed programs

## `housing.json`

Housing options.

Each option defines:
- monthly cost
- move-in cost
- stress / life satisfaction effect
- roommate-event pressure
- quality score
- hometown requirement if any
- minimum family support if any

## `transport.json`

Transport options.

Each option defines:
- monthly cost
- upfront cost
- stress effect
- access level
- reliability
- repair-event weight
- quality score

## `focus_actions.json`

Monthly focus choices.

Each focus action defines:
- income multiplier
- promotion progress bonus
- education progress bonus
- stress / energy effect
- life satisfaction effect

## `events.json`

Monthly life events.

Each event defines:
- eligibility filters
- minimum month / stress / debt rules
- immediate stat effects
- optional temporary modifier
- log text

Valid stat-effect keys:
- `cash`
- `savings`
- `debt`
- `stress`
- `energy`
- `life_satisfaction`
- `family_support`
- `promotion_progress`
- `education_progress`

## `presets.json`

Starting archetypes.

Each preset defines:
- starting cash / savings / debt
- starting stress / energy / life satisfaction
- starting family support
- academic strength

## `data/balance/difficulty_modifiers.json`

Difficulty-level runtime modifiers:
- starting cash / debt bonus
- income multiplier
- housing / transport multiplier
- stress multiplier
- progression multiplier
- interest multiplier

## `data/balance/scoring_weights.json`

Final Life Position Score weights:
- financial position
- career and credentials
- housing stability
- debt burden
- wellbeing
