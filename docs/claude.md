# NY Harbor ULSD Options Data Workflow - STRICT CONSTRAINTS

## Non-Negotiable Constraints

### 1. Input Constraint
- The input to the system must always be clearly defined and unambiguous.
- Local JSON file: glbx-mdp3-20100606-20250617.ohlcv-1d.json (OHLCV data for all instruments)
- This eliminates API dependency and N+1 query timeout issues

### 2. Output Constraint
- The output of the system must match the format of the output and what the output is attempting to do
- /output/final_output.csv

### 3. Throughput Constraint
- The internal calculation process (throughput) must use explicitly defined methods without exception.
- The Goal: To create a single CSV file that contains the daily prices for NY Harbor ULSD (OH) futures and the specific 15-delta call options used in a rolling monthly strategy. The output format should match the example image below (Date in rows, Instruments in columns).

## Required Logic
The script should take a start_date and end_date. For each month in that period, it must:

1. **Identify Target Option**: On the first trading day of Month M, target the options contract for the Month M+2 expiration. (e.g., on July 1, 2025, target the Sept. 2025 OHU5 contract).

2. **Find Specific Strike**: On that same day, calculate the delta for all available call strikes to find the one closest to 0.15.

3. **Pull Price History**: Pull the complete daily price history (ohlcv-1d) for that single identified 15-delta strike from the same day until expiry.

## Deliverable - A Single CSV File
The final output must be a single CSV file with the following structure:
- **Column A**: timestamp (Date)
- **Column B, C, D, etc.**: A separate column for each unique 15-delta option that was identified. The header for each column must be the full instrument symbol (e.g., OHU5 C31500). The price data in each column should only exist for the dates that specific option was active in the strategy.

**CRITICAL: Date Range Logic**
- The CSV dates MUST be constrained by user input date range (user interface contract)
- The CSV structure uses user-specified start_date to end_date
- Option data is populated where available within the user date range
- Empty cells where no option data exists within the user range
- Example: User requests Jan 1-5, CSV shows Jan 1-5 rows with option data populated where available

## Operational Procedure
Execute the following iterative workflow:

### Step 1: Reload Constraints
- Begin each cycle by reloading the "claude.md" file to ensure constant awareness of the constraints.

### Step 2: Execute Workflow
- Run the defined workflow using clear, exact inputs.

### Step 3: Validate Output
- Compare the generated output rigorously against the exact predefined output specification.

### Step 4: Diagnose and Reflect (if mismatch occurs)
- Deeply analyze logs and diagnostics to understand precisely WHY the mismatch occurred.
- Clearly document the exact cause of any deviation from the input, output, or throughput constraints.

### Step 5: Strategize and Implement Fix
- Formulate a concrete, actionable plan to rectify the identified issue.
- Implement this corrective measure.

### Step 6: Repeat Until Perfect
- Re-execute the workflow repeatedly until the output exactly matches the specification without any deviation whatsoever.

## Core Principle
The solution and success of this task are found by unwaveringly maintaining the tension between these three constraints:
- **Clear Inputs**: Absolutely defined and non-negotiable.
- **Clear Outputs**: Exactly formatted, zero tolerance for variance.
- **Clear Throughputs**: Precise calculation methods explicitly specified.

**NEVER violate these constraints.**