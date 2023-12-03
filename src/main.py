#!/usr/bin/python3
'''
CS 341-005
Benedikt Macaro
DPDA simulator
'''

class DPDA:
    """
    Class representation of DPDA
    Q: number of states
    SIG: language alphabet
    GAM: stack alphabet
    F: accept states

    d: transitions for each state
    """
    def __init__(self):
        self.Q = -1
        self.SIG = -1
        self.GAM = set('$')
        self.F = -1
        
        self.d = {}

    def set_init(self):
        """
        Prompts user to set Q, SIG, GAM, F.
        return void
        """
        # Get states
        while (self.Q == -1):
            try:
                self.Q = int(input("Enter number of states :\n"))
            except:
                print("Invalid input: number of states must be int")

        # Get input alphabet
        while (self.SIG == -1):
            tmp = set(input(
                "Enter input alphabet as a"
                + " comma-separated list of symbols :\n").strip().split(","))
            if (tmp == ""):
                print("Input alphabet can't be empty")
                continue
            self.SIG = tmp

        self.GAM = self.SIG | self.GAM

        # Get accept states
        while (self.F == -1):
            # For all accept states, delimit by comma, convert to int, store in list.
            try:
                i = set(map(int,
                    input(
                        "Enter accepting states as a "
                        + "comma-separated list of integers :\n").strip().split(",")))

                m = max(i)
                if (m > self.Q - 1):
                    print(
                        "invalid state {0}; enter a value between {1} and {2}"
                        .format(m, 0, self.Q - 1))
                    continue
                self.F = i
            except:
                print("Invalid input: accept state must be integers")
        return

    def trans_to_str(self, tup):
        a = tup[0]
        t = tup[1]
        w = tup[3]
        b = ""
        if (a == ""):
            a = "eps"
        if (t == ""):
            t = "eps"

        for x in w:
            b += x

        if (b == ""):
            b = "eps"

        return "[{0},{1}->{2}]".format(a, t, b)

    def print_transitions(self, q):
        print("Transitions for state {0}:".format(q))
        if (q in self.d):
            for t in self.d[q]:
                print(self.trans_to_str(t))
        return

    def print_all_transitions(self):
        for i in range(self.Q):
            self.print_transitions(i)
        return

    def get_all_transitions(self):
        for i in range(self.Q):
            tmp = -1
            while (tmp != 'y' or tmp != 'n'):
                self.print_transitions(i)
                tmp = input("Need a transition rule for state {0} ? (y or n)"
                            .format(i))

                if (tmp == "n"):
                    # Needed for checking final state in process()
                    if (i not in self.d):
                        # Set the transition to have empty list in dictionary
                        self.d[i] = []
                    break

                elif (tmp == "y"):
                    self.get_transition(i)

                else:
                    print("Invalid input: must be 'y' or 'n'")
        return

    def get_transition(self, q):
        '''
        Prompts user to add transition rule for q.
        Checks if able to add the transition.
        If able, returns tuple (a,t,r,w,c)
        '''
        a, t, r, w, c = -1, -1, -1, -1, -1
        eps = "-"
        minus = "--"

        # Get input symbol a
        while (a not in self.SIG):
            a = input(
                    "Input Symbol to read "
                    + "(enter - for epsilon, enter -- for '-'): ")

            if (a == eps):
                a = ""
                break

            if (a == minus):
                a = "-"

            if (a not in self.SIG):
                print("Invalid input: symbol not in alphabet")

        # Get stack match t
        while (t not in self.GAM):
            t = input(
                    "Stack symbol to match and pop "
                    + "(enter - for epsilon, enter -- for '-'): ")

            if (t == eps):
                t = ""
                break
            
            if (t == minus):
                t = "-"

            if (t not in self.GAM):
                self.GAM.add(t)

        # Get next state r
        while (r not in range(self.Q)):
            try:
                    r = int(input("State to transition to : "))
                    if (r not in range(self.Q)):
                        print("Invalid input: input greater than", self.Q)
            except:
                print("Invalid input: state must be integer")

        # Get stack symbol(s) to push w
        while (w == -1):
            # PRONE TO BREAKING no string validation
            tmp = input(
                "Stack symbols to push as comma separated list, "
                + "first symbol to top of stack "
                + "(enter - for epsilon, enter -- for '-'): ")
            if (tmp == eps):
                w = [""]
                break

            if (tmp == minus):
                w = ["-"]

            else:
                l = []
                for s in tmp.split(","):
                    if (s == minus):
                        l.append("-")
                    else:
                        l.append(s)

                # Add new symbols from tmp to GAM
                self.GAM = self.GAM | set(l)

                # Set w to l
                w = l

        c = self.condition(a, t)
        if (self.valid(q, (a, t, r, w, c))):
            self.add_transition(q, (a, t, r, w, c))
        return

    def add_transition(self, q, entry):
        if (q not in self.d):
            self.d[q] = [entry]
        else:
            self.d[q].append(entry)
        return
        
    def condition(self, sym_read, stack_top):
        '''
        helper function
        determine which condition for transition being added
        '''
        if (sym_read == '' and stack_top == ''):
            return 1
        elif (sym_read == '' and stack_top != ''):
            return 2
        elif (sym_read != '' and stack_top == ''):
            return 3
        return 4

    def valid(self, q, trans):
        '''
        helper function
        takes in state and tuple.
        Lookup in d for transitions
        compares trans tuple to existing transitions in d
        '''
        if (q not in self.d):
            return True

        for t in self.d[q]:
            # eps, eps transition only allowed rule
            if (t[4] == 1):
                print("Violation of DPDA due to epsilon input/epsilon"
                      + " stack transition from state {0}:".format(q)
                      + self.trans_to_str(t))
                return False

            # check duplicate (a, t) pairs
            elif ((t[0] == trans[0]) and (t[1] == trans[1])):
                print("Violation of DPDA due to multiple transitions"
                      + " for the same input and "
                      + "stack top from state {0}:".format(q)
                      + self.trans_to_str(t))
                return False

            # check duplicate a if adding epsilon stack or exists epsilon stack
            elif ((trans[4] == 1)
                    or (t[0] == trans[0] 
                        and ((trans[1] == "") or (t[1] == "")))):
                print("Violation of DPDA due to epsilon stack"
                      + " transition from state {0}:".format(q)
                      + self.trans_to_str(t))
                return False

        return True

