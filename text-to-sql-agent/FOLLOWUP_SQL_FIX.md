# Follow-up SQL Display Fix

## ✅ Issue Resolved

**Problem:** When user asks a follow-up visualization question, the "Generated SQL & Confidence" section was being updated to show "Using cached results from previous query" instead of keeping the original SQL query visible.

**User Request:** "When performing a followup do not update the Generated SQL section, leave it as it's still using that same SQL result."

---

## 🔧 Solution Implemented

### Changes Made:

#### 1. **Added `sql_display` to Cache** (`src/ui/gradio_simple.py`)

**Before:**
```python
last_query = {"sql": None, "data": None, "columns": None}
```

**After:**
```python
last_query = {"sql": None, "data": None, "columns": None, "sql_display": None}
```

This stores the formatted SQL display string along with the query results.

---

#### 2. **Store SQL Display When Query Executes**

**Before:**
```python
# Store last query for follow-ups
last_query = {"sql": sql, "data": rows, "columns": columns}
```

**After:**
```python
# Create SQL display for the accordion
sql_display = f"**Confidence:** {confidence:.2f}\n\n```sql\n{sql}\n```"

# Store last query for follow-ups (including SQL display)
last_query = {"sql": sql, "data": rows, "columns": columns, "sql_display": sql_display}
```

Now the exact SQL display (with confidence score) is saved when a query is first executed.

---

#### 3. **Reuse Original SQL Display on Follow-ups**

**Before:**
```python
# Keep the same SQL display
sql_display = f"**Using cached results from previous query**\n\n*{len(rows)} rows × {len(columns)} columns*"

return new_history, sql_display, SCHEMA, viz_wrapped
```

**After:**
```python
# Keep the original SQL display from when query was executed
sql_display = last_query.get("sql_display", "")

return new_history, sql_display, SCHEMA, viz_wrapped
```

On follow-up visualization requests, the original SQL display is reused unchanged.

---

## 📊 User Experience Flow

### Before Fix:

```
User: "What are the top 10 customers by lifetime value?"
  ↓
UI Shows:
  - Chat: Results table
  - SQL Section: "Confidence: 0.95
                 SELECT * FROM customers ORDER BY lifetime_value DESC LIMIT 10"
  
User: "show that as a bar chart"
  ↓
UI Updates:
  - Chat: "Visualization created"
  - SQL Section: "Using cached results from previous query" ❌ CHANGED!
                 "10 rows × 4 columns"
```

**Problem:** Original SQL query is replaced with generic message.

---

### After Fix:

```
User: "What are the top 10 customers by lifetime value?"
  ↓
UI Shows:
  - Chat: Results table
  - SQL Section: "Confidence: 0.95
                 SELECT * FROM customers ORDER BY lifetime_value DESC LIMIT 10"
  
User: "show that as a bar chart"
  ↓
UI Updates:
  - Chat: "Visualization created"
  - SQL Section: "Confidence: 0.95
                 SELECT * FROM customers ORDER BY lifetime_value DESC LIMIT 10"
                 ✅ UNCHANGED! Original SQL still visible
```

**Solution:** SQL display remains exactly as it was when the query was first executed.

---

## ✅ Benefits

1. **Context Preservation** - Users can always see the original SQL query
2. **Better Understanding** - Users know exactly which query generated the data
3. **Debugging Aid** - If visualization looks wrong, SQL is still visible for review
4. **Professional UX** - Consistent display, not replaced with generic message

---

## 🧪 Testing

### Test Case 1: Basic Follow-up
```
1. Ask: "Show top 10 customers by lifetime value"
2. Check SQL section shows: "SELECT * FROM customers..." with confidence
3. Ask: "show as bar chart"
4. Verify SQL section UNCHANGED - still shows same query
5. Ask: "make it a pie chart"
6. Verify SQL section STILL UNCHANGED
```

### Test Case 2: Multiple Questions
```
1. Ask: "Show revenue by plan"
2. SQL section shows revenue query
3. Ask: "show as pie chart"
4. SQL section unchanged (revenue query still visible)
5. Ask: "What are the top cities?"
6. SQL section UPDATES (new query generated)
7. Ask: "visualize as bar chart"
8. SQL section unchanged (cities query still visible)
```

### Test Case 3: Clear and Restart
```
1. Ask question + follow-up
2. Click "Clear" button
3. SQL section cleared (empty)
4. Ask new question
5. SQL section shows new query
```

---

## 📁 Files Modified

**`src/ui/gradio_simple.py`**

### Lines Changed:

1. **Line 61** - Added `sql_display` to cache initialization
2. **Line 401** - Changed follow-up to reuse `sql_display` from cache
3. **Lines 432-436** - Store `sql_display` when query executes
4. **Line 520** - Removed duplicate `sql_display` creation (cleanup)
5. **Line 528** - Added `sql_display` to clear_chat reset

---

## 🎯 Code Changes Summary

```python
# 1. Initialize with sql_display field
last_query = {
    "sql": None, 
    "data": None, 
    "columns": None, 
    "sql_display": None  # NEW
}

# 2. When query executes - store SQL display
sql_display = f"**Confidence:** {confidence:.2f}\n\n```sql\n{sql}\n```"
last_query = {
    "sql": sql, 
    "data": rows, 
    "columns": columns, 
    "sql_display": sql_display  # NEW - store formatted display
}

# 3. On follow-up - reuse original SQL display
if is_viz_request and last_query["data"]:
    # ... create visualization ...
    sql_display = last_query.get("sql_display", "")  # NEW - reuse original
    return new_history, sql_display, SCHEMA, viz_wrapped

# 4. On clear - reset sql_display too
def clear_chat():
    global last_query
    last_query = {
        "sql": None, 
        "data": None, 
        "columns": None, 
        "sql_display": None  # NEW - reset this too
    }
```

---

## ✨ Result

The SQL query accordion now **persists the original query** across all follow-up visualization requests, providing better context and a more professional user experience.

**Status: ✅ Complete and tested!**
