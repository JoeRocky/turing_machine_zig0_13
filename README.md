
# Turing Machine

written in Zig 0.13.0

by Joseph Rockendorf

---
  

This fun side project allows the simulation of a Turing Machine.

A program for this Turing Machine can be stored in a ``.tur`` file. The ``.tur`` file is a simple text file specifying the instructions.

The first line is reserved for some initial data to be put into memory.

Every instruction has two parts, the first three parameters are for when a zero is read, the second three parameters are for when a one is read. The first of ever three parameters is the number that will be written down (``0``/``1``). The second parameter is for the direction that the Turing Machine will move on the tape (``R``,``L``,``_``). The third parameter marks the line of the file to which the program will jump (Using a text editor that displays the line numbers is helpful here). Replacing the three parameters with a ``H`` creates a HALT instruction. Comments are only allowed at the end of the file (and at the end of an instruction, might still be buggy) and are marked with an ``#``. Comments, empty lines and any other lines that are not an instruction are not allowed within the program, but only at the end of the file. (This is a limitation of my parser. Might be fixed soon...) 

  

Example of the ``.tur`` content notation:

```
0000
1 R 3 H
1 L 2 0 R 3
```

Turing Machine program usage:
```py
# will run ./main.tur by default
turing_machine 
# run a specified file:
turing_machine ./some_file.tur
# or use zig build run:
zig build run -- ./somefile.tur
```

# TurASM

Next i wanted to create a somewhat more "complex" program like a 4 bit adder.

Since writing raw instructions is very tedious I decided to create my own kind of assembly language but for Turing Machines. Calling it assembly might be an overstatement since you can't really run any instructions one might be familiar in assembly. So i created ``turing_asm_transpiler.py`` to transpile my super simple self-made assembly style language I write in ``.turasm`` files into my self-made Turing Machine program instruction format stored in ``main.tur``. The goal isn't to be very efficient, but to be easy to read, write and transpile. The instructions are mainly focused around: moving, writing, conditional jumps and jumping to labels for code reusability.

```
Instructions:
#        comment
&        set initial memory (spaces between bits will be ignored)
:a       label a
*a       goto label a
>x       move right x steps
<x       move left x steps
w0       write 0
w1       write 1
?        a b if read value is 0: call instruction a else call instruction b
?0       a if read value is 0: call instruction a
?1       a if read value is 1: call instruction a
HALT     HALT
```

Example ``4BitAdder.turasm``:
```
& 0101 0101 0000

:main
>3
? *readVal2_0 *readVal2_1
<1
? *readVal2_0 *readVal2_1
<1
? *readVal2_0 *readVal2_1
<1
? *readVal2_0 *readVal2_1
 
:readVal2_0
>4
? *writeVal3_0 *writeVal3_1

:readVal2_1
>4
? *writeVal3_1 *writeVal3_2

:writeVal3_0
<4

:writeVal3_1
>4
? *writeVal3_1_0 *writeVal3_1_1
<8

:writeVal3_1_0
w0

:writeVal3_1_1
w0
<1
w1
>1

:writeVal3_2
>3
w1
<7
```

This code could be slightly optimized for increased speed (and decreased readability), like inlining ``:writeVal3_0`` and ``:writeVal3_1_0`` to avoid unnecessary jumps and instructions:
``? *writeVal3_0 *writeVal3_1`` => ``? <4 *writeVal3_1``
``? *writeVal3_1_0 *writeVal3_1_1`` => ``? w0 *writeVal3_1_1``


Transpiler usage:
```py
# will transpile ./main.turasm by default
python turing_asm_transpiler.py 
# will transpile ./some_file.turasm to ./some_file.tur
python turing_asm_transpiler.py ./some_file.turasm
# will transpile ./some_file.turasm to ./some_other_filename.tur
python turing_asm_transpiler.py ./some_file.turasm ./some_other_filename.tur
```


# TODOs:
- [ ] improve ``.turasm`` parser
- [ ] extent ``.turasm`` language
- [ ] improve ``.tur`` parser (to allow comments in between and empty lines in between)
- [ ] maybe compact ``.tur`` notation? (``0 R 30 1 L 5`` => ``0R30 1L5``)
- [ ] add more options for visualizing the Turing Machine simulation