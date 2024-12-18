# Catherine Healy
# Team chealy5
# Net ID: chealy5
# Due December 9th 2024
# No other team members
# Nondeterminisitic turing machine simulator

from collections import deque
import csv
import dataclasses


# Use dataclass to store the current configuraton
@dataclasses.dataclass
class Configuration:
    tape: str  # tape contents
    state: str  # current state
    remaining: str  # what is left to process in tape

# Store the nondeterminisitc turing machine information in special TM dataclass
class TuringMachine:
    def __init__(self, file_name):
        self.transitions = {}
        self.name = None
        self.start_state = None
        self.accept_state = None
        self.reject_state = None

        # populate the information with stuff from NTM file
        self.get_machine_info(file_name)

    def get_machine_info(self, file_name):
        with open(file_name, 'r') as file:
            lines = [line.strip() for line in file.readlines()]

            # get machine info from input file (I will assume it comes in propper format)
            self.name = lines[0]  # machine name
            _ = lines[1]  # states
            _ = lines[2]  # input alphabet
            _ = lines[3]  # tape alphabet
            self.start_state = lines[4]  # start state
            self.accept_state = lines[5]  # accept state
            self.reject_state = lines[6]  # reject state

            # The rest of the inputs are transitions
            for transition_line in lines[7:]:
                transition_parts = transition_line.split(',')
                if len(transition_parts) == 5:
                    current_state, current_char, next_state, write_char, direction = transition_parts

                    # Store all the unique transitions into a dictionary for easy searching.
                    if current_state not in self.transitions:
                        self.transitions[current_state] = {}
                    if current_char not in self.transitions[current_state]:
                        self.transitions[current_state][current_char] = []
                    self.transitions[current_state][current_char].append(
                        (next_state, write_char, direction)
                    )

    def read_input(self, input_string: str, max_depth: int = 100):
        # Initial configuration
        initial_config = Configuration(tape="", state=self.start_state, remaining=input_string)

        # Queue for BFS with each entry containing: (current_config, path_so_far, num_transitions)
        queue = deque([(initial_config, [], 0)])

        # Tracking total configurations and transitions
        total_configurations = 0
        total_transitions = 0
        total_branches = 0  # total number of branches

        # Keep track of depht (i think depth is like the # of transitions of accepted one)
        depth_reached = 0
        new_configs_this_iteration = 0

        longest_reject_path = None # If rejected, need the longest path
        max_reject_transitions = 0 # If all transtions are rejected, then reject overlal

        # condition is while queue is not empty and the max depth is not reached yet
        while queue and depth_reached < max_depth:
            level_size = len(queue)
            new_configs_this_iteration = 0

            # Process all configurations at current depth (This is basically BFS method)
            for _ in range(level_size):
                current_config, current_path, current_transitions = queue.popleft()
                total_configurations += 1

                # If no remaining input/blank tape, see if it accepts
                if not current_config.remaining:
                    # Kogge gave several average nondeterminism formulas
                    # and I am confused which is corred. For now, I used total configurations divided by depth
                    # because he talked about that being an option
                    nondeterminism = total_configurations / (depth_reached + 1)
                    return {
                        "status": "accept",
                        "machine_name": self.name,
                        "input": input_string,
                        "depth": current_transitions,
                        "total_configurations": total_configurations,
                        "transitions": current_transitions,
                        "max_depth_reached": depth_reached,
                        "nondeterminism": nondeterminism,
                        "path": current_path + [current_config]
                    }

                current_char = current_config.remaining[0]

                # find possible transitions
                valid_transitions = False

                #check if transitions exist
                if (current_config.state in self.transitions and
                    current_char in self.transitions[current_config.state]):
                    # check each possible transition
                    branch_count = len(self.transitions[current_config.state][current_char])
                    total_branches += branch_count - 1  # Subtract 1 because first transition doesn't count as bbranch

                    for next_state, write_char, direction in self.transitions[current_config.state][current_char]:
                        total_transitions += 1
                        valid_transitions = True
                        new_configs_this_iteration += 1

                        # Figure out what the new configuraiton is based on the transition
                        new_tape = current_config.tape + write_char

                        #Follwo direcitons to update the tape
                        if direction == 'R':
                            new_remaining = current_config.remaining[1:] if current_config.remaining else ''
                        else:  # 'L'
                            new_remaining = current_config.remaining

                        # Add new configuration that will be added to queue based on where you can go next
                        new_config = Configuration(
                            tape=new_tape,
                            state=next_state,
                            remaining=new_remaining
                        )

                        # Add to queue with updated path
                        new_path = current_path + [current_config]
                        queue.append((new_config, new_path, current_transitions + 1))

                # if no valid transitions, add to reject path
                if not valid_transitions:
                    total_transitions += 1
                    # add to reject path if it's the longest so far
                    if current_transitions > max_reject_transitions:
                        longest_reject_path = (current_config, current_path, current_transitions)
                        max_reject_transitions = current_transitions

                    # If no valid transitions, go to reject state
                    new_config = Configuration(
                        tape=current_config.tape,
                        state=self.reject_state,
                        remaining=current_config.remaining
                    )
                    new_path = current_path + [current_config]
                    queue.append((new_config, new_path, current_transitions + 1))

            # Update the depth each iteration
            depth_reached += 1

            # If paths all reject, stop
            if all(config[0].state == self.reject_state for config in queue):
                break

        # average nondeterminism formula from kogge: total configurations divided by depth
        nondeterminism = total_configurations / (depth_reached + 1)

        return {
            "status": "reject",
            "machine_name": self.name,
            "input": input_string,
            "depth": max_reject_transitions,
            "total_configurations": total_configurations,
            "transitions": max_reject_transitions if longest_reject_path else total_transitions,
            "max_depth_reached": depth_reached,
            "nondeterminism": nondeterminism,
            "path": longest_reject_path[1] + [longest_reject_path[0]] if longest_reject_path else []
        }

