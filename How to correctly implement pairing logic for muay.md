<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# How to correctly implement pairing logic for muay thai?

Use this citation:
9. ВЕСОВЫЕ КАТЕГОРИИ.

9.1. Весовая категория, в которой может выступать тай-боксер определяется тренером и врачом, о чем делается запись во врачебно-контрольной карте, заявке и зачетной классификационной книжке спортсмена.
9.2. Взрослые и юниоры выступают в следующих весовых категориях:
Категории Весовые ограничения

1. Первый наилегчайший вес не ниже 45 кг, но не выше 48 кг
2. Наилегчайший вес не ниже 48 кг, но не выше51 кг
3. Легчайший вес не ниже 51 кг, но не выше 54 кг
4. Полулегкий вес не ниже 54 кг, но не выше 57 кг
5. Легкий вес не ниже 57 кг, но не выше 60 кг
6. Первый полусредний вес не ниже 60 кг, но не выше 63,5 кг
7. Второй полусредний вес не ниже 63,5 кг, но не выше 67 кг
8. Первый средний вес не ниже 67 кг, но не выше 71 кг
9. Средний вес не ниже 71 кг, но не выше 75 кг
10. Полутяжелый вес не ниже 75 кг, но не выше81 кг
11. Первый тяжелый вес не ниже 81 кг, но не выше 86 кг
12. Тяжелый вес не ниже 86 кг, но не выше 91 кг
13. Супертяжелый вес не ниже 91 кг
9.3. В соревнованиях юношей 12-14 лет пары составляются с таким расчетом, чтобы разница в весе у тай-боксеров, имеющих вес до 60 кг, не превышала 2-х кг, от 60 до 70 кг - 3-х кг, от 70 до 80 кг - 4-х кг и свыше 80 кг - 5 кг.
9.4. В соревнованиях юношей 15-16 лет пары составляются с таким расчетом, чтобы разница в весе у тай-боксеров, имеющих вес до 54 кг не превышал 2-х кг, от 54 до 66 кг - 3-х кг. от 66 до74 кг - 4-х кг, от 74 до79 кг - 5-и кг, от 79 до 85 кг - 6-и кг и свыше 85
9.5. Участники командных соревнований могут выступать в смежной (более тяжелой) весовой категории с правом возврата в категорию, указанную в заявке.
9.6. В абсолютных чемпионатах участвуют тай-боксеры свыше 81 кг.

To correctly implement the pairing logic based on the provided text (which appears to be standard Russian Muay Thai Federation rules), you need to handle two distinct systems: **Fixed Weight Classes** for Adults/Juniors and **Weight Difference Limits** for Youths.

Here is the Python implementation strategy, broken down into logical components.

### 1. Define the Constants (The Rules)

First, translate the text into Python dictionaries. This separates the "configuration" from the "logic," making it easier to update later.

```python
# utils/rules.py

# 9.2 Adults (18+) and Juniors (17-18) - Fixed Classes
WEIGHT_CLASSES_ADULT = [
    {"name": "First Flyweight", "min": 45.0, "max": 48.0},
    {"name": "Flyweight", "min": 48.0, "max": 51.0},
    {"name": "Bantamweight", "min": 51.0, "max": 54.0},
    {"name": "Featherweight", "min": 54.0, "max": 57.0},
    {"name": "Lightweight", "min": 57.0, "max": 60.0},
    {"name": "Light Welterweight", "min": 60.0, "max": 63.5},
    {"name": "Welterweight", "min": 63.5, "max": 67.0},
    {"name": "Light Middleweight", "min": 67.0, "max": 71.0},
    {"name": "Middleweight", "min": 71.0, "max": 75.0},
    {"name": "Light Heavyweight", "min": 75.0, "max": 81.0},
    {"name": "Cruiserweight", "min": 81.0, "max": 86.0},
    {"name": "Heavyweight", "min": 86.0, "max": 91.0},
    {"name": "Super Heavyweight", "min": 91.0, "max": 999.0}, # 91+
]

# 9.3 Youths (12-14 years) - Floating pairing logic
def get_max_diff_12_14(weight):
    if weight <= 60: return 2.0
    if weight <= 70: return 3.0
    if weight <= 80: return 4.0
    return 5.0 # Over 80kg

# 9.4 Older Youths (15-16 years) - Floating pairing logic
def get_max_diff_15_16(weight):
    if weight <= 54: return 2.0
    if weight <= 66: return 3.0
    if weight <= 74: return 4.0
    if weight <= 79: return 5.0
    if weight <= 85: return 6.0
    return 99.0 # Over 85 (Usually open, but let's say safely unlimited or set a cap)
```


### 2. The Logic Function

You need a function that takes two fighters and determines if they *can* fight.

