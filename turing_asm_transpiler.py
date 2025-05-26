import copy
import sys


def error(msg: str):
  print("ERROR: " + msg)
  exit(1)


class PartialInstruction:
  move: str = ""
  write: bool = False
  goto: str = "0"

  def __init__(self, write: bool = False, move: str = "", goto: str = ""):
    self.move = move
    self.write = write
    self.goto = goto
  
  def __str__(self):
    if self.move == "H": 
      return "H"
    else:
      return f"{"1" if self.write else "0"} {self.move} {"+1" if (self.goto == "") else self.goto}"

class Instruction:
  read0: PartialInstruction = None
  read1: PartialInstruction = None

  def __init__(self, read0: PartialInstruction = None, read1: PartialInstruction = None):
    self.read0 = read0
    self.read1 = read1
  
  def __str__(self):
    return f"{str(self.read0)} {str(self.read1)}"

  def make_move_right():
    return Instruction(
      PartialInstruction(False, "R", "+1"),
      PartialInstruction(True, "R", "+1")
    )
  def make_move_left():
    return Instruction(
      PartialInstruction(False, "L", "+1"),
      PartialInstruction(True, "L", "+1")
    )
  def make_write(val: bool):
    return Instruction(
      PartialInstruction(val, "_", "+1"),
      PartialInstruction(val, "_", "+1")
    )
  def make_halt():
    return Instruction(
      PartialInstruction(False, "H", "+1"),
      PartialInstruction(False, "H", "+1")
    )
  def make_return():
    return Instruction(
      PartialInstruction(False, "_", "return"),
      PartialInstruction(True, "_", "return")
    )
  def make_jump(label: str):
    return Instruction(
      PartialInstruction(False, "_", label),
      PartialInstruction(True, "_", label)
    )

class Label:
  instructions: list[Instruction] = None

  def __init__(self):
    self.instructions = []

  def __str__(self):
    string = ""
    for instr in self.instructions:
      string += "" + str(instr) + "\n"
    return string
  
  def link_lables(self, write_to_line: int = 0, called_from_line: int = 0, all_labels: dict[str, 'Label'] = {}) -> list[Instruction]:
    instrs: list[Instruction] = copy.deepcopy(self.instructions)
    for i, instr in enumerate(instrs):
      if instr.read0.goto[0] == "+":
        instr.read0.goto = str(int(instr.read0.goto[1:]) + write_to_line + i)
      if instr.read1.goto[0] == "+":
        instr.read1.goto = str(int(instr.read1.goto[1:]) + write_to_line + i)
      if instr.read0.goto == "return":
        instr.read0.goto = str(called_from_line + 1)
      if instr.read1.goto == "return":
        instr.read1.goto = str(called_from_line + 1)
      if instr.read0.goto[0] == "*" and instr.read0.goto != instr.read1.goto:
        jmp_pos = write_to_line + len(instrs)
        instrs.extend(all_labels[instr.read0.goto[1:]].link_lables(jmp_pos, write_to_line + i, all_labels))
        instr.read0.goto = str(jmp_pos)
      if instr.read1.goto[0] == "*" and instr.read0.goto != instr.read1.goto:
        jmp_pos = write_to_line + len(instrs)
        instrs.extend(all_labels[instr.read1.goto[1:]].link_lables(jmp_pos, write_to_line + i, all_labels))
        instr.read1.goto = str(jmp_pos)
      if instr.read0.goto[0] == "*" and instr.read1.goto[0] == "*" and instr.read0.goto == instr.read1.goto:
        jmp_pos = write_to_line + len(instrs)
        instrs.extend(all_labels[instr.read0.goto[1:]].link_lables(jmp_pos, write_to_line + i, all_labels))
        instr.read0.goto = str(jmp_pos)
        instr.read1.goto = str(jmp_pos)
    return instrs


class ParsedProgram:
  memory: str = None
  labels: dict[str, Label] = None

  def __init__(self, memory: str = "", labels: dict[str, Label] = {}):
    self.memory = memory
    self.labels = labels