def main():
    # Get Turing machine information file
    file_name = input("Please enter the name of the file describing the Nondeterministic Turing machine: ")

    # create the turing machine dataclass based on info
    NTM = TuringMachine(file_name)

    # open output files for writing results
    output_file = open("output_TM_results_chealy5.txt", "w")
    summary_file = open("output_TM_Table_chealy5.csv", "w")

    # Get input strings. User can use -t flag to show max depth to terminate at.
    # for example, user can do -t 20 to stop after depth 20 reached
    user_input = input("Please enter the input string(s) and indicate max depth with -t [int]: ").strip()
    entries = user_input.split()
    max_depth = 100  # Keep the default maximum depth to 100 so it doesn't loop forever

    # Loop through input strings and if a -t flag detected, then need to indicate max depth or use default
    if '-t' in entries:
        t_index = entries.index('-t')
        if t_index + 1 < len(entries):
            try:
                max_depth = int(entries[t_index + 1])
                input_strings = entries[:t_index]
            except ValueError:
                max_depth = 100
                input_strings = entries
        else:
            input_strings = entries[:t_index]
    else:
        input_strings = entries

    # initialize input string as empty in case nothing gets entered by user
    if not input_strings:
        input_strings = ['']

    # # will want a table
    table_writer = csv.writer(summary_file)
    table_writer.writerow([
        "Machine Name",
        "Input String",
        "Result",
        "Depth of Tree",
        "Configurations Explored",
        "Nondeterminism"
    ])

    # Loop through the input strings and trace all the paths for each string
    for input_string in input_strings:
        # run the Turing machine
        result = NTM.read_input(input_string, max_depth)

        # determine the result
        if result['status'] == 'accept':
            result_status = 'Accepted'
        elif result['max_depth_reached'] >= max_depth:
            result_status = 'Ran Too Long'
        else:
            result_status = 'Rejected'

        # output
        output_lines = [
            f"Machine Name: {result['machine_name']}",
            f"Input String: '{result['input']}'",
            f"Depth of Configuration Tree: {result['depth']}",
            f"Total Transitions / Execution time: {result['transitions']}",
            f"Total Configurations: {result['total_configurations']}",
            f"Nondeterminism: {result['nondeterminism']:.2f}"
        ]

        # try to format stuff and get it into files for submission
        if result['status'] == 'accept':
            output_lines.append(f"\nString ACCEPTED in {result['transitions']} transitions")
            output_lines.append("\nAcceptance Path (each line shows: tape state current_head remaining_tape):")
            for config in result['path']:
                left = config.tape
                head = '_' if not config.remaining else config.remaining[0]
                right = '_' if len(config.remaining) <= 1 else config.remaining[1:]
                output_lines.append(f"{left} {config.state} {head} {right}")

        else:
            output_lines.append(f"\n{'RAN TOO LONG' if result['max_depth_reached'] >= max_depth else 'String REJECTED'} in {result['transitions']} transitions")
            output_lines.append("\nLongest Path (each line shows: tape state current_head remaining_tape):")
            for config in result['path']:
                left = config.tape
                head = '_' if not config.remaining else config.remaining[0]
                right = '_' if len(config.remaining) <= 1 else config.remaining[1:]
                output_lines.append(f"{left} {config.state} {head} {right}")

        # Print to google colabs result so I can view output
        for line in output_lines:
            print(line)

        # write results ot file so I can upload it into github for submission
        output_file.write("\n".join(output_lines) + "\n\n")

        # write stats/results in the table
        table_writer.writerow([
            result['machine_name'],
            result['input'],
            result_status,
            result['depth'],
            result['total_configurations'],
            round(result['nondeterminism'], 2)
        ])

    output_file.close()
    summary_file.close()

if __name__ == '__main__':
    main()

#
