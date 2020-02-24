from typing import List
import getpass
import sys
from parser import Parser
from lexer import Lexer
from evaluator import Evaluator
from environment import Environment

PROMPT = ">> "
MONKEY_FACE = """            __,__
   .--.  .-"     "-.  .--.
  / .. \\/  .-. .-.  \\/ .. \\
 | |  '|  /   Y   \\  |'  | |
 | \\   \\  \\ 0 | 0 /  /   / |
  \\ '- ,\\.-"""""""-./, -'  /
   ''-' /_   ^ ^   _\\ '-''
       |  \\._   _./  |
       \\   \\ '~' /   /
        '._ '-=-' _.'
           '-----'"""


def start() -> None:
    env = Environment()
    user = getpass.getuser()

    if len(sys.argv) == 1:
        print(f"hello {user}! This is the monkey programming language!")
        print("Feel free to type in commands")

    while True:
        if len(sys.argv) == 1:
            line = input(PROMPT)
            if len(line) == 0:
                continue
        else:
            with open(sys.argv[1], "r") as file:
                line = file.read()

        lexer = Lexer(line)
        parser = Parser(lexer)
        program = parser.parse_program()
        if len(parser.errors) != 0:
            _print_parser_errors(parser.errors)
            continue

        evaluator = Evaluator()
        evaluated = evaluator.eval(program, env)
        if evaluated is not None:
            print(evaluated.inspect())
        if len(sys.argv) == 2:
            break


def _print_parser_errors(errors: List[str]) -> None:
    print(MONKEY_FACE)
    print("Woops! We ran into some monkey business here!")
    print(" parser errors:")
    for error in errors:
        print(f"\t{error}")


if __name__ == "__main__":
    start()