class FinalProgram:
  memory: str = None
  instructions: list[Instruction] = None

  def __init__(self, memory: str = "", instructions: list[Instruction] = []):
    self.memory = memory
    self.instructions = instructions

  def __str__(self):
    string = "" + self.memory + "\n"
    for instr in self.instructions:
      string += "" + str(instr) + "\n"
    return string

def convert_file_to_instructions(file_name: str) -> ParsedProgram:
  file = open(file_name, "r")
  memory = ""
  labels: dict[str, Label] = {}
  current_label = ""

  for line in file:
    if line.strip() == "":
      continue
    match line[0]:
      case "#":
        pass
      case "&":
        memory += line[1:].strip().replace(" ", "")
      case ":":
        if current_label == "main":
          labels[current_label].instructions.append(Instruction.make_halt())
        elif current_label != "":
          labels[current_label].instructions.append(Instruction.make_return())
        current_label = line[1:].strip()
        labels[current_label] = Label()
      case ">":
        number = int(line[1:].strip())
        for _ in range(number):
          labels[current_label].instructions.append(Instruction.make_move_right())
      case "<":
        number = int(line[1:].strip())
        for _ in range(number):
          labels[current_label].instructions.append(Instruction.make_move_left())
      case "w":
        value = line[1] == "1"
        labels[current_label].instructions.append(Instruction.make_write(value))
      case "H":
        if line[1:4] == "ALT":
          labels[current_label].instructions.append(Instruction.make_halt())
      case "*":
        label = "*" + line[1:].strip()
        labels[current_label].instructions.append(Instruction.make_jump(label))
      case "?":
        # ?0
        if line[1] == "0":
          instr = line[2:].strip()
          instr_count = 0
          jmp_instr = Instruction(
            PartialInstruction(False, "_", "+1"),
            PartialInstruction(True, "_", "+1")
          )
          labels[current_label].instructions.append(jmp_instr)
          match instr[0]:
            case ">":
              number = int(instr[1:].strip().replace(" ", ""))
              for _ in range(number):
                labels[current_label].instructions.append(Instruction(
                  PartialInstruction(False, "R", "+1"),
                  PartialInstruction(True, "_", "+1")
                ))
                instr_count += 1
            case "<":
              number = int(instr[1:].strip().replace(" ", ""))
              for _ in range(number):
                labels[current_label].instructions.append(Instruction(
                  PartialInstruction(False, "L", "+1"),
                  PartialInstruction(True, "_", "+1")
                ))
                instr_count += 1
            case "w":
              value = instr[1] == "1"
              labels[current_label].instructions.append(Instruction(
                PartialInstruction(value, "_", "+1"),
                PartialInstruction(True, "_", "+1")
              ))
              instr_count += 1
            case "*":
              label = "*" + instr[1:].strip()
              labels[current_label].instructions.append(Instruction(
                PartialInstruction(False, "_", label),
                PartialInstruction(True, "_", "+1")
              ))
              instr_count += 1
          jmp_instr.read1.goto = "+" + str(instr_count+1)
        # ?1
        elif line[1] == "1":
          instr = line[2:].strip()
          instr_count = 0
          jmp_instr = Instruction(
            PartialInstruction(False, "_", "+1"),
            PartialInstruction(True, "_", "+1")
          )
          labels[current_label].instructions.append(jmp_instr)
          match instr[0]:
            case ">":
              number = int(instr[1:].strip().replace(" ", ""))
              for _ in range(number):
                labels[current_label].instructions.append(Instruction(
                  PartialInstruction(False, "_", "+1"),
                  PartialInstruction(True, "R", "+1")
                ))
                instr_count += 1
            case "<":
              number = int(instr[1:].strip().replace(" ", ""))
              for _ in range(number):
                labels[current_label].instructions.append(Instruction(
                  PartialInstruction(False, "_", "+1"),
                  PartialInstruction(True, "L", "+1")
                ))
                instr_count += 1
            case "w":
              value = instr[1] == "1"
              labels[current_label].instructions.append(Instruction(
                PartialInstruction(False, "_", "+1"),
                PartialInstruction(value, "_", "+1")
              ))
              instr_count += 1
            case "*":
              label = "*" + instr[1:].strip()
              labels[current_label].instructions.append(Instruction(
                PartialInstruction(False, "_", "+1"),
                PartialInstruction(True, "_", label)
              ))
              instr_count += 1
          jmp_instr.read0.goto = "+" + str(instr_count+1)
        # ?
        elif line[1] == " ":
          instr1 = line[2:].strip().split(" ")[0]
          instr1_count = 0
          instr2 = line[2:].strip().split(" ")[1]
          instr2_count = 0
          jmp1_instr = Instruction(
            PartialInstruction(False, "_", "+1"),
            PartialInstruction(True, "_", "+1")
          )
          labels[current_label].instructions.append(jmp1_instr)
          match instr1[0]:
            case ">":
              number = int(instr1[1:].strip().replace(" ", ""))
              for _ in range(number):
                labels[current_label].instructions.append(Instruction.make_move_right())
                instr1_count += 1
            case "<":
              number = int(instr1[1:].strip().replace(" ", ""))
              for _ in range(number):
                labels[current_label].instructions.append(Instruction.make_move_left())
                instr1_count += 1
            case "w":
              value = instr1[1] == "1"
              labels[current_label].instructions.append(Instruction.make_write(value))
              instr1_count += 1
            case "*":
              label = "*" + instr1[1:].strip()
              labels[current_label].instructions.append(Instruction.make_jump(label))
              instr1_count += 1
          jmp2_instr = Instruction(
            PartialInstruction(False, "_", "+1"),
            PartialInstruction(True, "_", "+1")
          )
          labels[current_label].instructions.append(jmp2_instr)
          instr1_count += 1
          jmp1_instr.read1.goto = "+" + str(instr1_count+1)
          match instr2[0]:
            case ">":
              number = int(instr2[1:].strip().replace(" ", ""))
              for _ in range(number):
                labels[current_label].instructions.append(Instruction.make_move_right())
                instr2_count += 1
            case "<":
              number = int(instr2[1:].strip().replace(" ", ""))
              for _ in range(number):
                labels[current_label].instructions.append(Instruction.make_move_left())
                instr2_count += 1
            case "w":
              value = instr2[1] == "1"
              labels[current_label].instructions.append(Instruction.make_write(value))
              instr2_count += 1
            case "*":
              label = "*" + instr2[1:].strip()
              labels[current_label].instructions.append(Instruction.make_jump(label))
              instr2_count += 1
          jmp2_instr.read0.goto = "+" + str(instr2_count+1)
          jmp2_instr.read1.goto = "+" + str(instr2_count+1)
        else:
          error("Unknown instruction: " + line)
  
  if current_label == "main":
    labels[current_label].instructions.append(Instruction.make_halt())
  elif current_label != "":
    labels[current_label].instructions.append(Instruction.make_return())
  
  file.close()
  return ParsedProgram(memory, labels)

def link_labels(parsed_program: ParsedProgram) -> FinalProgram:
  main_label = parsed_program.labels["main"]
  final_instrs = main_label.link_lables(2, 0, parsed_program.labels)
  return FinalProgram(parsed_program.memory, final_instrs)

def write_to_file(final_program: FinalProgram, file_name: str):
  file = open(file_name, "w")
  file.write(str(final_program))
  file.close()


def main():
  file_path = "./main.turasm"
  if len(sys.argv) > 1:
    file_path = sys.argv[1]

  file_name = file_path.split("/")[-1]
  output_file_name = file_name[0:len(file_name)-(len(file_name.split(".")[-1])+1)] + ".tur"
  if len(sys.argv) > 2:
    output_file_name = sys.argv[2]
  parsed_program = convert_file_to_instructions(file_path)
  final_program = link_labels(parsed_program)
  write_to_file(final_program, f"./{output_file_name}")


if __name__ == "__main__":
  main()