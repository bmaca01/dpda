#!/usr/bin/env bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# 1. Create the DPDA
print_status "Creating DPDA..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/dpda/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Arithmetic Expression DPDA",
    "description": "DPDA for parsing arithmetic expressions with +, -, *, / and parentheses"
  }')

# Extract the ID using jq
DPDA_ID=$(echo "$RESPONSE" | jq -r '.id')

# Check if we got a valid ID
if [ -z "$DPDA_ID" ] || [ "$DPDA_ID" = "null" ]; then
  print_error "Failed to create DPDA or extract ID"
  print_error "Response: $RESPONSE"
  exit 1
fi

print_info "Created DPDA with ID: $DPDA_ID"

# 2. Set the states (14 states: 0-13)
print_status "Setting states..."
curl -s -X POST http://localhost:8000/api/dpda/${DPDA_ID}/states \
  -H "Content-Type: application/json" \
  -d '{
    "states": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"],
    "initial_state": "0",
    "accept_states": ["13"]
  }' | jq -r '.message // "States configured"'

# 3. Set the alphabets
print_status "Setting alphabets..."
curl -s -X POST http://localhost:8000/api/dpda/${DPDA_ID}/alphabets \
  -H "Content-Type: application/json" \
  -d '{
    "input_alphabet": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "+", "-", "*", "/", "(", ")"],
    "stack_alphabet": ["$", "S", "E", "T", "F", "E1", "T1", "+", "-", "*", "/", ")", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "("],
    "initial_stack_symbol": "$"
  }' | jq -r '.message // "Alphabets configured"'

# 4. Add transitions
print_status "Adding transitions..."

# Helper function to add transition silently
add_transition() {
    curl -s -X POST http://localhost:8000/api/dpda/${DPDA_ID}/transition \
      -H "Content-Type: application/json" \
      -d "$1" > /dev/null
}

# State 0: ε,ε -> 1, push S,$
add_transition '{
    "from_state": "0",
    "input_symbol": null,
    "stack_top": null,
    "to_state": "1",
    "stack_push": ["S", "$"]
  }'

# State 1: ε,S -> E
add_transition '{
    "from_state": "1",
    "input_symbol": null,
    "stack_top": "S",
    "to_state": "2",
    "stack_push": ["E"]
  }'

# State 2: ε,E -> 3, push T,E1
add_transition '{
    "from_state": "2",
    "input_symbol": null,
    "stack_top": "E",
    "to_state": "3",
    "stack_push": ["T", "E1"]
  }'

# State 3: ε,T -> 4, push F,T1
add_transition '{
    "from_state": "3",
    "input_symbol": null,
    "stack_top": "T",
    "to_state": "4",
    "stack_push": ["F", "T1"]
  }'

# State 4: Transitions for digits 0-9
for digit in 0 1 2 3 4 5 6 7 8 9; do
  add_transition "{
      \"from_state\": \"4\",
      \"input_symbol\": \"$digit\",
      \"stack_top\": \"F\",
      \"to_state\": \"4\",
      \"stack_push\": []
    }"
done

# State 4: (,F -> 2, push E,)
add_transition '{
    "from_state": "4",
    "input_symbol": "(",
    "stack_top": "F",
    "to_state": "2",
    "stack_push": ["E", ")"]
  }'

# State 4: ε,T1 -> ε
add_transition '{
    "from_state": "4",
    "input_symbol": null,
    "stack_top": "T1",
    "to_state": "5",
    "stack_push": []
  }'

# State 5: *,ε -> 6, push *,F,T1
add_transition '{
    "from_state": "5",
    "input_symbol": "*",
    "stack_top": null,
    "to_state": "6",
    "stack_push": ["*", "F", "T1"]
  }'

# State 5: /,ε -> 7, push /,F,T1
add_transition '{
    "from_state": "5",
    "input_symbol": "/",
    "stack_top": null,
    "to_state": "7",
    "stack_push": ["/", "F", "T1"]
  }'

# State 5: +,ε -> ε
add_transition '{
    "from_state": "5",
    "input_symbol": "+",
    "stack_top": null,
    "to_state": "8",
    "stack_push": []
  }'

# State 5: -,ε -> ε
add_transition '{
    "from_state": "5",
    "input_symbol": "-",
    "stack_top": null,
    "to_state": "9",
    "stack_push": []
  }'

