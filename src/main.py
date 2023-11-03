'''
CS 341-005
Benedikt Macaro
DPDA simulator
'''

'''
what am i doing
1) get states (int), input alphabet (comma separated no space), accept state (comma separated no space)
2) get transitions
'''
class DPDA:
    """
    Class representation of DPDA
    stack: DPDA stack
    alpha: language alphabet
    num_s: number of states
    acc_s: accept states
    """
    def __init__(self, num_s, alpha, acc_s):
        self.num_s = num_s
        self.alpha = alpha
        self.acc_states = acc_s
        self.trans = {}
        self.stack = []

    def print_transitions(self, q):
        print("Transitions for state {}:".format(q))
        if (self.trans):
            a = self.trans[q][0]
            t = self.trans[q][1]
            w = self.trans[q][3]
            print("[{0},{1}->{2}]".format(a, t, w))

    def get_transition(self, q):
        tmp = input("Need a transition rule for state {0} ? (y or n)"
            .format(q))

        if (tmp == "n"):
            continue
        else:
            a = input("Input Symbol to read (enter - for epsilon): ")
            t = input("Stack symbol to match and pop (enter - for epsilon): ")
            r = int(input("State to transition to : "))
            # TODO: for w - validation and shit, probably broken LMAO
            # Need to make sure stack symbols being pushed are in the alphabet
            w = input(
                "Stack symbols to push as comma separated list, "
                + "first symbol to top of stack (enter - for ep"
                + "silon): ").strip().split(",")
            c = condition(a, t)

    def add_transition(self, q, a, t, r, w, c):
        #TODO: Make into switch statement maybe?
        if (c == 1):
            if (not self.trans[q]):
                self.trans[q] = (a, t, r, w, c)
                return
            else:
                #TODO: Error handling
                pass
        elif (c == 2):
            pass
        elif (c == 3):
            pass
        elif (c == 4):
            pass
        

def condition(sym_read, stack_top):
    if sym_read == '-' and stack_top == '-':
        return 1
    elif sym_read == '-' and stack_top != '-':
        return 2
    elif sym_read != '-' and stack_top == '-':
        return 3
    return 4

def main():
    '''
    TODO: input validation: (ano pa ba?)
        Q (must be int), 
        sigma (cannot be empty), 
        F (must be ints)
    '''

    Q = int(input("Enter number of states :\n"))
    sigma = input(
        "Enter input alphabet as a"
        + " comma-separated list of symbols :\n").strip().split(",")
    F = []
    while (not F):
        # For all accept states, delimit by comma, convert to int, store in list.
        i = list(map(int, 
            input(
                "Enter accepting states as a "
                + "comma-separated list of integers :\n").strip().split(",")))

        m = max(i)
        if (m > Q - 1):
            print(
                "invalid state {0}; enter a value between {1} and {2}"
                .format(m, 0, Q - 1))
            continue
        F = i

    print("Q: ", Q)
    print("sigma: ", sigma)
    print("F: ", F)

    M = DPDA(Q, sigma, F)

    for i in range(Q):
        M.print_transitions(i);
        M.get_transition(i);


if __name__ == '__main__':
    main();