def stack_to_str(l):
    rtn = ""
    # If the stack is empty
    if (not l):
        return "eps"
    for it in l[::-1]:
        rtn += it
    return rtn

def get_path(curr_sym, stack_top, trans_ls):
    sz = len(trans_ls)
    # If only transition is eps, eps
    if (sz == 1 and trans_ls[0][4] == 1):
        return 0

    # Find matching transition
    for i in range(sz):
        if (curr_sym == trans_ls[i][0] or stack_top == trans[i][1]):
            return i

    # Return case if no match found
    return -1

def process_s(M, s): 
    stack = []              # DPDA Stack
    curr_s = 0              # DPDA State
    curr_sym = ""           # Current char
    next_sym = ""           # Next char
    stack_top = ""          # Stack top
    configs = ""

    '''
    x1: q_i in F            := In accepting state
    x2: s[i:] == ''         := Done reading input
    x3: stack == []         := Stack is empty
    x4: get_path() == -1    := There does not exist a path to take
    accept: x1 and x2 and x3 and not x4
    '''
    x1 = False
    x2 = False
    x3 = True
    x4 = True
    accept = False

    # Start computation loop
    i = 0
    while (True):
        # Set stream pointer and lookahead
        if (i != len(s)):
            curr_sym = s[i]
        else:
            curr_sym = ""

        if (i + 1 < len(s)):
            next_sym = s[i + 1]
        else:
            next_sym = ""

        # Set stack pointer if stack not empty
        if (len(stack) > 0):
            stack_top = stack[-1]
        else:
            stack_top = ""

        # Update the transitions for the current state
        t = M.d[curr_s]

        # Get index of transition to take
        idx = get_path(curr_sym, stack_top, t)

        # Check the DPDA configuration
        x1 = curr_s in M.F
        x2 = s[i:] == ""
        x3 = len(stack) == 0
        x4 = idx == -1
        stop = (x1 and x2 and x3) or x4
        accept = x1 and x2 and x3

        # Update configurations string
        if (s[i:] == ""):
            configs += "(q{0};eps;{1})".format(curr_s, stack_to_str(stack))
        else:
            configs += "(q{0};{1};{2})".format(curr_s, s[i:], stack_to_str(stack))

        # Check if able to return
        if (stop):
            return (accept, configs)

        # Choose a transition to make from current state
        t_func = t[idx]     # Transition tuple to take
        t_r = t_func[2]
        t_w = t_func[3]
        t_c = t_func[4]

        # 1) move to next state
        curr_s = t_r

        # 2) advance stream pointer if input is matched
        if ((t_c == 3 or t_c == 4) and i <= len(s)):
            i += 1

        # 3) update the stack if stack is matched
        if (t_c == 2 or t_c == 4):
            stack.pop()

        # 4) push symbols from transition on to stack
        for sym in t_w[::-1]:
            if (sym == ""):
                break
            stack.append(sym)

        # 5) update configs with transition taken
        configs += "--" + M.trans_to_str(it) + "-->"

        '''
            # If no transition is possible and there's input to read, stop computation
            elif (x2 and it == t[-1]):
                return (False, configs)
        '''

def main():
    # Set up DPDA through user input
    M = DPDA()
    M.set_init()
    M.get_all_transitions()
    M.print_all_transitions()

    while (True):
        s = input("Enter an input string to be processed by the PDA : ")
        ret = process_s(M, s)
        print("Accept string {0}?".format(s), ret[0])
        print(ret[1])
    

if __name__ == '__main__':
    main();