# State 5: ε,E1 -> ε
add_transition '{
    "from_state": "5",
    "input_symbol": null,
    "stack_top": "E1",
    "to_state": "12",
    "stack_push": []
  }'

# State 6: ε,* -> ε
add_transition '{
    "from_state": "6",
    "input_symbol": null,
    "stack_top": "*",
    "to_state": "4",
    "stack_push": []
  }'

# State 7: ε,/ -> ε
add_transition '{
    "from_state": "7",
    "input_symbol": null,
    "stack_top": "/",
    "to_state": "4",
    "stack_push": []
  }'

# State 8: ε,E1 -> 10, push +,T,E1
add_transition '{
    "from_state": "8",
    "input_symbol": null,
    "stack_top": "E1",
    "to_state": "10",
    "stack_push": ["+", "T", "E1"]
  }'

# State 9: ε,E1 -> 11, push -,T,E1 (-- for minus)
add_transition '{
    "from_state": "9",
    "input_symbol": null,
    "stack_top": "E1",
    "to_state": "11",
    "stack_push": ["-", "T", "E1"]
  }'

# State 10: ε,+ -> ε
add_transition '{
    "from_state": "10",
    "input_symbol": null,
    "stack_top": "+",
    "to_state": "3",
    "stack_push": []
  }'

# State 11: ε,- -> ε
add_transition '{
    "from_state": "11",
    "input_symbol": null,
    "stack_top": "-",
    "to_state": "3",
    "stack_push": []
  }'

# State 12: ),) -> ε
add_transition '{
    "from_state": "12",
    "input_symbol": ")",
    "stack_top": ")",
    "to_state": "4",
    "stack_push": []
  }'

# State 12: ε,$ -> ε
add_transition '{
    "from_state": "12",
    "input_symbol": null,
    "stack_top": "$",
    "to_state": "13",
    "stack_push": []
  }'

print_info "All transitions added"

# 5. Validate the DPDA
print_status "Validating DPDA..."
VALIDATION=$(curl -s -X POST http://localhost:8000/api/dpda/${DPDA_ID}/validate)
IS_VALID=$(echo "$VALIDATION" | jq -r '.is_valid')
if [ "$IS_VALID" = "true" ]; then
    print_info "DPDA is valid!"
else
    print_error "DPDA validation failed:"
    echo "$VALIDATION" | jq -r '.errors[]' 2>/dev/null || echo "$VALIDATION"
fi

# 6. Test with sample inputs
print_status "Testing with sample inputs..."

# Function to test an input string
test_input() {
    local input="$1"
    local expected="$2"

    RESULT=$(curl -s -X POST http://localhost:8000/api/dpda/${DPDA_ID}/compute \
      -H "Content-Type: application/json" \
      -d "{
        \"input_string\": \"$input\",
        \"show_trace\": false
      }")

    ACCEPTED=$(echo "$RESULT" | jq -r '.accepted')

    if [ "$ACCEPTED" = "$expected" ]; then
        echo -e "  ${GREEN}✓${NC} '$input' -> $ACCEPTED (expected: $expected)"
    else
        echo -e "  ${RED}✗${NC} '$input' -> $ACCEPTED (expected: $expected)"
    fi
}

print_info "Testing valid expressions (should accept):"
test_input "1+1" "true"
test_input "(1+1)" "true"
test_input "(2+5)-4*3/2" "true"
test_input "(((2+4)*3*(2-9))/5+3*(8-2+1))*9+1/(2+3*5)+8" "true"

print_info "Testing invalid expressions (should reject):"
test_input "11+1" "false"
test_input "1++1" "false"
test_input "((1+1)" "false"
test_input "(1+1))" "false"
test_input ")(1)" "false"

# 7. Export the DPDA definition (optional)
print_status "Exporting DPDA definition..."
EXPORT=$(curl -s -X GET http://localhost:8000/api/dpda/${DPDA_ID}/export)
echo "$EXPORT" | jq -c '.data | {states: .states | length, transitions: .transitions | length}' | \
    xargs -I {} echo "  Exported DPDA: {}"

# 8. Show DPDA info
print_status "DPDA Summary:"
curl -s -X GET http://localhost:8000/api/dpda/${DPDA_ID} | jq '{
    id: .id,
    name: .name,
    num_states: .num_states,
    num_transitions: .num_transitions,
    is_complete: .is_complete
}'

print_info "DPDA testing complete!"