```python
# utils/pairing_logic.py
import math

def is_match_valid(f1, f2):
    """
    Checks if two fighters are a valid match based on Rule 9.
    f1, f2 are dicts with keys: 'age', 'weight', 'gender'
    """
    
    # 0. Basic Safety Checks
    if f1['gender'] != f2['gender']:
        return False, "Gender mismatch"
    
    # Age Group Check (Simplify age to match rule groups)
    # Note: In reality, you might allow 16 vs 17, but strict rules usually separate them.
    if abs(f1['age'] - f2['age']) > 2: 
        return False, "Age gap too large"

    avg_weight = (f1['weight'] + f2['weight']) / 2
    weight_diff = abs(f1['weight'] - f2['weight'])

    # --- RULE 9.3: Youths 12-14 ---
    if 12 <= f1['age'] <= 14 and 12 <= f2['age'] <= 14:
        max_allowed = get_max_diff_12_14(avg_weight)
        if weight_diff <= max_allowed:
            return True, "Valid 12-14 match"
        else:
            return False, f"Weight diff {weight_diff}kg exceeds limit {max_allowed}kg"

    # --- RULE 9.4: Youths 15-16 ---
    elif 15 <= f1['age'] <= 16 and 15 <= f2['age'] <= 16:
        max_allowed = get_max_diff_15_16(avg_weight)
        if weight_diff <= max_allowed:
            return True, "Valid 15-16 match"
        else:
            return False, f"Weight diff {weight_diff}kg exceeds limit {max_allowed}kg"

    # --- RULE 9.2: Juniors (17-18) & Adults (19+) ---
    else:
        # They must be in the SAME weight category
        cat1 = get_weight_category(f1['weight'])
        cat2 = get_weight_category(f2['weight'])
        
        if cat1 and cat1 == cat2:
            return True, f"Match in {cat1}"
        
        # 9.5 Exception: Moving up a weight class (Optional Logic)
        # If you want to allow someone to fight ONE category up:
        # if cat2_index == cat1_index + 1: return True (with warning)
        
        return False, f"Different categories: {cat1} vs {cat2}"

def get_weight_category(weight):
    from utils.rules import WEIGHT_CLASSES_ADULT
    for cat in WEIGHT_CLASSES_ADULT:
        if cat['min'] <= weight < cat['max']: # Standard notation [min, max)
            return cat['name']
        if cat['name'] == "Super Heavyweight" and weight >= 91:
            return cat['name']
    return None
```


### 3. The Pairing Algorithm (The looper)

Now you need the engine that loops through your list of fighters and finds the best matches using the logic above.

```python
# utils/matchmaker.py
from utils.pairing_logic import is_match_valid

def generate_pairs(fighters_df):
    """
    fighters_df: Pandas DataFrame containing all available fighters
    """
    # 1. Sort fighters to make matching easier (by Age, then Weight)
    # This helps the greedy algorithm find close matches first
    sorted_fighters = fighters_df.sort_values(by=['Gender', 'Age', 'Weight']).to_dict('records')
    
    matches = []
    unmatched = []
    
    while len(sorted_fighters) > 1:
        current_fighter = sorted_fighters.pop(0) # Take the first one
        best_opponent = None
        best_opponent_idx = -1
        
        # Look for the best match in the remaining list
        for i, opponent in enumerate(sorted_fighters):
            
            # HARD CONSTRAINT: Same Club?
            if current_fighter['Club'] == opponent['Club']:
                continue 
                
            # RULE CHECK: Are they allowed to fight?
            is_valid, reason = is_match_valid(current_fighter, opponent)
            
            if is_valid:
                best_opponent = opponent
                best_opponent_idx = i
                break # Found the first valid match (Greedy approach)
                # For better results, you could calculate a "score" and find the BEST valid match
        
        if best_opponent:
            # Match found!
            matches.append({
                'Red Corner': current_fighter,
                'Blue Corner': best_opponent,
                'Category': reason
            })
            # Remove opponent from the pool
            sorted_fighters.pop(best_opponent_idx)
        else:
            # No match found
            unmatched.append(current_fighter)
            
    # If one person is left at the end
    if sorted_fighters:
        unmatched.extend(sorted_fighters)
        
    return matches, unmatched
```


### 4. How to display this in Streamlit (`app.py`)

When you run this, you will get a list of pairs.

```python
import streamlit as st
from utils.matchmaker import generate_pairs

# ... load df ...

if st.button("Auto-Match"):
    matches, leftovers = generate_pairs(st.session_state.fighters_df)
    
    st.header("Generated Bouts")
    
    # Convert to DataFrame for nice display
    match_data = []
    for m in matches:
        match_data.append({
            "Red Name": m['Red Corner']['Name'],
            "Red Weight": m['Red Corner']['Weight'],
            "Blue Name": m['Blue Corner']['Name'],
            "Blue Weight": m['Blue Corner']['Weight'],
            "Class": m['Category']
        })
        
    st.dataframe(match_data)
    
    if leftovers:
        st.warning(f"Could not pair {len(leftovers)} fighters:")
        st.dataframe(leftovers)
```


### Key Takeaways for this Implementation

1. **Polymorphic Logic**: The code treats 12-14 year olds differently than 18+ adults. This is crucial because adults *must* be in a bracket (e.g., 63.5-67kg), whereas kids just need to be *close* in weight (e.g., 38kg vs 39kg is fine).
2. **Greedy Sort**: By sorting by weight first, the algorithm naturally pairs the 60kg fighter with the 61kg fighter, rather than the 63kg fighter.
3. **Extensibility**: If the rules change (e.g., weight gap increases to 3kg), you only update `utils/rules.py`.
